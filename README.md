# Agent Chatbot — Learning Repo

This repository is a small, hands-on example for students who want to learn how to build simple agentic systems and to experiment with LLMs safely.

Who this is for
- Entry-level college students learning software design, testing, and responsible use of LLMs.

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

Have fun learning — this is a playground for learning developing with Agents, not production code.

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
