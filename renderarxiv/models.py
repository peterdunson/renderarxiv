from pydantic import BaseModel
from typing import Optional, List
import re


class Paper(BaseModel):
    """Represents an arXiv paper."""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    arxiv_url: str
    published: str  # ISO format date string
    updated: str  # ISO format date string
    categories: List[str]  # e.g., ['cs.LG', 'cs.AI']
    primary_category: str  # e.g., 'cs.LG'
    comment: Optional[str] = None  # e.g., "10 pages, 3 figures"
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    citations: Optional[int] = None  # From Semantic Scholar if available


def clean_text(text: str) -> str:
    """Clean text by removing excessive whitespace and newlines."""
    if not text:
        return ""
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def format_authors(authors: List[str], max_authors: int = 5) -> str:
    """Format author list with 'et al.' if too many."""
    if len(authors) <= max_authors:
        return ", ".join(authors)
    else:
        return ", ".join(authors[:max_authors]) + ", et al."


def format_paper_for_llm(paper: Paper) -> str:
    """
    Format a single paper for LLM consumption.
    """
    output = []
    
    # Header
    output.append(f"📄 {clean_text(paper.title)}")
    output.append(f"👥 Authors: {format_authors(paper.authors)}")
    output.append(f"📅 Published: {paper.published[:10]}")  # Just the date part
    output.append(f"🏷️ Categories: {', '.join(paper.categories)}")
    output.append(f"🔗 arXiv: {paper.arxiv_url}")
    output.append(f"📥 PDF: {paper.pdf_url}")
    
    if paper.citations is not None:
        output.append(f"📊 Citations: {paper.citations}")
    
    if paper.comment:
        output.append(f"💬 Note: {clean_text(paper.comment)}")
    
    if paper.journal_ref:
        output.append(f"📖 Journal: {clean_text(paper.journal_ref)}")
    
    if paper.doi:
        output.append(f"🔍 DOI: {paper.doi}")
    
    # Abstract
    output.append(f"\n📝 Abstract:")
    output.append(clean_text(paper.abstract))
    
    return "\n".join(output)


def format_results_for_llm(papers: List[Paper]) -> str:
    """
    Convert a list of papers into a clean, LLM-friendly string.
    """
    formatted_papers = []
    
    for i, paper in enumerate(papers, 1):
        formatted = f"\n{'#'*80}\n# PAPER {i}\n{'#'*80}\n\n"
        formatted += format_paper_for_llm(paper)
        formatted_papers.append(formatted)
    
    return "\n\n".join(formatted_papers)


