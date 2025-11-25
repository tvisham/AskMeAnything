import random


class MusicTravelAgent:
    name = "Music & Travel Agent"

    MUSIC_FAQ = {
        "scale": "A major scale follows the pattern W-W-H-W-W-W-H (W=whole step, H=half step).",
        "chord": "A major triad uses the 1st, 3rd, and 5th notes of the major scale. E.g., C-E-G for C major.",
        "tempo": "Tempo is measured in BPM (beats per minute). Typical pop is 100-130 BPM.",
    }

    TRAVEL_TIPS = [
        "Pack a small first-aid kit and photocopies of important documents.",
        "Check visa requirements and local entry rules before travel.",
        "Use offline maps and save key addresses in advance.",
    ]

    def handle(self, query: str) -> str:
        q = query.lower()
        if not q.strip():
            return "Ask me a music or travel question — e.g., 'What is a major scale?' or 'Travel tips for Paris?'."

        for k, v in self.MUSIC_FAQ.items():
            if k in q:
                return v

        if "travel" in q or "trip" in q or "visa" in q or "pack" in q:
            return random.choice(self.TRAVEL_TIPS)

        if "song" in q or "compose" in q or "melody" in q:
            return "Start with a short motif (2-4 notes) and repeat it with small variations. Think about rhythm and contour."

        return "I can answer basic music-theory questions (scales, chords, tempo) and give short travel tips. Ask something specific."
