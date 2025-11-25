from .math_agent import MathAgent
from .highschool_agent import HighSchoolAgent
from .music_agent import MusicAgent
from .travel_agent import TravelAgent
from .games_agent import GamesAgent
from .llm_agent import LLMAgent
from .ap_stem_agent import APSTEMAgent
from .intent_router import IntentRouter
from .sat_act_agent import SATACTAgent
from .college_admission_agent import CollegeAdmissionAgent
from typing import Optional, Union, Dict


class AgentManager:
    def __init__(self):
        self.agents = {
            MathAgent.name: MathAgent(),
            HighSchoolAgent.name: HighSchoolAgent(),
            MusicAgent.name: MusicAgent(),
            TravelAgent.name: TravelAgent(),
            GamesAgent.name: GamesAgent(),
            LLMAgent.name: LLMAgent(),
            APSTEMAgent.name: APSTEMAgent(),
            SATACTAgent.name: SATACTAgent(),
            CollegeAdmissionAgent.name: CollegeAdmissionAgent(),
        }
        self.intent_router = IntentRouter()

    def list_agents(self):
        return list(self.agents.keys())

    def handle(self, agent_name: Optional[str], query: str, fallback_pref: str = None, api_key: str = None, auto_route: bool = False, use_web: bool = False, agent_fallbacks: dict = None) -> Union[str, Dict]:
        """
        Route query to appropriate agent.

        Args:
            agent_name: Explicit agent name (if None, will auto-detect unless auto_route=False)
            query: The user query
            fallback_pref: Fallback preference for LLMAgent
            api_key: API key for LLM/web search
            auto_route: If True and agent_name is None, auto-detect best agent

        Returns:
            Response from the agent (string or dict)
        """
        # Auto-detect agent if not specified
        if not agent_name or agent_name.lower() == "auto":
            auto_route = True
            agent_name, confidence = self.intent_router.detect_intent(query)
            # IntentRouter now returns categorical confidence 'low'|'medium'|'high'
            if isinstance(confidence, str):
                if confidence == 'low' and agent_name != "LLM Agent":
                    agent_name = "LLM Agent"
            else:
                # Backwards compatibility: numeric confidence
                if confidence < 0.3 and agent_name != "LLM Agent":
                    agent_name = "LLM Agent"

        agent = self.agents.get(agent_name)
        if not agent:
            return f"Unknown agent: {agent_name}"

        try:
            # Try to pass fallback_pref, api_key and use_web if the agent supports them
            # Call the agent with best-effort kwargs
            try:
                resp = agent.handle(query, fallback_pref=fallback_pref, api_key=api_key, use_web=use_web)
            except TypeError:
                try:
                    resp = agent.handle(query, fallback_pref=fallback_pref, api_key=api_key)
                except TypeError:
                    resp = agent.handle(query)

            # If this is not the LLM Agent and the response seems like a fallback/insufficient answer,
            # and an API key is provided, forward to LLM Agent for a better response.
            # Respect per-agent fallback configuration if provided
            fallback_allowed = True if agent_fallbacks is None else agent_fallbacks.get(agent_name, True)

            if agent_name != LLMAgent.name and api_key and fallback_allowed:
                # Extract textual content for heuristic checks
                resp_text = ''
                if isinstance(resp, dict):
                    # prefer explicit 'text' key
                    resp_text = (resp.get('text') or '')
                elif isinstance(resp, str):
                    resp_text = resp

                resp_text_norm = (resp_text or '').strip()

                # Heuristics for insufficient responses
                insufficient_phrases = [
                    "i don't",
                    "dont",
                    "do not",
                    "could not",
                    "couldn't",
                    "unable",
                    "i couldn't",
                    "i don't see",
                    "sympy not available",
                    "please provide",
                    "try a simpler",
                    "i don't see a direct",
                    "i'm not",
                    "i am not",
                    "no direct",
                    "no variables",
                    "unknown",
                    "not sure",
                    "i don't know",
                    "unable to",
                ]

                # Consider too-short or empty responses insufficient
                short_answer = not resp_text_norm or len(resp_text_norm) < 30
                fallbackish = any(p in resp_text_norm.lower() for p in insufficient_phrases)

                # Also treat explicit structured fallback flags from agents as signals
                structured_fallback = isinstance(resp, dict) and (resp.get('fallback') or resp.get('fallback_reason'))

                if fallbackish or short_answer or structured_fallback:
                    llm = self.agents.get(LLMAgent.name)
                    if llm:
                        try:
                            llm_resp = llm.handle(query, fallback_pref=fallback_pref, api_key=api_key, use_web=True)
                            # annotate returned result so UI can show it was a fallback
                            if isinstance(llm_resp, dict):
                                llm_resp.setdefault('fallback_from', agent_name)
                            else:
                                llm_resp = { 'text': llm_resp, 'fallback_from': agent_name }
                            return llm_resp
                        except Exception:
                            # If LLM fails, return original response
                            return resp

            return resp
        except Exception as e:
            return f"Agent error: {e}"

    def detect_intent(self, query: str):
        """Detect and return suggested agent with confidence score."""
        return self.intent_router.detect_intent(query)

    def get_suggestions(self, query: str, top_n: int = 3):
        """Get multiple agent suggestions for a query."""
        return self.intent_router.suggest_agents(query, top_n)