def get_category_name(category_code: str) -> str:
    """
    Convert arXiv category code to human-readable name.
    """
    # Major categories
    category_map = {
        # Computer Science
        "cs.AI": "Artificial Intelligence",
        "cs.AR": "Hardware Architecture",
        "cs.CC": "Computational Complexity",
        "cs.CE": "Computational Engineering",
        "cs.CG": "Computational Geometry",
        "cs.CL": "Computation and Language",
        "cs.CR": "Cryptography and Security",
        "cs.CV": "Computer Vision",
        "cs.CY": "Computers and Society",
        "cs.DB": "Databases",
        "cs.DC": "Distributed Computing",
        "cs.DL": "Digital Libraries",
        "cs.DM": "Discrete Mathematics",
        "cs.DS": "Data Structures and Algorithms",
        "cs.ET": "Emerging Technologies",
        "cs.FL": "Formal Languages",
        "cs.GL": "General Literature",
        "cs.GR": "Graphics",
        "cs.GT": "Computer Science and Game Theory",
        "cs.HC": "Human-Computer Interaction",
        "cs.IR": "Information Retrieval",
        "cs.IT": "Information Theory",
        "cs.LG": "Machine Learning",
        "cs.LO": "Logic in Computer Science",
        "cs.MA": "Multiagent Systems",
        "cs.MM": "Multimedia",
        "cs.MS": "Mathematical Software",
        "cs.NA": "Numerical Analysis",
        "cs.NE": "Neural and Evolutionary Computing",
        "cs.NI": "Networking and Internet Architecture",
        "cs.OH": "Other Computer Science",
        "cs.OS": "Operating Systems",
        "cs.PF": "Performance",
        "cs.PL": "Programming Languages",
        "cs.RO": "Robotics",
        "cs.SC": "Symbolic Computation",
        "cs.SD": "Sound",
        "cs.SE": "Software Engineering",
        "cs.SI": "Social and Information Networks",
        "cs.SY": "Systems and Control",
        # Math
        "math.AG": "Algebraic Geometry",
        "math.AT": "Algebraic Topology",
        "math.AP": "Analysis of PDEs",
        "math.CT": "Category Theory",
        "math.CA": "Classical Analysis and ODEs",
        "math.CO": "Combinatorics",
        "math.AC": "Commutative Algebra",
        "math.CV": "Complex Variables",
        "math.DG": "Differential Geometry",
        "math.DS": "Dynamical Systems",
        "math.FA": "Functional Analysis",
        "math.GM": "General Mathematics",
        "math.GN": "General Topology",
        "math.GT": "Geometric Topology",
        "math.GR": "Group Theory",
        "math.HO": "History and Overview",
        "math.IT": "Information Theory",
        "math.KT": "K-Theory and Homology",
        "math.LO": "Logic",
        "math.MP": "Mathematical Physics",
        "math.MG": "Metric Geometry",
        "math.NT": "Number Theory",
        "math.NA": "Numerical Analysis",
        "math.OA": "Operator Algebras",
        "math.OC": "Optimization and Control",
        "math.PR": "Probability",
        "math.QA": "Quantum Algebra",
        "math.RT": "Representation Theory",
        "math.RA": "Rings and Algebras",
        "math.SP": "Spectral Theory",
        "math.ST": "Statistics Theory",
        "math.SG": "Symplectic Geometry",
        # Physics
        "physics.acc-ph": "Accelerator Physics",
        "physics.ao-ph": "Atmospheric and Oceanic Physics",
        "physics.app-ph": "Applied Physics",
        "physics.atm-clus": "Atomic and Molecular Clusters",
        "physics.atom-ph": "Atomic Physics",
        "physics.bio-ph": "Biological Physics",
        "physics.chem-ph": "Chemical Physics",
        "physics.class-ph": "Classical Physics",
        "physics.comp-ph": "Computational Physics",
        "physics.data-an": "Data Analysis",
        "physics.flu-dyn": "Fluid Dynamics",
        "physics.gen-ph": "General Physics",
        "physics.geo-ph": "Geophysics",
        "physics.hist-ph": "History and Philosophy of Physics",
        "physics.ins-det": "Instrumentation and Detectors",
        "physics.med-ph": "Medical Physics",
        "physics.optics": "Optics",
        "physics.ed-ph": "Physics Education",
        "physics.soc-ph": "Physics and Society",
        "physics.plasm-ph": "Plasma Physics",
        "physics.pop-ph": "Popular Physics",
        "physics.space-ph": "Space Physics",
        # Quantum Physics
        "quant-ph": "Quantum Physics",
        # Statistics
        "stat.AP": "Applications",
        "stat.CO": "Computation",
        "stat.ML": "Machine Learning",
        "stat.ME": "Methodology",
        "stat.OT": "Other Statistics",
        "stat.TH": "Statistics Theory",
        # Electrical Engineering
        "eess.AS": "Audio and Speech Processing",
        "eess.IV": "Image and Video Processing",
        "eess.SP": "Signal Processing",
        "eess.SY": "Systems and Control",
        # Economics
        "econ.EM": "Econometrics",
        "econ.GN": "General Economics",
        "econ.TH": "Theoretical Economics",
    }
    
    return category_map.get(category_code, category_code)