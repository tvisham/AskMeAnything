"""SAT/ACT Agent

Provides practice MCQs, quick scoring guidance, and integrates with MathAgent's MCQ matcher
for numeric/math questions.
"""
from typing import List, Dict
import random

from .math_agent import _extract_mcq, _match_mcq


class SATACTAgent:
    name = "SAT/ACT Agent"

    def sample_practice(self, section: str = "math") -> Dict:
        """Return a practice MCQ for the given `section` and optional difficulty.

        - `section`: 'math' or 'reading'
        - The returned dict includes: `question`, `difficulty`, `explanation_text`, `explanation_html`
        """
        # A small curated bank of representative questions and explanations
        bank = {
            'math': {
                'easy': [
                    {
                        'question': "If 3x + 5 = 20, what is x?\nA) 3\nB) 5\nC) 10\nD) 15",
                        'explanation': ["Solve 3x + 5 = 20.", "3x = 15", "x = 5. Answer: B"],
                    }
                ],
                'medium': [
                    {
                        'question': "What is the value of x if 2(x - 3) = 3x + 1?\nA) -7\nB) 5\nC) -1\nD) 7",
                        'explanation': ["Expand: 2x - 6 = 3x + 1.", "Rearrange: -x = 7.", "x = -7. Answer: A"],
                    }
                ],
                'hard': [
                    {
                        'question': "If f(x)=x^2-4x+3, what is the vertex of f?\nA) (2,-1)\nB) (2,1)\nC) (-2,-1)\nD) (1,-2)",
                        'explanation': ["Vertex x-coordinate = -b/(2a) = 4/2 = 2.", "f(2) = 4 - 8 + 3 = -1.", "Vertex is (2, -1). Answer: A"],
                    }
                ],
                'geometry': [
                    {
                        'question': "In triangle ABC, angle A = 90°, AB = 3, AC = 4. What is BC?\nA) 5\nB) 6\nC) 7\nD) 4",
                        'explanation': ["Right triangle with legs 3 and 4: hypotenuse = sqrt(3^2+4^2)=5. Answer: A"],
                    }
                ],
                'probability': [
                    {
                        'question': "A bag contains 3 red and 2 blue marbles. One marble is drawn at random. What is the probability it is red?\nA) 2/5\nB) 3/5\nC) 1/2\nD) 3/2",
                        'explanation': ["3 red out of 5 total => probability 3/5. Answer: B"],
                    }
                ],
            },
            'reading': {
                'easy': [
                    {
                        'question': (
                            "Passage: 'The community garden transformed a neglected lot into a vibrant hub of neighbors, plants, and small markets."
                            " Read the passage and answer: Which choice best describes the author's tone?\n"
                            "A) Objective and neutral\nB) Sarcastic and bitter\nC) Optimistic and celebratory\nD) Confused and uncertain"
                        ),
                        'explanation': ["The passage uses positive, celebratory language about transformation and community."],
                    }
                ]
            }
        }

        # add a helper to format explanation as HTML for UI display
        def format_explanation_html(lines):
            return "<div class='explanation'>" + "".join(f"<p>{l}</p>" for l in lines) + "</div>"

        sect = (section or 'math').lower()
        # choose a random difficulty if none specified
        # allow inputs like 'math medium' by splitting if space-separated
        if ' ' in sect:
            sect, maybe_diff = sect.split(' ', 1)
            difficulty = maybe_diff.strip().lower()
        else:
            difficulty = None

        if sect not in bank:
            sect = 'math'

        available_diffs = list(bank[sect].keys())
        if difficulty and difficulty in bank[sect]:
            choices = bank[sect][difficulty]
            chosen = random.choice(choices)
            diff = difficulty
        else:
            # pick random difficulty and question
            diff = random.choice(available_diffs)
            choices = bank[sect][diff]
            chosen = random.choice(choices)

        explanation_text = "\n".join(chosen.get('explanation', []))
        explanation_html = format_explanation_html(chosen.get('explanation', []))
        return {"question": chosen['question'], "difficulty": diff, "explanation_text": explanation_text, "explanation_html": explanation_html}

    def handle(self, query: str, api_key: str = None) -> Dict:
        """Handle a user query related to SAT/ACT practice.

        If an MCQ is provided, attempt to match and return the selected option.
        Otherwise provide a short practice prompt or scoring guideline.
        """
        q = query.strip()
        if not q:
            return {"text": "Ask for a practice question with 'practice math' or paste an MCQ to check."}

        # if user asks for practice
        if q.lower().startswith('practice'):
            parts = q.split()
            section = parts[1] if len(parts) > 1 else 'math'
            return self.sample_practice(section=section.lower())

        # try to extract MCQ and match using math_agent helpers
        question, options = _extract_mcq(q)
        if question and options:
            match = _match_mcq(question, options, api_key=api_key)
            if match:
                return {"text": f"I think the answer is {match['answer']}", "match": match}
            return {"text": "I couldn't confidently match an option. Try giving a clearer numeric expression or enable LLM fallback with an API key."}

        # fallback general guidance
        if 'score' in q.lower() or 'scoring' in q.lower():
            return {"text": "SAT: Raw scores are converted to scaled scores; focus on accuracy. ACT: similar — practice timing. Use official practice tests for calibration."}

        return {"text": "Unrecognized SAT/ACT request. Try 'practice math' or paste an MCQ question."}
