import streamlit as st
from typing import Optional
import os
import base64
import io
import io
from functools import lru_cache
from datetime import datetime
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

from agents import AgentManager


def init_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""


def main():
    st.set_page_config(page_title="Agent Chatbot", layout="wide")
    # Header will be rendered after sidebar selection so we can include the current agent
    manager = AgentManager()

    agents = manager.list_agents()
    agents = manager.list_agents()

    init_state()

    # Sidebar: agent selection and optional OpenAI API key (session-only)
    with st.sidebar:
        st.markdown("<div style='padding-bottom:6px'><strong style='font-size:18px'>Settings</strong></div>", unsafe_allow_html=True)
        # on_change callback to immediately refresh header when agent selection changes
        def _on_agent_change():
            # ensure the selected value is stored and trigger a rerun to update header
            st.session_state["selected_agent"] = st.session_state.get("selected_agent")
            try:
                st.experimental_rerun()
            except Exception:
                pass

        # Choose agent at the top
        selected = st.selectbox("Choose an agent", agents, index=0, key="selected_agent", on_change=_on_agent_change)

        # Show intent detection directly after agent selection
        st.markdown("---")
        with st.expander("Intent Detection", expanded=False):
            st.markdown("**Intent Detection**")
            if st.session_state.get("query_input", "").strip():
                query = st.session_state.get("query_input", "").strip()
                suggestions = manager.get_suggestions(query, top_n=3)
                st.write("Suggested agents:")
                # Render categorical badges (Low / Medium / High) instead of numeric percentages
                color_map = {"low": "#ef4444", "medium": "#f59e0b", "high": "#10b981"}
                for agent, confidence in suggestions:
                    if isinstance(confidence, str):
                        cat = confidence.lower()
                    else:
                        try:
                            val = float(confidence)
                            if val < 0.3:
                                cat = 'low'
                            elif val < 0.7:
                                cat = 'medium'
                            else:
                                cat = 'high'
                        except Exception:
                            cat = 'low'

                    badge_color = color_map.get(cat, '#9ca3af')
                    badge_html = f"<span style='display:inline-block;padding:4px 8px;border-radius:12px;background:{badge_color};color:#fff;font-size:11px;font-weight:600;margin-left:8px'>{cat.title()}</span>"
                    st.markdown(f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px'><div style='font-size:13px'>{agent}</div><div>{badge_html}</div></div>", unsafe_allow_html=True)
            else:
                st.caption("Type a question to see agent suggestions")

        # LLM settings and helpers
        with st.expander("LLM / OpenAI (optional)", expanded=False):
            st.text_input("OpenAI API Key (session only)", type="password", key="openai_api_key")
            st.caption("The key is stored only in this Streamlit session and not written to disk.")
            st.markdown("<div class='sidebar-section'>LLM Fallback (global)</div>", unsafe_allow_html=True)
            global_fallback = st.checkbox("Enable LLM fallback for non-LLM agents", value=True, key="global_fallback")

        # Compact and Screenshot toggles (after LLM settings)
        compact_mode = st.checkbox("Compact mode (reduce spacing)", key="compact_mode")
        screenshot_mode = st.checkbox("Screenshot mode (minimize whitespace)", key="screenshot_mode")

        st.subheader(f"You are chatting with: {selected}")

        # Brief snippet card about the selected agent placed in a compact container
        try:
            desc = """Specialized agents for Math, AP STEM, Music, Travel and more. Use 'Auto-detect' to route questions automatically."""
            st.markdown(f"<div style='border:1px solid #e5e7eb;padding:8px;border-radius:8px;margin-bottom:6px;background:#ffffff;font-size:13px'>{desc}</div>", unsafe_allow_html=True)
        except Exception:
            pass

    # Avatar/logo removed by user request — keep banner only

    # Generate and display a simple agent banner image (in-memory PNG) so the UX has a visual cue
    def _get_agent_image_bytes(agent_name: str) -> bytes:
        if not _HAS_PIL:
            return b""
        # color palette per agent (fallback color used when key missing)
        palette = {
            "Math Agent": (60, 120, 216),
            "High School Agent": (34, 139, 34),
            "Music & Travel Agent": (200, 85, 140),
            "LLM Agent": (120, 120, 120),
            "LLM Agent (via API)": (120, 120, 120),
            "AP STEM Agent": (180, 120, 40),
        }
        bg = palette.get(agent_name, (100, 100, 200))
        # generate a smaller banner image so it doesn't dominate the UI
        banner_w, banner_h = (360, 80)
        img = Image.new("RGB", (banner_w, banner_h), color=bg)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()
        text = agent_name
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            try:
                w, h = font.getsize(text)
            except Exception:
                w, h = 180, 18
        draw.text(((banner_w - w) / 2, (banner_h - h) / 2), text, fill=(255, 255, 255), font=font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()

    # banner image removed per user request

    # Add CSS to style header and constrain sidebar/main heights so layout fits in one page
    compact = st.session_state.get('compact_mode', False)
    screenshot_mode = st.session_state.get('screenshot_mode', False)
    sidebar_w = '260px' if compact else '300px'
    header_pad = '8px' if compact else '12px'
    title_size = '18px' if compact else '20px'
    sub_size = '11px' if compact else '12px'
    block_pad_bottom = '12px' if compact else '48px'
    if screenshot_mode:
        block_pad_bottom = '6px'
    sidebar_section_fs = '12px' if compact else '13px'
    agent_header_shadow = '0 1px 2px rgba(0,0,0,0.03)' if compact else '0 1px 3px rgba(0,0,0,0.04)'
    st.markdown(f"""
    <style>
    /* Header styling with multiple animation options */
    .agent-header {{ background: linear-gradient(90deg,#ffffff,#f8fafc); padding:8px 12px; border-radius:8px; box-shadow:{agent_header_shadow}; transition: transform 200ms cubic-bezier(.2,.8,.2,1), opacity 200ms ease, box-shadow 200ms ease; margin-top:12px; }}
    .agent-header.animate-fade {{ opacity: 0; transform: translateY(-4px); }}
    .agent-header.animate-scale {{ transform: scale(0.985); box-shadow:0 6px 18px rgba(16,24,40,0.06); }}
    .agent-header.animate-flash {{ box-shadow:0 0 0 6px rgba(59,130,246,0.08); }}
    .agent-title {{ font-size:{title_size}; font-weight:600; color:#1f2937; margin:0; }}
    .agent-sub {{ font-size:{sub_size}; color:#6b7280; margin:0; }}
    /* Sidebar can still scroll if necessary; main content should flow naturally so controls remain visible */
    div[data-testid="stSidebar"] > div {{ max-height: calc(100vh - 40px); overflow:auto; }}
    div[data-testid="stAppViewContainer"] .block-container {{ padding-top:28px; padding-bottom: {block_pad_bottom}; }}
    /* Sidebar width and compact section styles */
    div[data-testid='stSidebar']{{width:{sidebar_w};}}
    .sidebar-section{{font-size:{sidebar_section_fs};padding:4px 0;margin-bottom:6px}}
    /* Tighter spacing for the settings area to reduce vertical white space */
    div[data-testid="stSidebar"] .block-container {{ padding-top:6px !important; padding-left:8px !important; padding-right:8px !important; }}
    div[data-testid="stSidebar"] .sidebar-section {{ margin-bottom:4px !important; padding:2px 0 !important; }}
    div[data-testid="stSidebar"] .stTextInput, div[data-testid="stSidebar"] .stCheckbox, div[data-testid="stSidebar"] .stSelectbox, div[data-testid="stSidebar"] .stButton {{ margin-bottom:6px !important; }}
    div[data-testid="stSidebar"] .streamlit-expander {{ margin-bottom:6px !important; padding:4px !important; }}
    /* Screenshot mode: reduce spacing between elements to fit more content on one page */
    """, unsafe_allow_html=True)

    if screenshot_mode:
        st.markdown("""
        <style>
        div[data-testid="stAppViewContainer"] .block-container { padding-bottom: 6px !important; }
        div[data-testid="stAppViewContainer"] .block-container > * { margin-bottom: 6px !important; }
        div[data-testid="stAppViewContainer"] .stButton { margin-bottom: 4px !important; padding: 6px 8px !important; }
        div[data-testid="stSidebar"] .block-container { padding-bottom: 6px !important; }
        .agent-header { margin-top:6px !important; margin-bottom:6px !important; }
        .explanation p { margin: 4px 0 !important; padding:0 !important; }
        </style>
        """, unsafe_allow_html=True)
    

    # Agent descriptions (compact) shown next to title
    AGENT_DESC = {
        'Math Agent': 'Symbolic and numeric math support — equations, simplification, and quick solves.',
        'High School Agent': 'Concise high-school level explanations and quick examples.',
        'AP STEM Agent': 'Exam-focused tips and structured setups for AP subjects.',
        'Music & Travel Agent': 'Music recommendations and travel tips.',
        'LLM Agent': 'OpenAI-backed freeform assistant (use API key for advanced answers).',
    }

    current_agent_name = st.session_state.get('selected_agent', agents[0] if agents else 'Auto-detect')
    current_desc = AGENT_DESC.get(current_agent_name, 'Specialized agent.')

    # Provider SVGs for header/browser badge and per-message badges
    PROVIDER_SVGS = {
        'serpapi': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="11" cy="11" r="8" stroke="#111827" stroke-width="1.5"/></svg>',
        'bing': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#0ea5a4" xmlns="http://www.w3.org/2000/svg"><path d="M3 12l7-9 7 9-7 9-7-9z"/></svg>',
        'duckduckgo-json': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#f97316" xmlns="http://www.w3.org/2000/svg"><path d="M12 2c2 0 3 1 4 3 1 2 4 3 4 7s-2 6-5 8-5 2-7 0-4-4-4-7 1-6 5-9z"/></svg>',
        'perplexity': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#6366f1" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7z"/></svg>',
        'openai-fallback': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#111827" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="#111827" stroke-width="1.2"/></svg>',
        'none': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#9ca3af" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9"/></svg>'
    }

    def _agent_icon_html(agent_name: str) -> str:
        # Map known agent/provider names to specific SVG assets
        mapping = {
            "openai": "openai.svg",
            "gpt": "openai.svg",
            "anthropic": "anthropic.svg",
            "claude": "anthropic.svg",
            "cohere": "cohere.svg",
            "local": "local.svg",
            "llama": "local.svg",
        }
        key = (agent_name or "").strip().lower()
        asset_file = mapping.get(key, "multi_llm.svg")
        asset_path = os.path.join("assets", asset_file)
        if os.path.exists(asset_path):
            try:
                with open(asset_path, "rb") as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode("utf-8")
                mime = "image/svg+xml" if asset_file.endswith(".svg") else "image/png"
                return f'<img src="data:{mime};base64,{b64}" style="width:48px;height:48px;display:inline-block;vertical-align:middle;margin-right:8px;"/>'
            except Exception:
                pass
        # final fallback: neutral box
        return '<div style="width:48px;height:48px;display:inline-block;background:#eee;border-radius:8px;margin-right:8px"></div>'

    # pick provider icon from session (server-side rendering)
    _last_provider = st.session_state.get('last_web_provider', '') or 'none'
    _provider_icon = PROVIDER_SVGS.get(_last_provider, PROVIDER_SVGS.get('none',''))

    header_html_main = f"""
    <div id='agent-header' class='agent-header' data-agent='{current_agent_name}' style='display:flex;align-items:center;justify-content:space-between;margin:6px 0 8px 0;'>
        <div style='display:flex;align-items:center;gap:12px'>
            {_agent_icon_html(current_agent_name)}
            <div>
                <div class='agent-title'>Agent Chatbot — Streamlit</div>
                <div class='agent-sub'>Multiple specialized agents — <strong>{current_agent_name}</strong></div>
            </div>
            <div style='margin-left:16px;padding:8px 12px;background:#ffffff;border-radius:6px;border:1px solid #eef2f7;box-shadow:0 1px 2px rgba(0,0,0,0.02);'>
                <div style='font-size:13px;font-weight:600;color:#111827;'> {current_agent_name} </div>
                <div style='font-size:12px;color:#6b7280;'> {current_desc} </div>
            </div>
        </div>
        <div style='text-align:right;color:#000000;font-size:12px;'>
            <div>Created By Tvisha Mishra</div>
            <div style='margin-top:6px;font-size:11px;color:#6b7280;display:flex;align-items:center;gap:8px;justify-content:flex-end'>
                <div style='font-weight:600;'>Browser:</div>
                <div style='display:inline-flex;align-items:center;gap:6px'>{_provider_icon}<span style="font-size:11px;color:#6b7280;">{_last_provider}</span></div>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html_main, unsafe_allow_html=True)

# small script to add animation class briefly when agent changes
    script = f"""
    <script>
    const hdr = document.getElementById('agent-header');
    if (hdr) {{
      hdr.classList.remove('animate');
      void hdr.offsetWidth; // trigger reflow
      hdr.classList.add('animate');
      setTimeout(()=> hdr.classList.remove('animate'), 500);
    }}
        // provider icon is rendered server-side; no DOM injection required
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)

    # main input widgets (with explicit keys so callbacks can read/write session_state)
    query = st.text_area("Your question", height=120, key="query_input")

    col_checkbox = st.columns(2)
    with col_checkbox[0]:
        use_llm = st.checkbox("Send this query to the LLM (use the API key above)", key="use_llm")
    with col_checkbox[1]:
        auto_route = st.checkbox("Auto-detect and route to best agent", key="auto_route", value=False)

    def _send_callback() -> None:
        q = st.session_state.get("query_input", "").strip()
        if not q:
            st.warning("Please type a question before sending.")
            return

        api_key = st.session_state.get("openai_api_key") or None
        # Build agent_fallbacks from current session value so checkbox changes take effect
        global_fallback_val = st.session_state.get("global_fallback", True)
        agent_fallbacks_current = {a: (False if a == "LLM Agent" else global_fallback_val) for a in agents}

        if st.session_state.get("use_llm"):
            # Route directly through LLMAgent to get fallback behavior
            resp = manager.handle("LLM Agent", q, fallback_pref="enabled", api_key=api_key, use_web=True, agent_fallbacks=agent_fallbacks_current)
            agent_name = "LLM Agent"
        elif st.session_state.get("auto_route"):
            # Auto-detect best agent
            detected_agent, confidence = manager.detect_intent(q)
            resp = manager.handle(detected_agent, q, fallback_pref="enabled", api_key=api_key, agent_fallbacks=agent_fallbacks_current)
            # Do not show confidence for the LLM Agent to avoid cluttering fallback displays
            if detected_agent == "LLM Agent":
                agent_name = detected_agent
            else:
                # Format confidence whether it's categorical ('low'/'medium'/'high') or numeric
                if isinstance(confidence, str):
                    conf_display = confidence.title()
                else:
                    try:
                        conf_display = f"{float(confidence):.1%}"
                    except Exception:
                        conf_display = str(confidence)
                agent_name = f"{detected_agent} (confidence: {conf_display})"
        else:
            # Use selected agent
            sel = st.session_state.get("selected_agent")
            resp = manager.handle(sel, q, fallback_pref="enabled", api_key=api_key, use_web=st.session_state.get("use_llm", False), agent_fallbacks=agent_fallbacks_current)
            agent_name = sel

        entry = {
            "agent": agent_name,
            "query": q,
            "response": resp,
            "timestamp": datetime.now().isoformat(sep=' ', timespec='seconds'),
        }
        st.session_state.history.append(entry)
        # Clear the text area by setting session state value (allowed inside callback)
        st.session_state["query_input"] = ""

    def _clear_callback() -> None:
        st.session_state.history = []

    col1, col2 = st.columns([1, 4])
    with col1:
        st.button("Send", on_click=_send_callback)
    with col2:
        st.button("Clear conversation", on_click=_clear_callback)

    # No injected footer — use the native Streamlit buttons above.

    if st.session_state.history:
        st.markdown("---")
        st.subheader("Conversation")
        # (Printable view buttons removed per user request to avoid popup/print blockers)
        # Add a lightweight download helper to export the conversation as an HTML file.
        def _build_printable_html(history):
            parts = [
                "<html><head><meta charset='utf-8'><title>Conversation Export</title>",
                "<style>body{font-family:Arial,Helvetica,sans-serif;padding:18px;color:#111}\n.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}\n.entry{border-bottom:1px solid #eee;padding:8px 0;margin-bottom:8px}\n.agent{font-weight:700}\n.query{color:#333;margin:6px 0}\n.response{background:#fafafa;padding:8px;border-radius:6px;margin:6px 0}",
                ".explanation p{margin:6px 0;color:#444;font-size:13px}</style></head><body>",
            ]
            parts.append("<div class='header'><div><h2>Agent Chat Export</h2><div style='font-size:13px;color:#666'>Generated from Agent Chatbot</div></div><div style='text-align:right;font-size:12px;color:#666'>" + datetime.now().strftime('%Y-%m-%d %H:%M') + "</div></div>")
            for e in history:
                agent = e.get('agent')
                q = e.get('query')
                r = e.get('response')
                ts = e.get('timestamp')
                parts.append("<div class='entry'>")
                parts.append(f"<div class='agent'>{agent} — <span style='font-weight:400;color:#666;font-size:12px'>{ts}</span></div>")
                parts.append(f"<div class='query'><strong>User:</strong> {q}</div>")
                if isinstance(r, dict):
                    text = r.get('text') or ''
                    question = r.get('question') or ''
                    expl_html = r.get('explanation_html') or ''
                    expl_text = r.get('explanation_text') or ''
                    if question:
                        parts.append(f"<div class='response'><strong>Question:</strong><div>{question}</div></div>")
                    if text:
                        parts.append(f"<div class='response'><strong>Response:</strong><div>{text}</div></div>")
                    if expl_html:
                        parts.append(f"<div class='explanation'><strong>Explanation:</strong>{expl_html}</div>")
                    elif expl_text:
                        parts.append(f"<div class='explanation'><strong>Explanation:</strong><div>{expl_text}</div></div>")
                else:
                    parts.append(f"<div class='response'><strong>Response:</strong><div>{r}</div></div>")
                parts.append("</div>")
            parts.append('</body></html>')
            return '\n'.join(parts)

        if st.button('Download conversation as HTML'):
            html_out = _build_printable_html(list(st.session_state.history))
            # provide download using download_button; encode to bytes
            st.download_button('Click to download HTML', data=html_out.encode('utf-8'), file_name='conversation_export.html', mime='text/html')
        for entry in reversed(st.session_state.history[-50:]):
            agent_name = entry.get("agent")
            q = entry.get("query")
            r = entry.get("response")
            ts = entry.get("timestamp")

            # layout: small avatar column + message column
            col_a, col_b = st.columns([0.6, 9])
            with col_a:
                # avatar removed; leave small spacer
                st.write(" ")
            with col_b:
                # Hide textual agent label for LLM Agent responses (keep user and timestamp)
                try:
                    is_llm = isinstance(agent_name, str) and agent_name.strip().startswith("LLM Agent")
                except Exception:
                    is_llm = False
                if is_llm:
                    st.markdown(f"*User:* {q}  \\n+*{ts}*")
                else:
                    st.markdown(f"**{agent_name}** — *User:* {q}  \\n+*{ts}*")

                # Flexible rendering for multimodal replies
                if isinstance(r, dict):
                    # dict can contain keys: text, image, audio (bytes or url), file (bytes)
                    # If structured web search data present, show provider and urls
                    if "search_provider" in r and r.get("search_provider"):
                        prov = r.get("search_provider")
                        # store last provider in session so header can show it
                        try:
                            st.session_state['last_web_provider'] = prov or 'none'
                        except Exception:
                            pass
                        # Render provider badges prominently
                        if isinstance(prov, str) and prov.startswith("multi:"):
                            parts = [p for p in prov.split(":", 1)[1].split(",") if p]
                            if parts:
                                def badge_for(p):
                                    # small inline SVG icons per provider
                                    svgs = {
                                        'serpapi': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="11" cy="11" r="8" stroke="#fff" stroke-width="1.5"/><path d="M15 15l5 5" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>',
                                        'bing': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 12l7-9 7 9-7 9-7-9z" fill="#fff"/></svg>',
                                        'duckduckgo-json': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2c2 0 3 1 4 3 1 2 4 3 4 7s-2 6-5 8-5 2-7 0-4-4-4-7 1-6 5-9c1-1 2-2 3-2z" fill="#fff"/></svg>',
                                        'duckduckgo-html': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2c2 0 3 1 4 3 1 2 4 3 4 7s-2 6-5 8-5 2-7 0-4-4-4-7 1-6 5-9c1-1 2-2 3-2z" fill="#fff"/></svg>',
                                        'perplexity': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7z" fill="#fff"/></svg>',
                                        'openai-fallback': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="#fff" stroke-width="1.2"/><path d="M8 12h8" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>',
                                    }
                                    icon = svgs.get(p, '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7z" fill="#fff"/></svg>')
                                    return f"<span class='provider-badge multi'><span class='icon'>{icon}</span>{p}</span>"

                                badges_html = "".join([badge_for(p) for p in parts])
                                st.markdown(f"**Sources:** {badges_html}", unsafe_allow_html=True)
                            else:
                                st.markdown("**Sources:** <span class='provider-badge none'>none</span>", unsafe_allow_html=True)
                        else:
                            # single provider like 'bing' or 'duckduckgo-json'
                            safe_class = prov.replace(' ', '-').lower()
                            svgs = {
                                'serpapi': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="11" cy="11" r="8" stroke="#fff" stroke-width="1.5"/><path d="M15 15l5 5" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>',
                                'bing': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 12l7-9 7 9-7 9-7-9z" fill="#fff"/></svg>',
                                'duckduckgo-json': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2c2 0 3 1 4 3 1 2 4 3 4 7s-2 6-5 8-5 2-7 0-4-4-4-7 1-6 5-9c1-1 2-2 3-2z" fill="#fff"/></svg>',
                                'duckduckgo-html': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2c2 0 3 1 4 3 1 2 4 3 4 7s-2 6-5 8-5 2-7 0-4-4-4-7 1-6 5-9c1-1 2-2 3-2z" fill="#fff"/></svg>',
                                'perplexity': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7z" fill="#fff"/></svg>',
                                'openai-fallback': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="#fff" stroke-width="1.2"/><path d="M8 12h8" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>',
                            }
                            icon = svgs.get(safe_class, '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7z" fill="#fff"/></svg>')
                            st.markdown(f"**Source:** <span class='provider-badge {safe_class}'><span class='icon'>{icon}</span>{prov}</span>", unsafe_allow_html=True)
                        # show fallback origin if present
                        if r.get("fallback_from"):
                            st.markdown(f"<span class='fallback-label'>Fallback from: {r.get('fallback_from')}</span>", unsafe_allow_html=True)
                    # Render textual content: prefer 'text', but also support 'question'
                    if "text" in r:
                        st.info(r["text"])
                    if "question" in r:
                        # render the MCQ or practice question block
                        try:
                            st.markdown(f"**Question:**\n\n{r['question']}")
                        except Exception:
                            st.write(r['question'])
                    # Render explanations if present (HTML preferred)
                    if "explanation_html" in r and r.get("explanation_html"):
                        try:
                            st.markdown(r.get("explanation_html"), unsafe_allow_html=True)
                        except Exception:
                            # fallback to plain text
                            if "explanation_text" in r:
                                st.markdown("**Explanation:**\n\n" + r.get("explanation_text", ""))
                    elif "explanation_text" in r and r.get("explanation_text"):
                        st.markdown("**Explanation:**\n\n" + r.get("explanation_text", ""))
                    # If agent suggests installing a package, show a small helper UI
                    try:
                        text_val = r.get("text") or ""
                        if isinstance(text_val, str) and "Try: pip install" in text_val:
                            # extract suggested package part
                            import re as _re
                            m = _re.search(r"Try:\s*pip install ([\w\-_, ]+)", text_val)
                            pkg = m.group(1) if m else None
                            if pkg:
                                st.markdown("**Install helper:**")
                                st.code(f"python -m pip install {pkg}")
                                st.caption("Run this in your environment (or add to requirements). Restart the app after installing.")
                    except Exception:
                        pass
                    # If there are URLs, render them as clickable links
                    if "search_urls" in r and r.get("search_urls"):
                        try:
                            urls = r.get("search_urls") or []
                            for u in urls:
                                st.markdown(f"- [Source]({u})", unsafe_allow_html=True)
                        except Exception:
                            pass
                    if "image" in r:
                        try:
                            st.image(r["image"])
                        except Exception:
                            st.write("[Could not render image]")
                    if "video" in r:
                        try:
                            st.video(r["video"])
                        except Exception:
                            st.write("[Could not render video]")
                    if "audio" in r:
                        try:
                            st.audio(r["audio"])
                        except Exception:
                            st.write("[Could not play audio]")
                    if "file" in r:
                        st.download_button("Download response", data=r["file"], file_name=r.get("file_name", "response.txt"))
                else:
                    # if response is a plain string, detect simple media URLs
                    resp_str: Any = r
                    # if the string contains a YouTube link, render as video
                    if isinstance(resp_str, str) and ("youtube.com" in resp_str or "youtu.be" in resp_str):
                        try:
                            st.video(resp_str)
                            continue
                        except Exception:
                            pass
                    if isinstance(resp_str, str) and resp_str.strip().lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                        st.image(resp_str)
                    elif isinstance(resp_str, str) and resp_str.strip().lower().endswith((".mp3", ".wav", ".ogg")):
                        st.audio(resp_str)
                    else:
                        st.info(resp_str)


@lru_cache(maxsize=32)
def create_agent_avatar(name: str, size: int = 128) -> bytes:
    """Generate a simple circular avatar PNG for the given agent name and return raw bytes suitable for st.image().

    This uses Pillow when available. The avatar contains initials and a deterministic background color based on the name.
    """
    if not _HAS_PIL:
        return b""

    # simple deterministic color from name
    colors = [
        (99, 179, 237),  # blue
        (102, 204, 153),  # green
        (255, 179, 71),   # orange
        (255, 127, 141),  # pink
        (178, 153, 255),  # purple
        (255, 205, 86),   # yellow
    ]
    idx = abs(hash(name)) % len(colors)
    bg = colors[idx]

    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # draw circle
    margin = int(size * 0.05)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=bg)

    # initials
    parts = [p for p in name.replace("&", " ").split() if p]
    if parts:
        initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()
    else:
        initials = "?"

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # scale font to image
    if font:
        # approximate sizing
        font_size = int(size * 0.4)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    try:
        bbox = draw.textbbox((0, 0), initials, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        try:
            w, h = font.getsize(initials)
        except Exception:
            w, h = int(size * 0.5), int(size * 0.3)
    pos = ((size - w) / 2, (size - h) / 2 - size * 0.03)
    draw.text(pos, initials, fill=(255, 255, 255), font=font)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue()


if __name__ == "__main__":
    main()
