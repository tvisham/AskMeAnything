"""Music Agent

Provides basic music search/play functionality. If `youtubesearchpython` is installed,
it will search YouTube and return the top video URL which the Streamlit UI can play via `st.video`.
If a direct media URL is provided by the user, it will be returned so the UI can play it.
"""
import re

_HAS_YP = False
_HAS_YS = False
VideosSearch = None
_youtube_search_fn = None

try:
    from youtubesearchpython import VideosSearch
    _HAS_YP = True
    _youtube_search_fn = 'youtubesearchpython'
except Exception:
    try:
        # try an alternate package name used by some environments
        from youtube_search import YoutubeSearch
        _HAS_YS = True
        _youtube_search_fn = 'youtube_search'
    except Exception:
        _HAS_YP = False
        _HAS_YS = False


class MusicAgent:
    name = "Music Agent"

    def handle(self, query: str) -> str | dict:
        q = query.strip()
        if not q:
            return "Ask for an artist, song name, or provide a direct audio/video URL to play."

        # If user provides a direct media or YouTube URL, return it so UI can play
        if re.search(r"https?://", q):
            # prefer returning a dict to allow multimodal rendering
            return {"text": f"Playing provided URL:", "url": q}

        # If youtubesearchpython is available, perform a quick search and return the first video URL
        if _HAS_YP or _HAS_YS:
            try:
                if _youtube_search_fn == 'youtubesearchpython':
                    videosSearch = VideosSearch(q, limit=1)
                    res = videosSearch.result()
                    if res and res.get("result"):
                        first = res["result"][0]
                        link = first.get("link")
                        title = first.get("title")
                        return {"text": f"Top YouTube result: {title}", "video": link}
                else:
                    # youtube_search.YoutubeSearch returns a dict with 'url_suffix' often
                    res = YoutubeSearch(q, max_results=1).to_dict()
                    if res:
                        first = res[0]
                        # try to build a full youtube link from 'url_suffix' or 'id'
                        url = first.get('url_suffix') or first.get('id')
                        if url and not url.startswith('http'):
                            url = f"https://www.youtube.com{url}"
                        title = first.get('title') or first.get('name') or 'YouTube result'
                        return {"text": f"Top YouTube result: {title}", "video": url}
            except Exception as e:
                return f"Search failed: {e}"

        # Fallback: provide guidance and a sample search suggestion
        pkg_hint = 'youtubesearchpython' if not _HAS_YS else 'youtube_search or youtubesearchpython'
        return (
            "I can't perform YouTube searches here. "
            "Provide a YouTube link or install a search package to enable searching. "
            f"(Try: pip install {pkg_hint})"
        )
