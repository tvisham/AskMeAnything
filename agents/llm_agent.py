from .llm_wrapper import ask_llm
from .web_search_util import search_web, get_copilot_context
from .ap_stem_agent import APSTEMAgent
from .highschool_agent import HighSchoolAgent
from typing import Optional, Union, Dict


class LLMAgent:
    name = "LLM Agent"

    def handle(self, query: str, fallback_pref: Optional[str] = None, api_key: Optional[str] = None, use_web: bool = False) -> Union[str, Dict]:
        q = query.strip()
        if not q:
            return "Ask me anything — this agent will forward your question to the configured LLM backend."

        prompt = (
            "You are a helpful tutor and assistant. Answer the user's question clearly and concisely. "
            f"User question: {q}"
        )

        # If web context is requested, try to augment prompt with web search context
        web_context = None
        web_provider = None
        web_urls = []
        if use_web:
            try:
                from .web_search_util import search_web_multi
                res = search_web_multi(q, max_results=3, api_key=api_key)
                if isinstance(res, dict):
                    web_context = res.get('text')
                    web_provider = res.get('provider')
                    web_urls = res.get('urls', []) or []
                    if web_context and ("403" in web_context.lower() or web_context.lower().startswith("no results")):
                        web_context = None
                        web_provider = None
                        web_urls = []
            except Exception:
                web_context = None
                web_provider = None
                web_urls = []

        if web_context:
            prompt = prompt + "\n\nWeb context:\n" + web_context

        resp = ask_llm(prompt, api_key=api_key)

        # If the LLM backend is unavailable or API key is missing, provide a local fallback
        fallback_indicators = [
            "OPENAI_API_KEY not set",
            "LLM backend not available",
            "LLM request failed",
        ]
        if any(ind in resp for ind in fallback_indicators):
            # decide which local agent to use based on explicit preference or heuristic
            pref = (fallback_pref or "auto").lower()
            ql = q.lower()
            if pref == "ap_stem" or (pref == "auto" and any(k in ql for k in ["ap", "calculus", "physics", "chemistry", "biology", "statistics", "computer", "derivative", "integral"])):
                fallback_agent = "AP STEM"
                text = APSTEMAgent().handle(q)
            else:
                fallback_agent = "High School"
                text = HighSchoolAgent().handle(q)

            # Always try web search to supplement the fallback answer
            res = search_web(q, api_key=api_key)
            combined_text = text
            provider = None
            urls = []
            # res may be dict or tuple/string
            if isinstance(res, dict):
                provider = res.get('provider')
                web_text = res.get('text')
                urls = res.get('urls', []) or []
                if web_text and not any(fatal in web_text for fatal in ["error:", "Error:", "unavailable"]):
                    combined_text = f"{text}\n\n**Web Search Supplement (via {provider}):**\n\n{web_text}"
            else:
                try:
                    web_text, provider = res
                    if web_text and not any(fatal in web_text for fatal in ["error:", "Error:", "unavailable"]):
                        combined_text = f"{text}\n\n**Web Search Supplement (via {provider}):**\n\n{web_text}"
                except Exception:
                    pass

            # return structured dict so callers (UI) can display a banner when fallback was used
            return {
                "text": combined_text,
                "fallback": True,
                "fallback_agent": fallback_agent,
                "fallback_reason": resp,
                "search_provider": provider,
                "search_urls": urls,
            }

        return resp
