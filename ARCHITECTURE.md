# Architecture — Agent Chatbot (Streamlit)

This document explains how the code is organized and why. It is written for developers and instructors who want a clear, practical view of how the example agents and optional LLM integration work together for teaching and experimentation.

What this project is for
------------------------
- A sandbox for learning how small, focused agents can be composed in a single app.
- A demonstration of simple routing, clear boundaries between rule-based logic and LLM-assisted responses, and safe handling of optional API keys.
- Not a production system — designed to be readable, testable, and easy to extend.

Key components
--------------
- `app.py` — Streamlit UI and session management. Handles user input, agent selection, and rendering of conversation history.
- `agents/` — collection of agent modules. Each agent implements a `name` and a `handle(query, ...)` interface. Examples:
  - `math_agent.py`: local numeric and symbolic helpers (uses `sympy` when available).
  - `highschool_agent.py`: concise, curriculum-style answers.
  - `music_travel_agent.py`: domain helpers for music and travel questions.
  - `ap_stem_agent.py`: AP-level focused guidance.
  - `llm_agent.py` and `llm_wrapper.py`: optional LLM calls (used only when an API key is provided).
- `agents/manager.py` — routes queries and implements fallback logic. It can auto-detect an agent, invoke a chosen agent, and forward to the LLM Agent when local logic is insufficient.
- `agents/intent_router.py` — keyword and pattern-based intent detection used for auto-routing. It returns categorical confidences (low/medium/high) to keep UI feedback simple and actionable.

Runtime flow (concise)
----------------------
1. User chooses an agent or enables auto-route in the sidebar and submits a query.
2. `AgentManager` receives the query and either routes it to the selected agent or uses `IntentRouter` to pick one.
3. The chosen agent processes the query locally. If the result is insufficient and an API key is available (and fallback is enabled), `AgentManager` requests the `LLM Agent` for a refined answer.
4. Responses are appended to session state and rendered in the Streamlit UI; when web sources are used, provider metadata and source links are shown.

Design notes (developer-focused)
--------------------------------
- Agents are intentionally small and focused: this keeps unit tests simple and makes it straightforward to replace or extend an agent.
- Fallback to LLM is explicit and opt-in: keys can be provided in the sidebar for experimentation without risking accidental network calls.
- Intent detection is conservative: when confidence is low the UI indicates that the system recommends using the LLM fallback rather than pretending to be certain.

Security and privacy
--------------------
- Do not hard-code API keys. Use environment variables or enter a key in the Streamlit sidebar for short-lived testing.
- Rule-based agents keep data local. Any data sent to an external LLM provider should be treated as potentially observable by that provider.

Educational guidance
--------------------
- Use this repo as a starting point for lessons about modular agent design, safe LLM integration, and testing strategies.
- Suggested exercises:
  - Add a new agent and write unit tests that verify its routing and output.
  - Replace the intent router with a trained classifier and compare routing behavior.
  - Swap the LLM provider or add multiple provider badges to observe fallbacks.

Diagram
-------
See `assets/architecture.svg` for a compact visual of components and data flow.
