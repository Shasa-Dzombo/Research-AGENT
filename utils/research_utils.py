import requests
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any, Optional
import time

# -----------------------
# Global model cache to avoid reloading
# -----------------------
_model_cache = None

def load_model():
    global _model_cache
    if _model_cache is None:
        print("Loading SentenceTransformer model (one-time setup)...")
        _model_cache = SentenceTransformer("all-MiniLM-L6-v2")
    return _model_cache

# -----------------------
# Fetch from CrossRef
# -----------------------
def fetch_crossref(query: str, rows: int = 5) -> List[Dict[str, Any]]:
    """Fetch papers from CrossRef API"""
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": rows}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return []

        data = response.json()
        results = []
        for item in data.get("message", {}).get("items", []):
            results.append({
                "source": "CrossRef",
                "title": item.get("title", [""])[0],
                "abstract": item.get("abstract", ""),
                "authors": [f"{a.get('given', '')} {a.get('family', '')}" for a in item.get("author", [])] if "author" in item else [],
                "year": item.get("issued", {}).get("date-parts", [[None]])[0][0],
                "citations": item.get("is-referenced-by-count", 0),
                "venue": item.get("container-title", [""])[0],
                "url": item.get("URL", "")
            })
        return results
    except Exception as e:
        print(f"CrossRef API error: {str(e)}")
        return []

# -----------------------
# Fetch from Semantic Scholar
# -----------------------
def fetch_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch papers from Semantic Scholar API"""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,citationCount,url,venue"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return []

        data = response.json()
        results = []
        for paper in data.get("data", []):
            results.append({
                "source": "Semantic Scholar",
                "title": paper.get("title", ""),
                "abstract": paper.get("abstract", ""),
                "authors": [a.get("name") for a in paper.get("authors", [])],
                "year": paper.get("year"),
                "citations": paper.get("citationCount", 0),
                "venue": paper.get("venue"),
                "url": paper.get("url", "")
            })
        return results
    except Exception as e:
        print(f"Semantic Scholar API error: {str(e)}")
        return []

# -----------------------
# Merge and rank results
# -----------------------
def merge_results(*sources) -> List[Dict[str, Any]]:
    """Merge results from multiple sources"""
    combined = []
    for src in sources:
        combined.extend(src)
    return combined

def rank_by_relevance(query: str, papers: List[Dict[str, Any]], model=None) -> List[Dict[str, Any]]:
    """Rank papers by relevance with hierarchical confidence scoring"""
    if not papers:
        return []
        
    if model is None:
        model = load_model()
        
    try:
        query_emb = model.encode(query, convert_to_tensor=True)
        
        for paper in papers:
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            text = f"{title} {abstract}"
            
            # Avoid encoding empty texts
            if not text.strip():
                paper["relevance"] = 0
                paper["confidence_tier"] = "low"
                continue
                
            paper_emb = model.encode(text, convert_to_tensor=True)
            semantic_similarity = util.cos_sim(query_emb, paper_emb).item()
            
            # Enhanced weighted scoring with stronger hierarchy
            recency_factor = 1.0
            if paper["year"]:
                try:
                    years_old = max(1, 2025 - int(paper["year"]))
                    # More aggressive recency weighting for better hierarchy
                    recency_factor = min(2.0, 1 + (5 / years_old))
                except (ValueError, TypeError):
                    pass
            
            # Enhanced citation factor with logarithmic scaling
            citation_count = paper.get("citations", 0) or 0
            citation_factor = 1 + (0.1 * (citation_count ** 0.3)) if citation_count > 0 else 1
            
            # Calculate final relevance score
            final_score = semantic_similarity * recency_factor * citation_factor
            paper["relevance"] = final_score
            
            # Assign confidence tiers based on score thresholds for clear hierarchy
            if final_score >= 0.8:
                paper["confidence_tier"] = "highest"
                paper["hierarchy_rank"] = 1
            elif final_score >= 0.6:
                paper["confidence_tier"] = "high"
                paper["hierarchy_rank"] = 2
            elif final_score >= 0.4:
                paper["confidence_tier"] = "medium"
                paper["hierarchy_rank"] = 3
            elif final_score >= 0.2:
                paper["confidence_tier"] = "low"
                paper["hierarchy_rank"] = 4
            else:
                paper["confidence_tier"] = "very_low"
                paper["hierarchy_rank"] = 5
        
        # Sort by relevance score (highest first) for clear hierarchy
        papers.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        # Add position indicators for the hierarchy
        for i, paper in enumerate(papers):
            paper["position"] = i + 1
            if i == 0:
                paper["is_primary"] = True
                paper["tier_label"] = "Primary Reference (Highest Confidence)"
            elif i < 3:
                paper["is_primary"] = False
                paper["tier_label"] = f"Secondary Reference #{i} (High Confidence)"
            else:
                paper["is_primary"] = False
                paper["tier_label"] = f"Supporting Reference #{i} (Supporting Evidence)"
        
        # Log the hierarchy for debugging
        if papers:
            print(f"Literature Hierarchy - Primary: {papers[0].get('title', 'Unknown')[:50]}... (Score: {papers[0].get('relevance', 0):.3f})")
            if len(papers) > 1:
                print(f"Secondary references: {len(papers)-1} papers with scores {papers[1].get('relevance', 0):.3f} to {papers[-1].get('relevance', 0):.3f}")
        
        return papers
    except Exception as e:
        print(f"Error ranking papers: {str(e)}")
        return papers

def search_literature(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search and rank papers from multiple academic sources with relevance scoring"""
    
    print(f"Searching literature for: '{query[:50]}...' (limit: {limit})")
    start_time = time.time()
    
    # Fetch from both academic sources for comprehensive results
    ss_results = fetch_semantic_scholar(query, limit=limit)
    cr_results = fetch_crossref(query, rows=limit)
    
    # Combine results from both sources
    combined = merge_results(ss_results, cr_results)
    print(f"Got {len(ss_results)} from Semantic Scholar + {len(cr_results)} from CrossRef")
    
    if not combined:
        print("No literature found for this query")
        return []
    
    # Load model and rank by relevance for best quality results
    model = load_model()
    ranked = rank_by_relevance(query, combined, model)
    
    # Return top results
    result = ranked[:limit]
    
    end_time = time.time()
    print(f"Literature search completed in {end_time - start_time:.2f} seconds")
    print(f"Returning {len(result)} relevant papers")
    
    return result

def search_literature_with_ranking(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Slower but higher quality search with relevance ranking"""
    model = load_model()
    
    ss_results = fetch_semantic_scholar(query, limit=limit)
    cr_results = fetch_crossref(query, rows=limit)
    
    combined = merge_results(ss_results, cr_results)
    ranked = rank_by_relevance(query, combined, model)
    
    return ranked[:limit]
