"""
arXiv API client and ranking logic.
"""

import requests
import feedparser
import time
import math
from typing import List, Optional
from datetime import datetime
from difflib import SequenceMatcher

from renderarxiv.models import Paper

# arXiv API endpoint
ARXIV_API = "http://export.arxiv.org/api/query"

# Semantic Scholar API (for citation counts)
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper"


def search_arxiv(
    query: str,
    max_results: int = 50,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    category: Optional[str] = None,
) -> List[Paper]:
    """
    Search arXiv using the official API.
    
    Args:
        query: Search query string
        max_results: Maximum number of papers to return
        sort_by: Sort criterion (relevance, lastUpdatedDate, submittedDate)
        sort_order: Sort order (ascending, descending)
        category: Filter by category (e.g., 'cs.LG', 'cs.AI')
    
    Returns:
        List of Paper objects
    """
    # Build query with category filter if specified
    search_query = query
    if category:
        search_query = f"cat:{category} AND {query}"
    
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    
    print(f"🔎 Searching arXiv for: '{query}'")
    if category:
        print(f"   Filtering by category: {category}")
    
    try:
        response = requests.get(ARXIV_API, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse the Atom feed
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("⚠️ No results found")
            return []
        
        papers = []
        for entry in feed.entries:
            # Extract arXiv ID from the URL
            arxiv_id = entry.id.split('/abs/')[-1]
            
            # Parse authors
            authors = [author.name for author in entry.authors] if hasattr(entry, 'authors') else []
            
            # Parse categories
            categories = []
            if hasattr(entry, 'tags'):
                for tag in entry.tags:
                    if hasattr(tag, 'term'):
                        categories.append(tag.term)
                    elif isinstance(tag, dict) and 'term' in tag:
                        categories.append(tag['term'])
            
            # Get primary category
            primary_category = "unknown"
            if hasattr(entry, 'arxiv_primary_category'):
                if hasattr(entry.arxiv_primary_category, 'term'):
                    primary_category = entry.arxiv_primary_category.term
                elif isinstance(entry.arxiv_primary_category, dict):
                    primary_category = entry.arxiv_primary_category.get('term', 'unknown')
            elif categories:
                primary_category = categories[0]
            
            # Extract optional fields
            comment = entry.arxiv_comment if hasattr(entry, 'arxiv_comment') else None
            journal_ref = entry.arxiv_journal_ref if hasattr(entry, 'arxiv_journal_ref') else None
            doi = entry.arxiv_doi if hasattr(entry, 'arxiv_doi') else None
            
            paper = Paper(
                arxiv_id=arxiv_id,
                title=entry.title.replace('\n', ' ').strip(),
                authors=authors,
                abstract=entry.summary.replace('\n', ' ').strip(),
                pdf_url=entry.link.replace('/abs/', '/pdf/'),
                arxiv_url=entry.link,
                published=entry.published,
                updated=entry.updated,
                categories=categories,
                primary_category=primary_category,
                comment=comment,
                journal_ref=journal_ref,
                doi=doi,
            )
            papers.append(paper)
        
        print(f"✓ Retrieved {len(papers)} papers")
        return papers
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return []
    except Exception as e:
        print(f"❌ Error parsing results: {e}")
        return []


def fetch_citations_batch(papers: List[Paper], batch_size: int = 100) -> List[Paper]:
    """
    Fetch citation counts from Semantic Scholar API.
    Updates papers in-place with citation counts.
    """
    if not papers:
        return papers
    
    print(f"📊 Fetching citation counts from Semantic Scholar...")
    
    # Process in batches to avoid rate limits
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        
        for paper in batch:
            try:
                # Try searching by arXiv ID
                url = f"{SEMANTIC_SCHOLAR_API}/arXiv:{paper.arxiv_id}"
                response = requests.get(
                    url,
                    params={"fields": "citationCount"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    paper.citations = data.get("citationCount", 0)
                else:
                    paper.citations = 0
                
                # Be nice to the API
                time.sleep(0.1)
                
            except Exception as e:
                # If API fails, just skip citation count
                paper.citations = 0
                continue
    
    total_citations = sum(p.citations or 0 for p in papers)
    print(f"✓ Retrieved citations (total: {total_citations})")
    
    return papers


def rank_papers(
    query: str,
    papers: List[Paper],
    mode: str = "balanced",
    max_results: int = 20,
) -> List[Paper]:
    """
    Rank and filter papers based on mode.
    
    Modes:
        balanced: Mix of relevance, citations, and recency
        recent: Newest papers first
        cited: Most cited papers first
        influential: High citations + recency
        relevant: Pure relevance to query
    """
    if not papers:
        return papers
    
    # Filter to max_results
    if mode == "recent":
        # Sort by publication date
        sorted_papers = sorted(papers, key=lambda p: p.published, reverse=True)
        return sorted_papers[:max_results]
    
    elif mode == "cited":
        # Sort by citations (highest first)
        sorted_papers = sorted(
            papers,
            key=lambda p: p.citations if p.citations is not None else 0,
            reverse=True
        )
        return sorted_papers[:max_results]
    
    elif mode == "relevant":
        # Sort by title/abstract similarity to query
        scored = []
        for paper in papers:
            # Simple string similarity
            title_sim = SequenceMatcher(None, query.lower(), paper.title.lower()).ratio()
            abstract_sim = SequenceMatcher(None, query.lower(), paper.abstract.lower()).ratio()
            score = 0.7 * title_sim + 0.3 * abstract_sim
            scored.append((score, paper))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:max_results]]
    
    elif mode == "influential":
        # High citations + recency
        scored = []
        current_year = datetime.now().year
        
        for paper in papers:
            # Parse year from published date
            year = int(paper.published[:4])
            recency = max(0, (year - 2000) / (current_year - 2000))
            
            # Citations (log-scaled)
            citations = paper.citations if paper.citations is not None else 0
            cite_score = math.log1p(citations) / 10
            
            # Weighted score: 60% citations, 40% recency
            score = 0.6 * cite_score + 0.4 * recency
            scored.append((score, paper))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:max_results]]
    
    else:  # balanced (default)
        # Mix of relevance, citations, and recency
        scored = []
        current_year = datetime.now().year
        
        for paper in papers:
            # Relevance
            title_sim = SequenceMatcher(None, query.lower(), paper.title.lower()).ratio()
            abstract_sim = SequenceMatcher(None, query.lower(), paper.abstract.lower()).ratio()
            relevance = 0.7 * title_sim + 0.3 * abstract_sim
            
            # Citations (log-scaled)
            citations = paper.citations if paper.citations is not None else 0
            cite_score = math.log1p(citations) / 10
            
            # Recency
            year = int(paper.published[:4])
            recency = max(0, (year - 2000) / (current_year - 2000))
            
            # Weighted score
            score = 0.4 * relevance + 0.35 * cite_score + 0.25 * recency
            scored.append((score, paper))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:max_results]]


