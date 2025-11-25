"""Web search utility using SerpAPI and DuckDuckGo for agents to fetch real-time answers.

Supports multiple search backends:
- SerpAPI: Best results (requires free API key from serpapi.com)
- DuckDuckGo: Free alternative (no key needed)
"""

try:
    import requests
    _HAS_REQUESTS = True
except Exception as e:
    _HAS_REQUESTS = False
    import sys
    print(f"[web_search_util] Failed to import requests: {e}", file=sys.stderr)

# Optional Azure Web Search SDK
_HAS_AZURE_BING_SDK = False
try:
    from azure.cognitiveservices.search.websearch import WebSearchClient
    from msrest.authentication import CognitiveServicesCredentials
    _HAS_AZURE_BING_SDK = True
except Exception:
    _HAS_AZURE_BING_SDK = False

import os
import time
from functools import wraps
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Simple in-memory TTL cache to reduce repeated provider calls
_search_cache = {}
_SEARCH_CACHE_TTL = 300  # seconds


def search_web(query: str, max_results: int = 3, api_key: str = None) -> tuple:
    """Search the web using SerpAPI (primary) or DuckDuckGo (fallback).
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        api_key: Optional SerpAPI key (checks SERPAPI_KEY env var if not provided)
    
    Returns:
        Formatted search results as string
    """
    if not _HAS_REQUESTS:
        return {"text": "Web search not available (requests not installed). Install with: pip install requests", "provider": "none", "urls": []}

    # Prefer running multiple providers in parallel and aggregate results
    try:
        multi_res = search_web_multi(query, max_results=max_results, api_key=api_key)
        if multi_res and multi_res.get('text'):
            return multi_res
    except Exception:
        # fall back to single-provider chain
        pass

    # Try Bing (Azure/Bing Web Search) if a Bing key is configured
    bing_key = os.getenv("BING_API_KEY") or os.getenv("AZURE_BING_KEY")
    if bing_key:
        try:
            bing_result = _search_bing(query, max_results, bing_key)
            if bing_result:
                # bing_result may be structured already
                if isinstance(bing_result, dict):
                    return bing_result
                low = bing_result.lower()
                if any(x in low for x in ("403", "forbidden", "error")):
                    pass
                else:
                    return {"text": bing_result, "provider": "bing", "urls": _extract_urls(bing_result)}
        except Exception:
            pass

    # Try Perplexity quick HTML fetch (best-effort) when available
    try:
        perplex_result = _search_perplexity_html(query, max_results)
        if perplex_result:
            if isinstance(perplex_result, dict):
                # only return if the dict contains a meaningful text without common access warnings
                per_text = (perplex_result.get('text') or '') if isinstance(perplex_result, dict) else ''
                low = per_text.lower()
                if any(x in low for x in ("403", "forbidden")) or low.startswith("no results"):
                    pass
                else:
                    return perplex_result
            else:
                low = str(perplex_result).lower()
            if any(x in low for x in ("403", "forbidden")) or low.startswith("no results"):
                pass
            else:
                return {"text": perplex_result, "provider": "perplexity", "urls": _extract_urls(perplex_result)}
    except Exception:
        pass

    # Fallback to DuckDuckGo
    ddg_res = _search_duckduckgo(query, max_results)
    if ddg_res:
        # duckduckgo may return tuple (text, provider) or already structured
        if isinstance(ddg_res, tuple):
            ddg, provider = ddg_res
            if ddg and not ddg.lower().startswith("no results"):
                return {"text": ddg, "provider": provider, "urls": _extract_urls(ddg)}
        elif isinstance(ddg_res, dict):
            return ddg_res

    # Final fallback: try OpenAI to generate a concise web-style answer if available
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            oa = _search_openai_fallback(query, max_results, openai_key)
            if oa:
                if isinstance(oa, dict):
                    return oa
                return {"text": oa, "provider": "openai-fallback", "urls": _extract_urls(oa)}
    except Exception:
        pass

    # fallback, ddg_res may be tuple
    try:
        if isinstance(ddg_res, tuple):
            ddg, provider = ddg_res
            return {"text": ddg, "provider": provider, "urls": _extract_urls(ddg)}
    except Exception:
        pass
    return {"text": f"No results found for '{query}'", "provider": "none", "urls": []}


def _extract_urls(text: str) -> list:
    if not text or not isinstance(text, str):
        return []
    # crude URL extractor
    urls = re.findall(r"https?://[^\s)\"]+", text)
    # also capture simple www. links
    wwws = re.findall(r"www\.[^\s)\"]+", text)
    for w in wwws:
        candidate = w if w.startswith("http") else f"http://{w}"
        if candidate not in urls:
            urls.append(candidate)
    return urls


