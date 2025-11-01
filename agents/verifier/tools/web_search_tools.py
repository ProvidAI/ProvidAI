"""Web search tools for Verifier agent."""

from typing import Dict, Any, List, Optional
import httpx
import json


async def search_web(
    query: str,
    num_results: int = 5,
    search_engine: str = "duckduckgo",
) -> Dict[str, Any]:
    """
    Search the web to verify claims or gather context.

    This allows the Verifier to fact-check results, verify data sources,
    or research best practices for validation.

    Args:
        query: Search query
        num_results: Number of results to return
        search_engine: Search engine to use (duckduckgo, serper, bing)

    Returns:
        Search results

    Example:
        # Verify a claim in task results
        results = await search_web(
            query="average customer churn rate SaaS 2024",
            num_results=5
        )
    """
    try:
        if search_engine == "duckduckgo":
            return await _search_duckduckgo(query, num_results)
        elif search_engine == "serper":
            return await _search_serper(query, num_results)
        else:
            return {
                "success": False,
                "error": f"Unsupported search engine: {search_engine}",
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Search error: {str(e)}",
        }


async def _search_duckduckgo(query: str, num_results: int) -> Dict[str, Any]:
    """Search using DuckDuckGo API."""
    try:
        async with httpx.AsyncClient() as client:
            # DuckDuckGo Instant Answer API
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            # Extract results
            results = []

            # Abstract/answer
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", ""),
                    "snippet": data.get("Abstract", ""),
                    "url": data.get("AbstractURL", ""),
                    "source": "abstract",
                })

            # Related topics
            for topic in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "source": "related",
                    })

            return {
                "success": True,
                "query": query,
                "num_results": len(results),
                "results": results[:num_results],
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"DuckDuckGo search failed: {str(e)}",
        }


async def _search_serper(query: str, num_results: int) -> Dict[str, Any]:
    """Search using Serper API (requires API key)."""
    import os

    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "SERPER_API_KEY not configured",
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": num_results,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            # Extract organic results
            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": "organic",
                })

            return {
                "success": True,
                "query": query,
                "num_results": len(results),
                "results": results,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Serper search failed: {str(e)}",
        }


async def verify_fact(
    claim: str,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify a factual claim by searching the web.

    Args:
        claim: Claim to verify
        context: Optional context for the claim

    Returns:
        Verification result with supporting evidence

    Example:
        result = await verify_fact(
            claim="The average SaaS churn rate is 5% monthly",
            context="From data analysis task results"
        )
    """
    # Search for evidence
    search_query = f"{claim} {context or ''} statistics research"
    search_results = await search_web(search_query, num_results=5)

    if not search_results.get("success"):
        return search_results

    # Analyze results
    supporting_evidence = []
    for result in search_results.get("results", []):
        snippet = result.get("snippet", "").lower()
        if any(word in snippet for word in claim.lower().split()[:3]):
            supporting_evidence.append(result)

    confidence = len(supporting_evidence) / max(len(search_results.get("results", [])), 1)

    return {
        "success": True,
        "claim": claim,
        "verified": confidence > 0.3,
        "confidence": confidence,
        "supporting_evidence": supporting_evidence,
        "all_results": search_results.get("results", []),
    }


async def check_data_source_credibility(
    source_url: str,
) -> Dict[str, Any]:
    """
    Check the credibility of a data source.

    Args:
        source_url: URL of the data source

    Returns:
        Credibility assessment

    Example:
        result = await check_data_source_credibility(
            source_url="https://example.com/data"
        )
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(source_url)
        domain = parsed.netloc

        # Search for domain reputation
        search_query = f"{domain} credibility reliability reviews"
        search_results = await search_web(search_query, num_results=5)

        if not search_results.get("success"):
            return search_results

        # Simple heuristic: check for known credible domains
        credible_domains = [
            ".gov", ".edu", ".org",
            "github.com", "kaggle.com", "data.gov",
            "worldbank.org", "who.int", "un.org",
        ]

        is_credible = any(domain.endswith(d) for d in credible_domains)

        return {
            "success": True,
            "source_url": source_url,
            "domain": domain,
            "credible": is_credible,
            "confidence": 0.8 if is_credible else 0.4,
            "search_results": search_results.get("results", []),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Credibility check failed: {str(e)}",
        }


async def research_best_practices(
    topic: str,
    industry: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Research best practices for validation.

    Args:
        topic: Topic to research
        industry: Optional industry context

    Returns:
        Best practices and guidelines

    Example:
        result = await research_best_practices(
            topic="data quality metrics",
            industry="SaaS analytics"
        )
    """
    # Build search query
    query_parts = [topic, "best practices", "guidelines"]
    if industry:
        query_parts.append(industry)

    search_query = " ".join(query_parts)
    search_results = await search_web(search_query, num_results=10)

    if not search_results.get("success"):
        return search_results

    # Extract key insights from snippets
    insights = []
    for result in search_results.get("results", []):
        snippet = result.get("snippet", "")
        if any(term in snippet.lower() for term in ["best practice", "guideline", "standard", "should"]):
            insights.append({
                "source": result.get("title", ""),
                "url": result.get("url", ""),
                "insight": snippet,
            })

    return {
        "success": True,
        "topic": topic,
        "industry": industry,
        "num_insights": len(insights),
        "insights": insights,
        "all_results": search_results.get("results", []),
    }
