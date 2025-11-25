"""College Admission Agent

Provides guidance on college essays, ranking extracurriculars, and sample messages/templates.
"""
from typing import List, Dict
import re


class CollegeAdmissionAgent:
    name = "College Admission Agent"

    def rank_extracurriculars(self, items: List[Dict]) -> List[Dict]:
        """Rank extracurricular items by impact heuristic.

        Each item is a dict with keys: 'name', 'hours_per_week' (optional), 'leadership' (bool), 'regional' (bool)
        Returns a sorted list (highest impact first) with an added 'score'.
        """
        def score(it):
            s = 0
            if it.get('leadership'):
                s += 40
            hours = float(it.get('hours_per_week', 0))
            s += min(hours * 2, 30)
            if it.get('regional'):
                s += 10
            # small bonus for named initiatives
            if re.search(r'project|initiative|founded|started', it.get('name', ''), re.I):
                s += 10
            return s

        ranked = []
        for it in items:
            itc = dict(it)
            itc['score'] = score(it)
            ranked.append(itc)
        ranked.sort(key=lambda x: x['score'], reverse=True)
        return ranked

    def essay_tips(self) -> List[str]:
        return [
            "Start with a vivid scene or moment.",
            "Show, don't tell — use specific examples.",
            "Keep your voice authentic and reflective.",
            "Answer the prompt directly; avoid unrelated tangents.",
            "Have a teacher or mentor review for clarity and grammar.",
        ]

    def essay_outline(self, prompt: str) -> List[str]:
        """Generate a short essay outline for a given prompt."""
        return [
            "Hook: Open with a vivid, specific moment relevant to the prompt.",
            "Context: Briefly explain the situation, people involved, and your role.",
            "Challenge/Action: Describe what you did and why it mattered.",
            "Reflection: Explain what you learned and how you changed.",
            "Conclusion: Tie the learning back to your future goals or fit for college.",
        ]

    def resume_suggestions(self, activities: List[Dict]) -> List[str]:
        """Return suggestions for turning activities into strong résumé bullets.

        Input items: {'name':str, 'role':str, 'impact':str, 'quantity':str}
        """
        bullets = []
        for it in activities:
            name = it.get('name', '')
            role = it.get('role', '')
            impact = it.get('impact', '')
            qty = it.get('quantity', '')
            bullet = f"{role} at {name}: {impact}"
            if qty:
                bullet += f" ({qty})"
            bullets.append(bullet)
        return bullets

    def sample_messages(self) -> Dict[str, str]:
        return {
            'teacher_recommendation_request': (
                "Subject: Recommendation Request\n\n"
                "Dear [Teacher Name],\n\nI hope you are well. I'm applying to colleges and would be honored if you could write a recommendation for me."
                " The deadline is [date]. I can provide my résumé and a summary of my activities. Thank you for considering this request.\n\nSincerely,\n[Your Name]"
            ),
            'college_visit_email': (
                "Subject: Prospective Student Visit Request\n\n"
                "Dear Admissions Office,\n\nI am a prospective applicant interested in visiting campus and meeting with a counselor."
                " Are there available tour dates in [month]? Thank you.\n\nSincerely,\n[Your Name]"
            )
        }

    def handle(self, query: str) -> Dict:
        q = query.strip()
        if not q:
            return {"text": "Ask for 'essay tips', 'rank extracurriculars' with a JSON list, or 'sample messages'."}

        if q.lower().startswith('essay'):
            return {"text": "Essay tips:", "tips": self.essay_tips()}

        if q.lower().startswith('sample'):
            return {"text": "Sample messages and templates:", "messages": self.sample_messages()}

        if q.lower().startswith('rank'):
            # expect a simple inline list representation like: rank: name|hours|leadership|regional;...
            body = q.split(':', 1)[1] if ':' in q else q
            parts = [p.strip() for p in body.split(';') if p.strip()]
            items = []
            for p in parts:
                # name|hours|leadership|regional
                seg = p.split('|')
                name = seg[0].strip()
                hours = float(seg[1]) if len(seg) > 1 and seg[1].strip() else 0
                leadership = seg[2].strip().lower() in ('1', 'yes', 'true') if len(seg) > 2 else False
                regional = seg[3].strip().lower() in ('1', 'yes', 'true') if len(seg) > 3 else False
                items.append({'name': name, 'hours_per_week': hours, 'leadership': leadership, 'regional': regional})
            ranked = self.rank_extracurriculars(items)
            return {"text": "Ranked extracurriculars:", "ranked": ranked}

        return {"text": "Unrecognized college admission request. Try 'essay tips', 'sample messages', or 'rank: name|hours|lead|regional; ...'"}
