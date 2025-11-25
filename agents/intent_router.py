"""Intelligent intent detection and routing system for multi-agent chatbot.

This module analyzes user queries and automatically routes them to the most appropriate agent
based on detected intent and keywords.
"""

from typing import Tuple, Optional
import re


class IntentRouter:
    """Analyzes queries and routes them to appropriate agents."""

    # Keywords organized by agent intent
    AGENT_KEYWORDS = {
        "Math": {
                "keywords": [
                "calculate", "math", "equation", "solve", "algebra", "geometry",
                "formula", "add", "subtract", "multiply", "divide", "arithmetic",
                "number", "fraction", "decimal", "percentage", "ratio", "proportion"
            ],
            # include geometry explicitly in the pattern so geometry queries register as pattern matches
            "pattern": r"\b(calculate|solve|math|equation|algebra|geometry|arithmetic|formula|add|subtract|multiply|divide)\b"
        },
        "AP STEM": {
            "keywords": [
                "derivative", "integral", "calculus", "physics", "chemistry", "biology",
                "statistics", "quantum", "thermodynamics", "kinematics", "diff", "d/dx",
                "differential", "integration", "limit", "series", "sequence",
                "force", "energy", "momentum", "acceleration", "velocity",
                "molecular", "atom", "electron", "protein", "dna", "cell", "evolution"
            ],
            "pattern": r"\b(derivative|integral|calculus|physics|chemistry|biology|statistics|quantum|thermodynamics|kinematics|differential|integration|force|energy|momentum|acceleration|velocity|molecular|atom|electron|protein|dna)\b"
        },
        "Music": {
            "keywords": [
                "music", "song", "artist", "album", "band", "concert", "instrument",
                "chord", "melody", "rhythm", "beat", "piano", "guitar", "violin",
                "jazz", "rock", "pop", "classical", "composer", "tune", "hear"
            ],
            "pattern": r"\b(music|song|artist|album|band|concert|instrument|chord|melody|rhythm|beat|piano|guitar|violin|jazz|rock|pop|classical|composer)\b"
        },
        "Travel": {
            "keywords": [
                "travel", "trip", "destination", "city", "country", "hotel", "flight",
                "airport", "visit", "tour", "tourism", "attraction", "restaurant",
                "location", "place", "explore", "journey", "vacation", "beach", "mountain"
            ],
            "pattern": r"\b(travel|trip|destination|city|country|hotel|flight|airport|visit|tour|tourism|attraction|restaurant|explore|journey|vacation|beach|mountain)\b"
        },
        "Games": {
            "keywords": [
                "game", "play", "chess", "trivia", "puzzle", "riddle", "card",
                "dice", "sport", "win", "lose", "score", "rule", "strategy",
                "question", "answer", "challenge", "compete"
            ],
            "pattern": r"\b(game|play|chess|trivia|puzzle|riddle|card|dice|sport|win|lose|score|rule|strategy|challenge|compete)\b"
        },
        "HighSchool": {
            "keywords": [
                "history", "literature", "government", "civics", "english", "essay",
                "book", "author", "war", "revolution", "president", "law",
                "geography", "culture", "society", "social", "topic", "question"
            ],
            "pattern": r"\b(history|literature|government|civics|english|essay|book|author|war|revolution|president|law|geography|culture|society)\b"
        }
    }

    @staticmethod
    def looks_like_math(s: str) -> bool:
        # common numeric operators with digits (e.g., '2+2', '3x', '4=5')
        if re.search(r"\d+\s*[=+\-*/^]", s):
            return True
        # leading decimal like .5 or .25
        if re.search(r"(?<!\d)\.\d+", s):
            return True
        # implicit multiplication or variable like '2x' or '3xy' or ')x'
        if re.search(r"\d\s*[a-zA-Z(]", s) or re.search(r"\)\s*[a-zA-Z(]", s):
            return True
        # LaTeX-like or function patterns: \sin(x), \frac, \sqrt, or plain sin(x), cos(x)
        if re.search(r"(\\[a-zA-Z]+\(|\\frac|\\sqrt|\b(sin|cos|tan|log|ln|exp|sqrt)\()", s, re.IGNORECASE):
            return True
        # Greek pi and common unicode math symbols
        if re.search(r"[\u03c0\u00d7\u00f7]", s):
            return True
        # calculus/math keywords
        if re.search(r"\bsolve\b|\bdiff(erenti|erivative)|\bintegral\b|\d+[xX]|\btheta\b", s, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def detect_intent(query: str) -> Tuple[str, float]:
        """
        Detect the intent of a user query and return the best matching agent.

        Args:
            query: The user query string

        Returns:
            Tuple of (agent_name, confidence_score) where confidence is 0-1
        """
        query_lower = query.lower()
        q = query.strip()

        scores = {}

        # Score each agent based on keyword matches
        for agent_name, agent_info in IntentRouter.AGENT_KEYWORDS.items():
            # Pattern-based scoring (higher weight)
            pattern = agent_info["pattern"]
            pattern_matches = len(re.findall(pattern, query_lower, re.IGNORECASE))

            # Keyword-based scoring
            keyword_matches = sum(
                1 for keyword in agent_info["keywords"]
                if keyword in query_lower
            )

            # Combined score (pattern matches weighted higher)
            score = (pattern_matches * 0.7) + (keyword_matches * 0.3)
            # Boost math score if query looks like a math expression
            if agent_name == "Math" and IntentRouter.looks_like_math(query):
                score += 3.0
            # Boost math score for explicit geometry mentions
            if agent_name == "Math" and re.search(r"\bgeometry\b", query_lower):
                score += 2.0
            # Boost AP STEM for calculus/physics cues
            if agent_name == "AP STEM" and re.search(r"derivative|integral|calculus|kinematics|projectile|force|momentum", query_lower):
                score += 2.0
            scores[agent_name] = score

        # Find best match
        if not scores or max(scores.values()) == 0:
            # Default to LLM Agent for unknown queries but return a low-confidence category
            return "LLM Agent", "low"

        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]

        # Normalize score to 0-1 range (allow higher dynamic range)
        normalized_score = min(best_score / 14.0, 1.0)

        # Map short intent names to actual agent names used by AgentManager
        name_map = {
            "Math": "Math Agent",
            "AP STEM": "AP STEM Agent",
            "Music": "Music Agent",
            "Travel": "Travel Agent",
            "Games": "Games Agent",
            "HighSchool": "High School Agent",
        }

        mapped_name = name_map.get(best_agent, best_agent)

        # Map normalized numeric score to categorical labels
        if normalized_score < 0.3:
            category = "low"
        elif normalized_score < 0.7:
            category = "medium"
        else:
            category = "high"

        # If confidence is low, prefer LLM Agent as a safe fallback
        if category == "low":
            return "LLM Agent", category

        return mapped_name, category

    @staticmethod
    def get_agent_for_query(query: str) -> str:
        """Get the recommended agent name for a query (ignores confidence)."""
        agent_name, _ = IntentRouter.detect_intent(query)
        return agent_name

    @staticmethod
    def suggest_agents(query: str, top_n: int = 3) -> list:
        """
        Suggest multiple agents for a query with their confidence scores.

        Args:
            query: The user query
            top_n: Number of top suggestions to return

        Returns:
            List of tuples (agent_name, confidence_score) sorted by confidence
        """
        query_lower = query.lower()
        scores = {}

        for agent_name, agent_info in IntentRouter.AGENT_KEYWORDS.items():
            pattern = agent_info["pattern"]
            pattern_matches = len(re.findall(pattern, query_lower, re.IGNORECASE))
            keyword_matches = sum(
                1 for keyword in agent_info["keywords"]
                if keyword in query_lower
            )
            score = (pattern_matches * 0.7) + (keyword_matches * 0.3)
            # quick math detector boost
            if agent_name == "Math" and IntentRouter.looks_like_math(query):
                score += 3.0
            if agent_name == "Math" and re.search(r"\bgeometry\b", query_lower):
                score += 2.0
            if agent_name == "AP STEM" and re.search(r"derivative|integral|calculus|kinematics|projectile|force|momentum", query_lower):
                score += 2.0
            # normalize to 0-1 and store numeric for now
            scores[agent_name] = min(score / 12.0, 1.0)

        # Convert numeric scores to categories for suggestions
        def to_cat(s: float) -> str:
            if s < 0.3:
                return 'low'
            if s < 0.7:
                return 'medium'
            return 'high'

        sorted_suggestions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        # Map short names to full agent names
        name_map = {
            "Math": "Math Agent",
            "AP STEM": "AP STEM Agent",
            "Music": "Music Agent",
            "Travel": "Travel Agent",
            "Games": "Games Agent",
            "HighSchool": "High School Agent",
        }
        results = []
        for k, v in sorted_suggestions[:top_n]:
            results.append((name_map.get(k, k), to_cat(v)))
        return results
