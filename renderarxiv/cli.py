#!/usr/bin/env python3
"""
renderarxiv: Search arXiv and render results in Human + LLM views
"""

import argparse
import html
import pathlib
import sys
import tempfile
import webbrowser
from typing import List
from datetime import datetime

from pygments.formatters import HtmlFormatter

from renderarxiv.arxiv_client import (
    search_arxiv,
    rank_papers,
    fetch_citations_batch,
    semantic_rank_papers,
)
from renderarxiv.models import (
    Paper,
    format_results_for_llm,
    format_authors,
    clean_text,
    get_category_name,
)


def build_html(query: str, papers: List[Paper]) -> str:
    """Generate the HTML page with Human + LLM views."""
    formatter = HtmlFormatter(nowrap=False)
    pygments_css = formatter.get_style_defs('.highlight')

    # 👤 Human View
    human_sections: List[str] = []
    for i, p in enumerate(papers, 1):
        title = html.escape(p.title)
        authors_str = html.escape(format_authors(p.authors, max_authors=5))
        abstract = html.escape(clean_text(p.abstract))
        arxiv_url = p.arxiv_url
        pdf_url = p.pdf_url
        published = p.published[:10]  # Just date
        
        # Categories with human-readable names
        category_tags = []
        for cat in p.categories[:3]:  # Show top 3 categories
            cat_name = get_category_name(cat)
            category_tags.append(f'<span class="category-tag" title="{cat}">{html.escape(cat_name)}</span>')
        categories_html = " ".join(category_tags)
        
        # Optional fields
        extras = []
        if p.comment:
            extras.append(f"💬 {html.escape(clean_text(p.comment))}")
        if p.journal_ref:
            extras.append(f"📖 {html.escape(clean_text(p.journal_ref))}")
        if p.doi:
            extras.append(f'🔍 DOI: <a href="https://doi.org/{p.doi}" target="_blank">{html.escape(p.doi)}</a>')
        extras_html = "<br>".join(extras) if extras else ""
        
        paper_html = f"""
        <section class="paper">
          <h2>{i}. {title}</h2>
          <div class="meta">
            <span class="authors">👥 {authors_str}</span>
            <span class="date">📅 {published}</span>
          </div>
          <div class="categories">{categories_html}</div>
          <div class="abstract">{abstract}</div>
          {f'<div class="extras">{extras_html}</div>' if extras_html else ''}
          <div class="links">
            <a href="{arxiv_url}" target="_blank" class="btn">📄 arXiv Page</a>
            <a href="{pdf_url}" target="_blank" class="btn btn-primary">📥 Download PDF</a>
          </div>
        </section>
        """
        human_sections.append(paper_html)

    human_html = "\n".join(human_sections)

    # 🤖 LLM View
    llm_text = format_results_for_llm(papers)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>renderarxiv – {html.escape(query)}</title>
<style>
  * {{
    box-sizing: border-box;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    margin: 0;
    padding: 0;
    line-height: 1.6;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
  }}
  .container {{ 
    max-width: 1100px; 
    margin: 0 auto; 
    padding: 2rem; 
    background: white;
    min-height: 100vh;
    box-shadow: 0 0 50px rgba(0,0,0,0.1);
  }}
  h1 {{ 
    margin-bottom: 0.5rem; 
    color: #2d3748;
    font-size: 2.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .summary {{
    color: #718096;
    margin-bottom: 2rem;
    font-size: 1rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
  }}
  .paper {{ 
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 2rem; 
    margin-bottom: 2rem;
    background: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .paper:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.1);
  }}
  .paper h2 {{ 
    margin: 0 0 1rem 0; 
    font-size: 1.4rem;
    color: #2d3748;
    line-height: 1.4;
  }}
  .meta {{
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    font-size: 0.9rem;
  }}
  .meta span {{
    color: #4a5568;
  }}
  .authors {{
    font-weight: 500;
  }}
  .date {{
    color: #718096;
  }}
  .citations {{
    color: #667eea;
    font-weight: 600;
  }}
  .categories {{
    margin-bottom: 1rem;
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }}
  .category-tag {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: help;
  }}
  .abstract {{
    background: #f7fafc;
    padding: 1.25rem;
    border-radius: 8px;
    font-size: 0.95rem;
    color: #2d3748;
    line-height: 1.7;
    margin-bottom: 1rem;
    border-left: 4px solid #667eea;
  }}
  .extras {{
    font-size: 0.9rem;
    color: #4a5568;
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: #edf2f7;
    border-radius: 6px;
  }}
  .extras a {{
    color: #667eea;
    text-decoration: none;
  }}
  .extras a:hover {{
    text-decoration: underline;
  }}
  .links {{
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }}
  .btn {{
    padding: 0.6rem 1.25rem;
    border: 2px solid #667eea;
    background: white;
    color: #667eea;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    display: inline-block;
  }}
  .btn:hover {{
    background: #667eea;
    color: white;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
  }}
  .btn-primary {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
  }}
  .btn-primary:hover {{
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }}
  .view-toggle {{
    margin: 2rem 0;
    display: flex;
    gap: 0.75rem;
    align-items: center;
    padding-bottom: 1.5rem;
    border-bottom: 2px solid #e2e8f0;
  }}
  .view-toggle strong {{
    color: #2d3748;
    font-size: 1.1rem;
  }}
  .toggle-btn {{
    padding: 0.65rem 1.5rem;
    border: 2px solid #cbd5e0;
    background: white;
    cursor: pointer;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    transition: all 0.2s;
    color: #4a5568;
  }}
  .toggle-btn.active {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: transparent;
    box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
  }}
  .toggle-btn:hover:not(.active) {{
    background: #f7fafc;
    border-color: #667eea;
    color: #667eea;
  }}
  #llm-view {{ display: none; }}
  #llm-text {{
    width: 100%;
    height: 70vh;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
    font-size: 0.9rem;
    border: 2px solid #cbd5e0;
    border-radius: 12px;
    padding: 1.5rem;
    resize: vertical;
    background: #f7fafc;
    color: #2d3748;
    line-height: 1.6;
  }}
  .llm-section {{
    background: white;
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  }}
  .llm-section h2 {{
    margin-top: 0;
    color: #2d3748;
    font-size: 1.8rem;
  }}
  .llm-section p {{
    color: #4a5568;
    margin-bottom: 1.5rem;
  }}
  .copy-hint {{
    margin-top: 1rem;
    padding: 1rem 1.25rem;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border-left: 4px solid #667eea;
    color: #2d3748;
    font-size: 0.95rem;
    border-radius: 8px;
  }}
  .copy-hint strong {{
    color: #667eea;
  }}
  kbd {{
    background: #edf2f7;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    padding: 0.15rem 0.4rem;
    font-family: monospace;
    font-size: 0.85em;
    color: #2d3748;
  }}
  {pygments_css}
