"""
AI/ML — Nidhi
--------------
WEB RESEARCH AGENT

This is the piece that actually goes out onto the internet and looks for
real suppliers / distributors / buyers for an at-risk product.

Primary engine: DuckDuckGo Search via the `ddgs` package.
  - 100% free, no API key, no signup, no rate-limit hassle for a hackathon.
  - pip install ddgs

Optional upgrade: Tavily (https://tavily.com) gives cleaner, AI-summarized
results and has a free tier (1000 searches/month) if you have time to grab
a key. It's wired in below behind an env var — just set TAVILY_API_KEY and
it will be used automatically instead of DuckDuckGo.

IMPORTANT (per the original pitch): this agent only RESEARCHES and
RECOMMENDS. It never contacts or transacts with a real supplier — a human
must click "Approve" in the dashboard before anything happens for real.
"""

import os
from typing import List, Dict

USE_TAVILY = bool(os.environ.get("TAVILY_API_KEY"))


def _search_duckduckgo(query: str, max_results: int = 5) -> List[Dict]:
    from ddgs import DDGS  # pip install ddgs

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title"),
                "snippet": r.get("body"),
                "url": r.get("href"),
            })
    return results


def _search_tavily(query: str, max_results: int = 5) -> List[Dict]:
    import requests

    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": os.environ["TAVILY_API_KEY"],
            "query": query,
            "max_results": max_results,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return [
        {"title": r.get("title"), "snippet": r.get("content"), "url": r.get("url")}
        for r in data.get("results", [])
    ]


def web_search(query: str, max_results: int = 5) -> List[Dict]:
    """Single entry point — picks Tavily if a key is set, else free DuckDuckGo."""
    try:
        if USE_TAVILY:
            return _search_tavily(query, max_results)
        return _search_duckduckgo(query, max_results)
    except Exception as e:
        # Never let a flaky network call crash the whole pipeline in a demo
        return [{"title": "search_error", "snippet": str(e), "url": ""}]


def find_supplier_options(product_name: str, category: str, region: str = "India") -> List[Dict]:
    """
    Runs a few targeted live searches to find real-world options for
    offloading / re-selling / distributing an at-risk product.
    Returns a deduplicated list of {title, snippet, url} candidate options.
    """
    queries = [
        f"wholesale distributors for {category} products in {region}",
        f"buy surplus {category} inventory {region}",
        f"liquidation buyers for {product_name} {category} {region}",
        f"B2B marketplaces to sell excess {category} stock {region}",
    ]

    all_results: List[Dict] = []
    seen_urls = set()
    for q in queries:
        for r in web_search(q, max_results=4):
            url = r.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    return all_results[:10]  # cap for readability in the demo


if __name__ == "__main__":
    # Quick manual test: python -m ai_ml.web_research_agent
    options = find_supplier_options("Product X", "general retail")
    for o in options:
        print("-", o["title"], "|", o["url"])
