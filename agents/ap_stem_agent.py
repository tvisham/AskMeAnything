"""AP STEM Agent

Provides concise, exam-focused answers for STEM-related AP subjects. This agent is
designed to give high-school students quick explanations, formulas, problem setup
tips, and exam-style guidance. For step-by-step worked solutions the agent will
encourage problem setup and may delegate to the LLM Agent when available.
"""
import re
from typing import List


class APSTEMAgent:
    name = "AP STEM Agent"

    # Brief human-written guidance for common AP STEM subjects
    KB = {
        "ap calculus": (
            "AP Calculus (AB/BC): Focus on limits, derivatives, integrals, the Fundamental Theorem of Calculus, "
            "and applications (optimization, related rates, area/volume). BC adds parametric, polar, and series. "
            "When solving, clearly state: 1) what is known, 2) which theorem/formula applies, and 3) show algebraic steps."
        ),
        "ap physics": (
            "AP Physics (1, 2, C): Start by drawing a clear diagram, define a coordinate system, list known quantities, "
            "and identify which laws apply (Newton's laws, energy conservation, kinematics, electromagnetism for 2/C). "
            "Show units in each step and box your final answer with units."
        ),
        "ap chemistry": (
            "AP Chemistry: Keep track of moles, molar masses, and significant figures. For equilibrium problems write the balanced reaction, "
            "define initial/change/equilibrium (ICE) tables, and relate concentrations to K (Kc or Kp). For titrations, follow stoichiometry carefully."
        ),
        "ap biology": (
            "AP Biology: Understand core principles (cell structure, energy flow, genetics, evolution). Answer free-response by connecting evidence to claims, "
            "and use correct biological terms. Practice interpreting graphs and experimental setups."
        ),
        "ap statistics": (
            "AP Statistics: Be fluent with descriptive stats, probability rules, sampling distributions, confidence intervals, and hypothesis testing. "
            "Always state null/alternative hypotheses and check conditions before applying formulas."
        ),
        "ap computer science": (
            "AP Computer Science A: Focus on Java syntax, OOP basics, arrays, loops, recursion, and tracing code. For code questions, write clear pseudocode and explain complexity when asked."
        ),
        "ap environmental": (
            "AP Environmental Science: Understand ecosystems, energy flow, biogeochemical cycles, and human impacts. Use data to support policy or management recommendations."
        ),
    }

    AP_SUBJECT_KEYS: List[str] = list(KB.keys())

    def _solve_derivative(self, query: str) -> str:
        """Attempt to solve derivatives symbolically."""
        try:
            from sympy import symbols, diff, simplify, sympify
            
            # Extract the expression after "derivative"
            expr_str = query.lower()
            
            # Remove common question words
            for phrase in ["find derivative of", "find the derivative of", "derivative of", "derivative"]:
                if phrase in expr_str:
                    expr_str = expr_str.replace(phrase, "").strip()
                    break
            
            # Handle common notation
            expr_str = expr_str.replace("^", "**")
            expr_str = expr_str.replace("sin(", "sin(").replace("cos(", "cos(").replace("tan(", "tan(")
            expr_str = expr_str.replace("e^", "exp(").replace("ln(", "log(")
            
            if not expr_str or len(expr_str.strip()) < 1:
                return "Please provide an expression to differentiate, e.g., 'derivative of x^2 + 3x'"
            
            x = symbols('x')
            expr = sympify(expr_str)
            derivative = diff(expr, x)
            simplified = simplify(derivative)
            
            return f"f(x) = {expr}\nDerivative: f'(x) = {simplified}"
        except Exception as e:
            return f"Could not solve derivative. Try a simpler expression like 'derivative of x^2' or 'derivative of sin(x)'"

    def _solve_integral(self, query: str) -> str:
        """Attempt to solve integrals symbolically."""
        try:
            from sympy import symbols, integrate, simplify, sympify
            
            # Extract the expression after "integral"
            expr_str = query.lower()
            
            # Remove common question words
            for phrase in ["find integral of", "find the integral of", "integral of", "antiderivative of", "integrate", "integral"]:
                if phrase in expr_str:
                    expr_str = expr_str.replace(phrase, "").strip()
                    break
            
            # Handle common notation
            expr_str = expr_str.replace("^", "**")
            expr_str = expr_str.replace("sin(", "sin(").replace("cos(", "cos(").replace("tan(", "tan(")
            expr_str = expr_str.replace("e^", "exp(").replace("ln(", "log(")
            
            if not expr_str or len(expr_str.strip()) < 1:
                return "Please provide an expression to integrate, e.g., 'integral of x^2 + 3x'"
            
            x = symbols('x')
            expr = sympify(expr_str)
            antiderivative = integrate(expr, x)
            
            return f"f(x) = {expr}\nAntiderivative: F(x) = {antiderivative} + C"
        except Exception as e:
            return f"Could not solve integral. Try a simpler expression like 'integral of x^2' or 'integral of sin(x)'"

    def handle(self, query: str, fallback_pref: str = None, api_key: str = None, use_web: bool = False) -> str:
        q = query.lower().strip()
        if not q:
            return (
                "Ask an AP STEM question (Calculus, Physics, Chemistry, Biology, Statistics, Computer Science, Environmental). "
                "Give details for numerical help, or ask conceptual questions for quick tips."
            )

        # Handle derivatives first
        if any(k in q for k in ["derivative", "derivative of", "diff", "d/dx"]):
            return self._solve_derivative(q)
        
        # Handle integrals
        if any(k in q for k in ["integral", "integrate", "antiderivative"]):
            return self._solve_integral(q)

        # Direct subject lookup
        for key in self.AP_SUBJECT_KEYS:
            if key in q:
                return self.KB[key]

        # Topic-specific heuristics and richer canned responses with formulas and examples
        if re.search(r"limit|fundamental theorem", q):
            return (
                "Calculus tip: For limits, check if direct substitution works; if indeterminate, try factoring, conjugate, or L'Hôpital's rule. "
                "The Fundamental Theorem connects antiderivatives to definite integrals."
            )

        if re.search(r"stoichiometry|mole|equilibrium|k(eq)|titration|oxidation|reduction", q):
            return (
                "Chemistry tip: Balance the reaction first. Convert grams to moles using molar mass, then use stoichiometric ratios. "
                "For equilibrium, write the balanced equation and an ICE table, then express K in terms of concentrations. For titrations, identify limiting reactant and use stoichiometry to find concentrations."
            )

        if re.search(r"kinematics|projectile|force|momentum|energy|work", q):
            return (
                "Physics tip: Draw a free-body diagram, define axes, and list knowns with units. Use kinematic equations (v = v0 + at, s = s0 + v0 t + 0.5 a t^2) for constant acceleration, and energy/momentum conservation where applicable. "
                "Include a solved-structure: 1) diagram and variables, 2) governing equations, 3) algebraic steps, 4) numerical substitution and units."
            )

        if re.search(r"probability|confidence interval|hypothesis test|p-value|sampling", q):
            return (
                "Statistics tip: Check assumptions (random sampling, independence, sample size). For confidence intervals, use estimate ± margin where margin = z*SE. For hypothesis tests state H0 and H1, compute test statistic and p-value, and compare to alpha. Show interpretation in context."
            )

        if re.search(r"array|recursion|class|object|inheritance|runtime complexity", q):
            return (
                "CS tip: For code tracing, list variable states per step. For algorithmic problems, provide clear pseudocode, then analyze time and space complexity (Big-O). Include edge cases and simple test cases."
            )

        # If none matched, provide a richer fallback and optionally invoke LLM if API key is provided
        fallback_text = (
            "Please provide more details or paste a specific problem and I'll help with definitions, formulas, or setup."
        )

        # If an API key is provided and caller requested LLM assistance, delegate to LLM for richer worked solution
        if api_key:
            try:
                from .llm_agent import LLMAgent
                llm = LLMAgent()
                llm_resp = llm.handle(query, fallback_pref=fallback_pref, api_key=api_key, use_web=use_web)
                if isinstance(llm_resp, dict):
                    return llm_resp
                return { 'text': llm_resp }
            except Exception:
                # ignore LLM failures and return fallback_text
                return fallback_text

        return fallback_text