</style>
</head>
<body>
<div class="container">

  <h1>🔬 arXiv: {html.escape(query)}</h1>
  <div class="summary">
    <strong>{len(papers)}</strong> papers found
  </div>

  <div class="view-toggle">
    <strong>View:</strong>
    <button class="toggle-btn active" onclick="showHumanView()">👤 Human</button>
    <button class="toggle-btn" onclick="showLLMView()">🤖 LLM</button>
  </div>

  <div id="human-view">
    {human_html}
  </div>

  <div id="llm-view">
    <div class="llm-section">
      <h2>🤖 LLM View – Ready to Copy</h2>
      <p>Copy the text below and paste it into ChatGPT/Claude/etc:</p>
      <textarea id="llm-text" readonly>{html.escape(llm_text)}</textarea>
      <div class="copy-hint">
        💡 <strong>Tip:</strong> Click in the text area, press <kbd>Ctrl+A</kbd> (or <kbd>Cmd+A</kbd> on Mac), then <kbd>Ctrl+C</kbd> (or <kbd>Cmd+C</kbd>) to copy everything.
      </div>
    </div>
  </div>

</div>

<script>
function showHumanView() {{
  document.getElementById('human-view').style.display = 'block';
  document.getElementById('llm-view').style.display = 'none';
  document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
}}

function showLLMView() {{
  document.getElementById('human-view').style.display = 'none';
  document.getElementById('llm-view').style.display = 'block';
  document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  setTimeout(() => {{
    const textArea = document.getElementById('llm-text');
    textArea.focus();
    textArea.select();
  }}, 100);
}}
</script>
</body>
</html>
"""


def derive_temp_output_path(query: str) -> pathlib.Path:
    """Temporary output path derived from query string."""
    safe_query = "".join(c if c.isalnum() else "_" for c in query)
    filename = f"renderarxiv_{safe_query[:30]}.html"
    return pathlib.Path(tempfile.gettempdir()) / filename


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Search arXiv and render results into HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  renderarxiv "transformer attention mechanism"
  renderarxiv "quantum computing" --mode recent --max-results 15
  renderarxiv "deep learning" --category cs.LG --mode relevant
  renderarxiv "neural networks" --mode semantic
        """
    )
    ap.add_argument("query", help="Search query")
    ap.add_argument(
        "--max-results", 
        type=int, 
        default=20, 
        help="Number of papers to return (default: 20)"
    )
    ap.add_argument(
        "--mode",
        choices=["balanced", "recent", "relevant", "semantic"],
        default="balanced",
        help="Ranking mode (default: balanced)"
    )
    ap.add_argument(
        "--category",
        help="Filter by arXiv category (e.g., cs.LG, cs.AI, math.CO)"
    )
    ap.add_argument(
        "--sort-by",
        choices=["relevance", "lastUpdatedDate", "submittedDate"],
        default="relevance",
        help="arXiv API sort criterion (default: relevance)"
    )

    ap.add_argument(
        "-o", "--out", 
        help="Output HTML file path (default: temp file)"
    )
    ap.add_argument(
        "--no-open", 
        action="store_true", 
        help="Don't open HTML in browser after generation"
    )
    args = ap.parse_args()

    if args.out is None:
        args.out = str(derive_temp_output_path(args.query))

    print(f"🔎 Searching arXiv for: {args.query}", file=sys.stderr)
    
    # Search arXiv
    papers = search_arxiv(
        query=args.query,
        max_results=args.max_results * 2,  # Fetch extra for better filtering
        sort_by=args.sort_by,
        category=args.category,
    )
    
    if not papers:
        print("❌ No papers found. Try a different query.", file=sys.stderr)
        return 1

    # Rank and filter
    if args.mode == "semantic":
        ranked = semantic_rank_papers(args.query, papers, max_results=args.max_results)
    else:
        ranked = rank_papers(args.query, papers, mode=args.mode, max_results=args.max_results)
    
    print(f"✓ Filtered to {len(ranked)} papers (mode={args.mode})", file=sys.stderr)

    # Generate HTML
    html_out = build_html(args.query, ranked)

    out_path = pathlib.Path(args.out)
    out_path.write_text(html_out, encoding="utf-8")
    print(f"💾 Wrote {out_path.stat().st_size/1024:.1f} KiB to {out_path}", file=sys.stderr)

    if not args.no_open:
        webbrowser.open(f"file://{out_path.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())