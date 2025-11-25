# Agent Chatbot — Learning Repo

This repository is a small, hands-on example for students who want to learn how to build simple agentic systems and to experiment with LLMs safely.

Who this is for
- Entry-level college students learning software design, testing, and responsible use of LLMs.
- Instructors who want a compact example to teach routing, agent boundaries, and safe handling of API keys.

What you’ll find
- A Streamlit UI in `app.py` where you can pick agents, send questions, and see responses.
- Focused agents in `agents/` (math, high-school topics, music & travel, AP-STEM).
- An optional `LLM Agent` that calls an external provider only when you provide an API key.

Quick start

1. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Run the app:

```powershell
streamlit run app.py
```

3. Useful UI tips:
- Use the sidebar to pick an agent or enable `Auto-detect` (keyword routing).
- Enter an API key in the sidebar only if you want the LLM fallback to run.
- Toggle `Compact mode` to reduce spacing for a tighter layout.

Why this setup
- Agents are small so you can read and test them quickly.
- The manager handles routing and only uses the LLM when you explicitly allow it.

Safety notes
- Never commit API keys. Enter keys in the UI for short experiments.
- Rule-based agents run locally and do not send user text out by default.

Exercises & Examples

- Exercise 1 — Compare agents: Pick a question such as "Explain how gravity works in one paragraph." Ask the same question to the Math agent, the High-School agent, and the LLM agent (if you have an API key). Note differences in style, depth, and whether the answer mentions sources.

- Exercise 2 — Add a tiny agent: Create a new file `agents/echo_agent.py` that returns the same text it receives. Add a test in `tests/test_echo_agent.py` that checks the behavior and run `pytest`.

- Exercise 3 — Tweak routing (optional): Open `agents/intent_router.py` and change or add a keyword rule to route certain queries to a new `career_agent`. Try several queries and observe how agent selection changes.

Quick sample — `echo_agent.py` (copy into `agents/echo_agent.py`):

```python
class EchoAgent:
    name = "Echo Agent"

    def handle(self, query: str):
        return {"text": query, "provider": "local", "urls": []}

# Minimal test for the echo agent (put in tests/test_echo_agent.py):
def test_echo_agent():
    agent = EchoAgent()
    out = agent.handle("Hello")
    assert out["text"] == "Hello"
```

Run the tests after adding the agent:

```powershell
python -m pip install -r requirements.txt
pytest -q
```

Where to look next
- `ARCHITECTURE.md` — a short developer-focused overview and a diagram.
- `tests/` — simple tests you can run and extend.

Have fun learning — this is a playground, not production code.

New Agents
----------

This release adds two helpful agents:

- `SAT/ACT Agent` (`agents/sat_act_agent.py`): provides practice MCQs for math and reading, supports difficulty sampling, and can check pasted MCQ questions using the MathAgent's MCQ matcher. Example usage:

```python
from agents.sat_act_agent import SATACTAgent
agent = SATACTAgent()
print(agent.sample_practice('math'))
# or check an MCQ:
print(agent.handle('If 3x+5=20, what is x?\nA)3\nB)5\nC)10\nD)15'))
```

- `College Admission Agent` (`agents/college_admission_agent.py`): offers essay tips, short essay outlines for prompts, résumé/activity bullet suggestions, and a helper to rank extracurriculars by impact. Example usage:

```python
from agents.college_admission_agent import CollegeAdmissionAgent
agent = CollegeAdmissionAgent()
print(agent.essay_tips())
print(agent.essay_outline('Describe a challenge you overcame'))
print(agent.handle('sample messages'))
```

These agents are intentionally lightweight and rule-based so you can read and modify them quickly. If you want richer, personalized feedback (for essays, scoring, or detailed explanations), enable the LLM fallback by entering an API key in the app's sidebar.
 
Video Search / YouTube
- To enable the Music Agent's YouTube search feature, install one of the supported packages. From your project directory run:

```powershell
python -m pip install youtube-search-python
```

- The project also supports the `youtube-search` package as a fallback. Both packages are already listed in `requirements.txt`. If you see a message in the app that says "Try: pip install ...", install the suggested package and restart the app.

Azure Bing / Web Search Key
- To use the app's Bing/Web Search provider you can provide an Azure/Bing Web Search key. Follow these steps:

1. Create an Azure account (if you don't have one): https://azure.microsoft.com
2. In the Azure Portal, create a resource for "Bing Search v7" or "Bing Web Search" under Cognitive Services (or use Azure Cognitive Services -> Search).
3. After creating the resource, go to the resource's "Keys and Endpoint" page and copy one of the keys.

Set the key for the app (PowerShell example, session-only):

```powershell
$env:BING_API_KEY = "<your-key-here>"
# or
$env:AZURE_BING_KEY = "<your-key-here>"
```

If you want the key to persist for your user account (Windows):

```powershell
[Environment]::SetEnvironmentVariable('BING_API_KEY', '<your-key-here>', 'User')
```

The web search utility will prefer SerpAPI (if configured), try Bing (if a key is set), then Perplexity and DuckDuckGo as fallbacks.

# Agent Chatbot — Streamlit

A lightweight, modular chatbot built with Streamlit that demonstrates multiple specialized agents. Each agent encapsulates domain logic (math, AP STEM, music & travel, high-school topics) while an optional LLM-backed agent provides richer natural-language responses when configured.

Quick highlights

- Lightweight and modular — easy to extend with new agents.
- Rule-based agents run locally and do not send user text off the machine.
- Optional LLM Agent integrates with OpenAI (or other providers) when an API key is supplied.

Run locally (Windows PowerShell)

```powershell
python -m pip install -r requirements.txt
````markdown
# Agent Chatbot — Learning Repo

This repo is a small, hands-on example for students who want to learn how to build simple agentic systems and how to experiment with LLMs safely.

Who this is for
- Entry-level college students learning software design, testing, and how LLMs can be integrated as optional helpers.
- Instructors who want a compact example to teach routing, agent boundaries, and safe use of API keys.

What you’ll find
- A Streamlit UI in `app.py` that shows how to pick agents, send questions, and display results.
- Small, focused agents in the `agents/` folder (math, high-school topics, music & travel, AP-STEM).
- An optional `LLM Agent` that calls an external provider only when you provide an API key.

Quick start

1. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Run the app:

```powershell
streamlit run app.py
```

3. Try these exercises:
- Switch agents in the sidebar and ask the same question to see different behaviors.
- Turn on `Auto-detect` to let the app pick an agent using simple keyword routing.
- Enter an OpenAI API key in the sidebar to experiment with LLM fallbacks (optional).

Why this setup
- Each agent is small so you can read and test it quickly.
- The manager handles routing and an explicit fallback to the LLM so network calls are always by choice.

Notes on safety
- Do not commit API keys. You can enter keys in the sidebar for short experiments.
- Rule-based agents run locally and do not send data out by default.

Learning activities
- Add a new agent and write tests for it.
- Replace the keyword router with a small classifier and compare results.
- Try changing the fallback rules to see how user experience changes.

Where to look next
- `ARCHITECTURE.md` — a short developer-focused overview and a diagram.
- `tests/` — simple tests you can run and extend.

Have fun learning — this is a playground, not production code.

````
