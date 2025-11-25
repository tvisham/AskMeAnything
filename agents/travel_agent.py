"""Travel Agent

Separated from the original Music & Travel agent; provides travel tips, visa checks guidance and packing lists.
"""


class TravelAgent:
    name = "Travel Agent"

    TIPS = [
        "Pack light and bring copies of important documents.",
        "Check visa and entry requirements well before travel.",
        "Use offline maps and save local emergency contacts.",
    ]

    def handle(self, query: str) -> str:
        q = query.lower().strip()
        if not q:
            return "Ask me travel questions: packing, visas, safety, or basic trip planning tips."

        if "visa" in q:
            return "Visa requirements vary by country. Check the embassy site for the destination and allow time for processing."
        if "pack" in q or "packing" in q:
            return "Tip: make a packing list separated by clothes, documents, electronics, and medications. Roll clothes to save space."
        if "safety" in q or "health" in q:
            return "Be aware of local advisories, keep copies of prescriptions, and check vaccination requirements for your destination."

        return self.TIPS[0]
