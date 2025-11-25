from agents.ap_stem_agent import APSTEMAgent


def test_ap_stem_agent_calculus():
    a = APSTEMAgent()
    resp = a.handle("How do I approach a derivative question in AP Calculus?")
    assert "derivative" in resp.lower() or "calculus" in resp.lower()


def test_ap_stem_agent_physics():
    a = APSTEMAgent()
    resp = a.handle("Explain projectile motion in AP Physics")
    assert "kinematic" in resp.lower() or "diagram" in resp.lower() or "acceleration" in resp.lower()


def test_ap_stem_agent_chemistry_keywords():
    a = APSTEMAgent()
    resp = a.handle("How to do stoichiometry problems?")
    assert "stoichiometry" in resp.lower() or "mole" in resp.lower()


def test_ap_stem_agent_fallback_prompt():
    a = APSTEMAgent()
    resp = a.handle("I have a physics problem about momentum and collision")
    assert "diagram" in resp.lower() or "momentum" in resp.lower() or "start" in resp.lower()