# Semantic search (optional - requires sentence-transformers)
def semantic_rank_papers(query: str, papers: List[Paper], max_results: int = 20) -> List[Paper]:
    """
    Rank papers using semantic embeddings.
    Requires: pip install sentence-transformers
    """
    try:
        from sentence_transformers import SentenceTransformer, util
        
        print("⏳ Loading semantic model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        query_emb = model.encode(query, convert_to_tensor=True)
        
        scored = []
        current_year = datetime.now().year
        
        for paper in papers:
            # Encode title + abstract
            text = paper.title + " " + paper.abstract
            doc_emb = model.encode(text, convert_to_tensor=True)
            similarity = float(util.cos_sim(query_emb, doc_emb).item())
            
            # Add citation and recency factors
            citations = paper.citations if paper.citations is not None else 0
            cite_score = math.log1p(citations) / 10
            
            year = int(paper.published[:4])
            recency = max(0, (year - 2000) / (current_year - 2000))
            
            # Weighted score
            score = 0.6 * similarity + 0.25 * cite_score + 0.15 * recency
            scored.append((score, paper))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:max_results]]
        
    except ImportError:
        print("⚠️ sentence-transformers not installed. Falling back to balanced mode.")
        return rank_papers(query, papers, mode="balanced", max_results=max_results)


if __name__ == "__main__":
    # Test the API
    print("🧪 Testing arXiv API...\n")
    
    papers = search_arxiv(
        query="transformer attention mechanism",
        max_results=5,
        sort_by="relevance"
    )
    
    if papers:
        papers = fetch_citations_batch(papers)
        ranked = rank_papers("transformer attention", papers, mode="balanced", max_results=5)
        
        print("\n=== Sample Paper ===")
        p = ranked[0]
        print(f"Title: {p.title}")
        print(f"Authors: {', '.join(p.authors[:3])}")
        print(f"Published: {p.published[:10]}")
        print(f"Citations: {p.citations}")
        print(f"Categories: {', '.join(p.categories)}")
        print(f"URL: {p.arxiv_url}")