def _retry_request(func):
    """Simple retry decorator for transient request failures."""
    @wraps(func)
    def wrapper(*args, retries: int = 2, backoff: float = 0.5, **kwargs):
        last_exc = None
        for attempt in range(retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if attempt < retries:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise
        raise last_exc
    return wrapper


def _extractive_summarize(texts: list, query: str = "", max_bullets: int = 3) -> str:
    """Simple extractive summarizer: score sentences by term frequency and query relevance.

    Returns a string with up to `max_bullets` bullet points.
    """
    if not texts:
        return ""

    # Collect candidate sentences
    candidates = []
    for t in texts:
        # split into sentences using punctuation and newlines
        parts = re.split(r"(?<=[.!?\n])\s+", t)
        for p in parts:
            s = p.strip()
            if not s:
                continue
            # normalize whitespace
            s = re.sub(r"\s+", " ", s)
            candidates.append(s)

    # Deduplicate
    seen = set()
    unique = []
    for c in candidates:
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)

    if not unique:
        return ""

    # Build term frequencies and document frequencies for IDF
    tf = {}
    df = {}
    for t in texts:
        seen_in_doc = set()
        for w in re.findall(r"\w+", t.lower()):
            if len(w) < 3:
                continue
            tf[w] = tf.get(w, 0) + 1
            if w not in seen_in_doc:
                df[w] = df.get(w, 0) + 1
                seen_in_doc.add(w)

    import math
    N = max(1, len(texts))

    # Score sentences using TF-IDF and query relevance, add position bias
    qwords = set(w for w in re.findall(r"\w+", query.lower()) if len(w) > 2)
    scored = []
    for idx, s in enumerate(unique):
        words = [w for w in re.findall(r"\w+", s.lower()) if len(w) > 2]
        if not words:
            continue
        score = 0.0
        for w in words:
            idf = math.log((N / (1 + df.get(w, 0))) + 1)
            score += tf.get(w, 0) * idf
            if w in qwords:
                score += 3.0
        # position bias: earlier sentences score slightly higher
        pos_bias = 1.0 + max(0.0, (1.0 - (idx / max(1, len(unique)))) ) * 0.2
        # length preference: prefer sentences with moderate length
        len_factor = min(1.0 + (len(words) / 20.0), 2.0)
        score = score * pos_bias * len_factor
        scored.append((score, s))

    # pick top sentences
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:max_bullets]]

    # Format as bullets
    bullets = []
    for t in top:
        clean = t.strip()
        if not clean.endswith(('.', '!', '?')):
            clean = clean + '.'
        bullets.append(f"- {clean}")

    return "\n".join(bullets)


def search_web_multi(query: str, max_results: int = 3, api_key: str = None) -> tuple:
    """Run multiple providers and return an extractive summary (bullets) plus providers used.

    Returns (summary_text, provider_list_string)
    """
    # check cache first
    key = f"{query.strip().lower()}|{max_results}|{bool(api_key)}"
    now = time.time()
    cache_entry = _search_cache.get(key)
    if cache_entry:
        ts, val = cache_entry
        if now - ts < _SEARCH_CACHE_TTL:
            return val

    providers_tried = []
    snippets = []

    # Define provider callables
    tasks = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        if api_key or os.getenv("SERPAPI_KEY"):
            tasks[ex.submit(_search_serpapi, query, max_results, api_key or os.getenv("SERPAPI_KEY"))] = "serpapi"
        bing_key = os.getenv("BING_API_KEY") or os.getenv("AZURE_BING_KEY")
        if bing_key:
            tasks[ex.submit(_search_bing, query, max_results, bing_key)] = "bing"
        tasks[ex.submit(_search_perplexity_html, query, max_results)] = "perplexity"
        tasks[ex.submit(_search_duckduckgo, query, max_results)] = "duckduckgo"

        for fut in as_completed(tasks):
            provider = tasks[fut]
            try:
                res = fut.result()
                # duckduckgo returns tuple (res, prov)
                if provider == "duckduckgo":
                    if isinstance(res, tuple):
                        rtext, prov = res
                    else:
                        rtext, prov = res, "duckduckgo"
                    r = rtext
                else:
                    r = res

                if not r:
                    continue
                low = r.lower() if isinstance(r, str) else ""
                if any(x in low for x in ("403", "forbidden")) or low.startswith("no results") or low.startswith("web search error"):
                    continue
                snippets.append(r)
                providers_tried.append(provider)
            except Exception:
                continue

    # If we have no snippets, try OpenAI fallback
    if not snippets:
        try:
            oa = _search_openai_fallback(query, max_results, api_key or os.getenv("OPENAI_API_KEY"))
            if oa and not oa.lower().startswith("openai fallback not available"):
                snippets.append(oa)
                providers_tried.append("openai-fallback")
        except Exception:
            pass

    if not snippets:
        return (f"No results found for '{query}'", "none")

    summary = _extractive_summarize(snippets, query, max_bullets=3)
    provider_str = ",".join(providers_tried)
    # If OpenAI is available, polish bullets into abstractive form
    try:
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        if openai_key and summary:
            polished = _refine_with_openai(summary, query, openai_key)
            if polished:
                result = (polished, f"multi:{provider_str}")
                _search_cache[key] = (now, result)
                return result
    except Exception:
        pass

    result = (summary, f"multi:{provider_str}")
    _search_cache[key] = (now, result)
    return result


    # store in cache (unreachable here normally, but kept for clarity)


