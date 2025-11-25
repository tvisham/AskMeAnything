"""Games Agent

Provides quick game suggestions, rules, and simple puzzles for students.
"""

class GamesAgent:
    name = "Games Agent"

    def handle(self, query: str) -> str:
        q = query.lower().strip()
        if not q:
            return "Ask for game suggestions, rules, or a short puzzle (e.g., 'suggest a party game' or 'give me a brainteaser')."

        if "suggest" in q or "recommend" in q:
            return (
                "Try: '20 Questions' (verbal), 'Codenames' (team word game), or 'Set' (pattern recognition). "
                "For quick puzzles try a KenKen or a short logic riddle."
            )
        if "rules" in q:
            return "Ask which game's rules you want — e.g., chess, poker, or monopoly — and I'll give a concise summary."
        if "puzzle" in q or "brainteaser" in q:
            return (
                "Brainteaser: I have keys but no locks. I have space but no room. You can enter but can't go outside. What am I? (Answer: a keyboard)"
            )

        return "I can suggest games for groups, give short rule summaries, or provide small puzzles. What do you want?"
