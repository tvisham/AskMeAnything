import re


class HighSchoolAgent:
    name = "High School Agent"

    FAQ = {
        "pythagoras": "In a right-angled triangle, a^2 + b^2 = c^2 where c is the hypotenuse.",
        "photosynthesis": "Photosynthesis converts sunlight into chemical energy in plants: 6CO2 + 6H2O -> C6H12O6 + 6O2.",
        "cell": "Cells are the basic unit of life; eukaryotic cells have a nucleus, prokaryotic cells do not.",
        "newton": "Newton's second law: F = m * a (force = mass × acceleration).",
        "acid": "An acid donates H+ ions in water; a base accepts H+ ions. pH < 7 is acidic.",
    }

    def handle(self, query: str) -> str:
        q = query.lower().strip()
        if not q:
            return "Ask me a question related to high-school topics (math, physics, chemistry, biology, etc.)."

        # simple keyword lookup
        for key, val in self.FAQ.items():
            if key in q:
                # Return the FAQ answer if matched
                return val

        # Add short AP-style sample questions + model answers (human-written, concise)
        samples = {
                    "ap calc sample derivative": (
                        "Question: Find the derivative of f(x)=x^3-5x+2 at x=2.\n"
                        "Answer: f'(x)=3x^2-5, so f'(2)=3*(2)^2-5=12-5=7."
                    ),
                    "ap calc sample integral": (
                        "Question: Compute the definite integral of x from 0 to 2.\n"
                        "Answer: ∫_0^2 x dx = [x^2/2]_0^2 = (4/2)-0 = 2."
                    ),
                    "ap physics projectile": (
                        "Question: A ball is thrown at 20 m/s at 30° above the horizontal. Ignore air resistance. What is the horizontal range?\n"
                        "Answer: Range = (v^2 * sin(2θ))/g. Here v=20, θ=30°, sin(60°)=√3/2, so R = 400*(√3/2)/9.8 ≈ (400*0.866)/9.8 ≈ 346.4/9.8 ≈ 35.35 m."
                    ),
                    "ap chem stoichiometry": (
                        "Question: How many moles are in 18.0 g of H2O?\n"
                        "Answer: Molar mass H2O ≈ 18.0 g/mol, so moles = 18.0 g / 18.0 g/mol = 1.0 mol."
                    ),
                    "ap stats ci": (
                        "Question: Sample mean 50, sd 10, n=25. What is a 95% CI for the mean?\n"
                        "Answer: SE = 10/√25 = 2. 95% CI ≈ mean ± 1.96*SE = 50 ± 3.92 → (46.08, 53.92)."
                    ),
                    "ap econ elasticity": (
                        "Question: If price rises 10% and quantity demanded falls 15%, what is the price elasticity?\n"
                        "Answer: Elasticity = %ΔQ / %ΔP = -15% / 10% = -1.5 (elastic)."
                    ),
                }

        for sk, sv in samples.items():
            if sk in q:
                return sv

        if re.search(r"derivative|differentiate|deriv of|d/dx", q):
            return (
                "Derivatives — quick rule: derivative of x^n is n*x^(n-1). "
                "For trig: d/dx sin x = cos x; d/dx cos x = -sin x. Ask a specific function for step-by-step help."
            )
        if re.search(r"integral|integrate|antiderivative|∫", q):
            return (
                "Integrals — common rule: ∫ x^n dx = x^(n+1)/(n+1) + C for n != -1. "
                "For definite integrals, provide bounds like 'integral of x^2 from 0 to 2'."
            )

        # AP Physics quick hits
        if re.search(r"kinematics|velocity|acceleration|projectile", q):
            return (
                "Kinematics: use v = v0 + a*t, x = x0 + v0*t + 1/2*a*t^2, and v^2 = v0^2 + 2*a*(x-x0). "
                "Specify which variable you need and the knowns."
            )
        if re.search(r"force|momentum|impulse|energy|work", q):
            return (
                "Physics formulas: F = m*a; momentum p = m*v; kinetic energy KE = 1/2*m*v^2; work W = F*d (in direction of force)."
            )

        # AP Chemistry quick hits
        if re.search(r"stoichiometry|mole|moles|molarity|mol/L", q):
            return (
                "Stoichiometry: convert grams to moles using mol = grams / molar_mass. For solutions, M = moles solute / liters solution. "
                "Provide an equation or amounts for numerical help."
            )
        if re.search(r"equilibrium|k(eq)|k\s*=?\s*\w+|le chatelier", q):
            return (
                "Chemical equilibrium: for aA + bB <-> cC + dD, Kc = [C]^c[D]^d / ([A]^a[B]^b). "
                "Le Chatelier's principle: a system shifts to counteract changes in concentration, pressure, or temperature."
            )

        # AP Economics quick hits
        if re.search(r"supply|demand|elasticity|equilibrium price|market equilibrium", q):
            return (
                "Economics basics: Equilibrium where supply = demand. Price elasticity of demand = % change in quantity / % change in price. "
                "Elasticity >1 is elastic, <1 inelastic. Ask a specific scenario for calculations."
            )
        if re.search(r"gdp|inflation|fiscal policy|monetary policy|aggregate demand|aggregate supply", q):
            return (
                "Macro basics: GDP measures total output. Fiscal policy uses government spending/taxes; monetary policy uses central bank actions (e.g., interest rates). "
                "Inflation is a general rise in prices — many causes include demand-pull and cost-push."
            )

        return (
            "Please provide more details or paste a specific problem and I'll help with definitions, formulas, or setup."
        )
