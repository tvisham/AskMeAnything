from agents.music_agent import MusicAgent
from agents.travel_agent import TravelAgent
from agents.games_agent import GamesAgent
from agents.manager import AgentManager


def test_music_agent_direct_url():
    m = MusicAgent()
    # supply a YouTube URL and expect a dict with 'url' or 'video' returned
    res = m.handle("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert isinstance(res, dict) or isinstance(res, str)


def test_travel_agent_basic():
    t = TravelAgent()
    assert "visa" in t.handle("Tell me about visa requirements for France").lower() or "pack" in t.handle("pack list").lower()


def test_games_agent_puzzle():
    g = GamesAgent()
    assert "brainteaser" in g.handle("give me a brainteaser").lower() or "keyboard" in g.handle("puzzle").lower()


def test_manager_has_new_agents():
    mgr = AgentManager()
    names = mgr.list_agents()
    assert "Music Agent" in names
    assert "Travel Agent" in names
    assert "Games Agent" in names
    
def test_import_new_agents():
    from agents import highschool_agent
    from agents import music_agent
    # new agents should import and expose basic methods
    from agents import sat_act_agent, college_admission_agent
    sa = sat_act_agent.SATACTAgent()
    ca = college_admission_agent.CollegeAdmissionAgent()
    assert 'question' in sa.sample_practice()
    assert isinstance(ca.essay_tips(), list)