def _refine_with_openai(extractive_summary: str, query: str, api_key: str) -> str:
    """Use OpenAI ChatCompletion to rewrite extractive bullets into polished abstractive bullets."""
    try:
        import openai
    except Exception:
        return ""

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return ""

    try:
        openai.api_key = key
        system = "You are a helpful assistant that rewrites bullet points into concise, polished 2-3 bullet summaries. Keep it factual and short."
        prompt = (
            f"Rewrite the following extractive bullets into a polished 2-3 bullet summary focused on: {query}\n\n{extractive_summary}\n\nPolished summary:")
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=200,
        )
        text = resp.choices[0].message.content.strip()
        return text
    except Exception:
        return ""


def _search_serpapi(query: str, max_results: int = 3, api_key: str = None) -> str:
    """Search using SerpAPI (Google search results).
    
    Get a free API key from: https://serpapi.com
    """
    if not api_key:
        return "SerpAPI error: No API key provided"
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "num": max_results
        }
        
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        
        # Check for errors
        if "error" in data:
            return f"SerpAPI error: {data['error']}"
        
        results = []
        
        # Extract organic results
        organic_results = data.get("organic_results", [])
        for result in organic_results[:max_results]:
            try:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                
                if title and snippet:
                    results.append(f"**{title}**: {snippet}")
            except Exception:
                continue
        
        if results:
            return "\n\n".join(results)
        else:
            return "SerpAPI: No results found"
    
    except requests.exceptions.Timeout:
        return "SerpAPI error: Request timed out"
    except requests.exceptions.RequestException as e:
        return f"SerpAPI error: {str(e)[:50]}"
    except Exception as e:
        return f"SerpAPI error: {str(e)[:50]}"


