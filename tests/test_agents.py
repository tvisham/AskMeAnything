import pytest

from agents.math_agent import MathAgent
from agents.highschool_agent import HighSchoolAgent
from agents.music_travel_agent import MusicTravelAgent
from agents.manager import AgentManager


def test_mathagent_simple_arithmetic():
    m = MathAgent()
    res = m.handle("2+3")
    assert "result" in res.lower() or "numeric" in res.lower() or "5" in res


def test_mathagent_equation_fallback_or_symbolic():
    m = MathAgent()
    res = m.handle("2*x+3=7")
    # Either sympy provides symbolic solution or fallback provides numeric check
    assert "solution" in res.lower() or "==" in res or "sympy" in res.lower()


def test_highschool_ap_calculus_keywords():
    h = HighSchoolAgent()
    assert "derivative" in h.handle("What is the derivative of x^2?").lower()
    assert "integral" in h.handle("How to integrate x^2?").lower()


def test_highschool_ap_physics_keywords():
    h = HighSchoolAgent()
    assert "kinematics" in h.handle("Explain projectile motion").lower() or "kinematics" in h.handle("projectile motion").lower()


def test_music_travel_agent():
    mt = MusicTravelAgent()
    assert "scale" in mt.handle("What is a major scale?").lower() or "scale" in mt.handle("major scale").lower()


def test_agent_manager_list_and_handle():
    am = AgentManager()
    agents = am.list_agents()
    assert isinstance(agents, list) and len(agents) >= 3
    # test routing
    resp = am.handle(agents[0], "Hello")
    assert isinstance(resp, str)
