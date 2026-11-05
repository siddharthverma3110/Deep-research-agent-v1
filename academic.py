"""Academic paper search via the OpenAlex API (free, no key needed)."""
import os

import httpx

API = "https://api.openalex.org/works"


def _abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos = {i: w for w, idxs in inv.items() for i in idxs}
    return " ".join(pos[i] for i in sorted(pos))


def _authors(auths: list) -> str:
    names = [a.get("author", {}).get("display_name") for a in auths or []]
    names = [n for n in names if n]
    return ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")


async def search_papers(query: str, limit: int = 5) -> list[dict]:
    params = {
        "search": query,
        "per-page": limit,
        "filter": "has_abstract:true",
        "select": "id,title,doi,publication_year,authorships,abstract_inverted_index,primary_location,cited_by_count",
    }
    if os.getenv("OPENALEX_EMAIL"):  # optional: puts you in OpenAlex's polite pool
        params["mailto"] = os.environ["OPENALEX_EMAIL"]
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(API, params=params)
            r.raise_for_status()
            works = r.json().get("results", [])
    except Exception:
        return []

    papers = []
    for w in works:
        title = w.get("title")
        loc = w.get("primary_location") or {}
        url = w.get("doi") or loc.get("landing_page_url") or w.get("id")
        if not title or not url:
            continue
        abstract = _abstract(w.get("abstract_inverted_index"))
        papers.append({
            "title": title,
            "url": url,
            "authors": _authors(w.get("authorships")),
            "year": w.get("publication_year"),
            "venue": (loc.get("source") or {}).get("display_name") or "",
            "cited_by": w.get("cited_by_count"),
            "abstract": abstract[:900],
            "snippet": abstract[:280],
        })
    return papers