def _search_duckduckgo(query: str, max_results: int = 3) -> tuple:
    """Search using DuckDuckGo's instant answer/API endpoint.
    
    This uses DuckDuckGo's JSON API which is more reliable than HTML scraping.
    """
    try:
        # Simplify query by removing common question words to get better results
        simple_query = query.strip()
        for word in ["explain", "what is", "what are", "tell me about", "describe", "latest", "current", "recent", "newest"]:
            if simple_query.lower().startswith(word):
                simple_query = simple_query[len(word):].strip()
                break
        
        url = "https://api.duckduckgo.com/"
        params = {
            "q": simple_query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        
        # Try Answer first (usually a direct answer)
        answer = data.get("Answer", "").strip()
        if answer and len(answer) > 20:
            results.append(f"**{simple_query}**: {answer}")
            return ("\n\n".join(results), "duckduckgo-json")
        
        # Try Abstract (summary/definition)
        abstract = data.get("Abstract", "").strip()
        if abstract and len(abstract) > 20:
            results.append(f"**{simple_query}**: {abstract}")
        
        # Try Definition
        if not results:
            definition = data.get("Definition", "").strip()
            if definition and len(definition) > 20:
                results.append(f"**{simple_query}**: {definition}")
        
        # Add Results if available
        if len(results) < max_results:
            result_list = data.get("Results", [])
            for result in result_list[:max_results]:
                try:
                    if isinstance(result, dict):
                        text = result.get("Text", "").strip()
                        if text and len(text) > 10 and text not in results:
                            results.append(text)
                except Exception:
                    continue
        
        # Add related topics if needed
        if len(results) < max_results:
            related = data.get("RelatedTopics", [])
            for topic in related[:max_results]:
                try:
                    if isinstance(topic, dict):
                        text = topic.get("Text", "").strip()
                        if text and len(text) > 10 and text not in results:
                            results.append(text)
                except Exception:
                    continue
        
        if results:
            return ("\n\n".join(results[:max_results]), "duckduckgo-json")
        else:
            # Attempt an HTML-based fallback (scrape the search results page) to catch cases
            # where the JSON API returns sparse data or misses non-exact queries.
            try:
                html_url = "https://html.duckduckgo.com/html/"
                params = {"q": query}
                # use retry wrapper for transient errors
                @_retry_request
                def _fetch_ddg_html(u, p, h):
                    r = requests.post(u, data=p, headers=h, timeout=8)
                    r.raise_for_status()
                    return r

                resp_html = _fetch_ddg_html(html_url, params, headers)
                text = resp_html.text
                # crude snippet extraction: find <a class="result__a"> and following snippet
                snippets = []
                import re as _re
                for m in _re.finditer(r'<a[^>]+class="result__a"[^>]*>(.*?)</a>.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', text, _re.S):
                    title = _re.sub('<[^<]+?>', '', m.group(1)).strip()
                    snippet = _re.sub('<[^<]+?>', '', m.group(2)).strip()
                    if snippet and title:
                        snippets.append(f"**{title}**: {snippet}")
                    if len(snippets) >= max_results:
                        break

                if snippets:
                    return ("\n\n".join(snippets[:max_results]), "duckduckgo-html")
                # If BeautifulSoup is available, try a more robust parse of the HTML
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(text, "html.parser")
                    found = []
                    for res in soup.select(".result__body")[:max_results]:
                        title_el = res.select_one(".result__a")
                        snippet_el = res.select_one(".result__snippet")
                        title = title_el.get_text(strip=True) if title_el else ""
                        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                        if title and snippet:
                            found.append(f"**{title}**: {snippet}")
                    if found:
                        return ("\n\n".join(found), "duckduckgo-html-bs")
                except Exception:
                    pass
                return (f"No results found for '{query}'", "none")
            except Exception:
                return (f"No results found for '{query}'", "none")
    
    except requests.exceptions.Timeout:
        return ("Web search timed out", "none")
    except requests.exceptions.RequestException as e:
        return (f"Web search error: {str(e)[:50]}", "none")
    except Exception as e:
        return (f"Web search error: {str(e)[:50]}", "none")


def _search_bing(query: str, max_results: int = 3, api_key: str = None) -> str:
    """Search using Bing Web Search API (Azure/Bing)."""
    if not _HAS_REQUESTS:
        return "Bing search not available (requests not installed)."

    key = api_key or os.getenv("BING_API_KEY") or os.getenv("AZURE_BING_KEY")
    if not key:
        return "Bing API key not provided"

    # If Azure SDK available, use it (may provide more structured responses)
    if _HAS_AZURE_BING_SDK:
        try:
            creds = CognitiveServicesCredentials(key)
            client = WebSearchClient(creds)
            res = client.web.search(query=query)
            web = getattr(res, 'web_pages', None)
            results = []
            if web and getattr(web, 'value', None):
                for item in web.value[:max_results]:
                    title = getattr(item, 'name', '')
                    snippet = getattr(item, 'snippet', '')
                    url_item = getattr(item, 'url', '')
                    if title and snippet:
                        results.append(f"**{title}**: {snippet}\n{url_item}")
            if results:
                text = "\n\n".join(results)
                return {"text": text, "provider": "bing", "urls": _extract_urls(text)}
            return {"text": "Bing: No results found", "provider": "bing", "urls": []}
        except Exception as e:
            return f"Bing SDK error: {e}"

    # Fallback to simple requests-based HTTP call
    try:
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": key}
        params = {"q": query, "count": max_results}
        resp = requests.get(url, headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        results = []
        web = data.get("webPages", {}).get("value", [])
        for item in web[:max_results]:
            title = item.get("name", "")
            snippet = item.get("snippet", "")
            url_item = item.get("url", "")
            if title and snippet:
                results.append(f"**{title}**: {snippet}\n{url_item}")

        if results:
            text = "\n\n".join(results)
            return {"text": text, "provider": "bing", "urls": _extract_urls(text)}
        return {"text": "Bing: No results found", "provider": "bing", "urls": []}
    except requests.exceptions.RequestException as e:
        return f"Bing error: {str(e)[:80]}"
    except Exception as e:
        return f"Bing error: {str(e)[:80]}"


def _search_perplexity_html(query: str, max_results: int = 3) -> str:
    """Best-effort fetch of Perplexity search page using a text proxy (r.jina.ai).

    This is a lightweight fallback and may not always produce results due to Perplexity
    using client-side rendering. It's used only when other providers return nothing.
    """
    if not _HAS_REQUESTS:
        return "Perplexity not available (requests not installed)."

    try:
        from urllib.parse import quote_plus
        proxy = "https://r.jina.ai/http://perplexity.ai/search?q=" + quote_plus(query)
        # wrap Perplexity proxy call with retry logic
        @_retry_request
        def _fetch_perplex(u, h):
            r = requests.get(u, headers=h, timeout=8)
            r.raise_for_status()
            return r

        resp = _fetch_perplex(proxy, {"User-Agent": "Mozilla/5.0"})
        # If the proxy or Perplexity returns a non-200 status (e.g., 403), treat as no results
        if resp.status_code != 200:
            # suppress raw 403 warnings and return a neutral no-results dict
            return {"text": f"No results found for '{query}'", "provider": "perplexity", "urls": []}
        # otherwise proceed
        text = resp.text
        # Take first few non-empty lines as a summary, but filter out raw links and Perplexity attribution
        raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
        snippets = []

        def is_probable_link(s: str) -> bool:
            s_low = s.lower()
            return s_low.startswith("http") or s_low.startswith("https") or "perplexity.ai" in s_low or s_low.endswith("perplexity")

        for ln in raw_lines:
            if len(snippets) >= max_results:
                break
            # skip lines that are likely just links or attribution
            if is_probable_link(ln):
                continue
            # skip very short lines
            if len(ln) < 30:
                continue
            # remove common prefixes like 'Source:' or 'perplexity:'
            cleaned = ln
            if cleaned.lower().startswith("source:"):
                cleaned = cleaned.split(":", 1)[1].strip()
            # avoid returning lines that are just file paths or navigation
            if is_probable_link(cleaned):
                continue
            snippets.append(cleaned)

        # If we didn't find long descriptive lines, fall back to first non-link lines
        if not snippets:
            for ln in raw_lines:
                if len(snippets) >= max_results:
                    break
                if is_probable_link(ln):
                    continue
                if len(ln) >= 15:
                    snippets.append(ln)

        if snippets:
            text = "\n\n".join(snippets[:max_results])
            # filter noisy warning lines like CAPTCHA or 403
            low = text.lower()
            if "403" in low or "captcha" in low or "forbidden" in low:
                return {"text": f"No results found for '{query}'", "provider": "perplexity", "urls": []}
            return {"text": text, "provider": "perplexity", "urls": _extract_urls(text)}
        return {"text": f"No results found for '{query}'", "provider": "perplexity", "urls": []}
    except requests.exceptions.HTTPError:
        # HTTP errors such as 403 should not be propagated to the user
        return {"text": f"No results found for '{query}'", "provider": "perplexity", "urls": []}
    except Exception:
        return {"text": f"No results found for '{query}'", "provider": "perplexity", "urls": []}


def _search_openai_fallback(query: str, max_results: int = 3, api_key: str = None) -> str:
    """Use OpenAI to generate a concise web-style summary when no real search results are found.

    This calls the OpenAI ChatCompletion API with a prompt to summarize/search the web.
    It is a fallback that generates an answer rather than fetching real web pages.
    """
    try:
        import openai
    except Exception:
        return "OpenAI fallback not available (openai package not installed)."

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return "OpenAI API key not set for fallback."

    try:
        openai.api_key = key
        system = (
            "You are a web research assistant. The user requested a web search. "
            "Provide a concise summary (3 short bullet points) and, if possible, example sources/URLs."
        )
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": f"Search the web and summarize: {query}"}],
            max_tokens=300,
        )
        text = resp.choices[0].message.content.strip()
        return {"text": f"**OpenAI-generated summary:**\n\n{text}", "provider": "openai-fallback", "urls": _extract_urls(text)}
    except Exception as e:
        return f"OpenAI fallback error: {e}"


def get_copilot_context(query: str, api_key: str = None) -> str:
    """Get Copilot-style context/answers for a query using web search.
    
    Args:
        query: Search query
        api_key: Optional SerpAPI key
    """
    try:
        res = search_web(query, max_results=5, api_key=api_key)
        if isinstance(res, dict) and res.get('text'):
            return f"**Search Result (via {res.get('provider','none')}):**\n\n{res.get('text')}"
        return "Unable to fetch search results."
    except Exception as e:
        return f"Error generating search context: {e}"
