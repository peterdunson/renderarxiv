# 🔬 renderarxiv

**renderarxiv** lets you search arXiv from the terminal and render results into a beautiful HTML page with two views:

- 👤 **Human View** — elegantly formatted papers with titles, authors, abstracts, categories, citations, and direct PDF download links
- 🤖 **LLM View** — plain-text block you can copy-paste into ChatGPT/Claude/etc.

No more hallucinated research papers from LLMs — everything comes straight from arXiv and Semantic Scholar APIs.

Inspired by [Andrej Karpathy's `rendergit`](https://github.com/karpathy/rendergit), [`renderscholar`](https://github.com/peterdunson/renderscholar), and [`renderstack`](https://github.com/yourusername/renderstack).

---

## ✨ Why renderarxiv?

**The problem:** When you ask ChatGPT/Claude about recent ML research, they often make up paper titles, authors, or cite non-existent arXiv IDs.

**The solution:** Search real arXiv preprints, get citation counts from Semantic Scholar, then feed the clean results to your AI assistant. Get accurate, up-to-date research summaries with proper citations.

---

## 🔧 Installation

You'll need **Python 3.10+**. Then install directly from GitHub:

```bash
pip install git+https://github.com/yourusername/renderarxiv.git
```

**Or clone and install locally:**

```bash
git clone https://github.com/yourusername/renderarxiv.git
cd renderarxiv
pip install -e .
```

### Optional: Semantic mode

For transformer-based semantic similarity ranking:

```bash
pip install "git+https://github.com/yourusername/renderarxiv.git#egg=renderarxiv[semantic]"
```

---

## 🚀 Usage

### Basic search

Search arXiv from the terminal:

```bash
renderarxiv "transformer attention mechanism"
```

This will:
1. Search arXiv API for relevant papers
2. Optionally fetch citation counts from Semantic Scholar
3. Rank and filter results
4. Generate a beautiful HTML file
5. Auto-open it in your browser

### Options

**Control results:**
```bash
renderarxiv "quantum computing" --max-results 15
```
- `--max-results N` — Number of papers to return (default: 20)

**Ranking modes:**
```bash
renderarxiv "deep learning optimization" --mode recent
```

Available modes:
- **balanced** → Mix of relevance, citations, and recency (default)
- **recent** → Newest papers first
- **cited** → Most cited papers first
- **influential** → High citations + recent (trending research)
- **relevant** → Pure text similarity to query
- **semantic** → Transformer embeddings for semantic similarity (requires optional install)

**Filter by category:**
```bash
renderarxiv "neural networks" --category cs.LG
```

Common categories:
- `cs.LG` — Machine Learning
- `cs.AI` — Artificial Intelligence
- `cs.CV` — Computer Vision
- `cs.CL` — Computation and Language (NLP)
- `cs.RO` — Robotics
- `stat.ML` — Statistics (Machine Learning)
- `math.OC` — Optimization and Control
- `quant-ph` — Quantum Physics

See full list: https://arxiv.org/category_taxonomy

**Fetch citations:**
```bash
renderarxiv "generative models" --fetch-citations
```
- Retrieves citation counts from Semantic Scholar
- Automatically enabled for `cited`, `influential`, and `balanced` modes
- Optional for other modes (faster without)

**Output control:**
```bash
renderarxiv "reinforcement learning" -o mypapers.html --no-open
```
- `-o FILE` — Save to specific file (default: temp file)
- `--no-open` — Don't auto-open in browser

### Full example

```bash
renderarxiv "large language models reasoning" \
  --category cs.CL \
  --mode influential \
  --max-results 15 \
  --fetch-citations
```

This will:
- Search for papers about LLM reasoning
- Filter to Computer Science - Computation and Language category
- Fetch citation counts
- Rank by influence (citations + recency)
- Return top 15 papers

---

## 📊 Modes Explained

Each mode changes how papers are ranked:

| Mode | Weights | Best For |
|------|---------|----------|
| `balanced` | 40% relevance, 35% citations, 25% recency | General research (default) |
| `recent` | 100% publication date | Latest developments, new techniques |
| `cited` | 100% citation count | Foundational papers, classics |
| `influential` | 60% citations, 40% recency | Trending impactful work |
| `relevant` | 70% title match, 30% abstract match | Finding papers on exact topic |
| `semantic` | 60% embedding similarity, 25% citations, 15% recency | Deep semantic understanding |

---

## 📂 Output

The HTML output includes two views:

### 👤 Human View
- Beautiful gradient design (purple/blue theme)
- Paper cards with hover effects
- Shows: title, authors, publication date, citation count
- Category tags with human-readable names
- Full abstract in highlighted box
- Optional metadata: journal reference, DOI, comments
- Direct links to arXiv page and PDF download

### 🤖 LLM View
- Plain text in a `<textarea>` for easy copying
- Formatted for maximum AI comprehension:
  - Clear separators between papers
  - Emoji markers (📄 👥 📅 🏷️ 🔗 📥 📊 📝)
  - All metadata included
  - Full abstracts preserved
- Ready to paste into ChatGPT, Claude, or any AI assistant

---

## 🎓 arXiv Categories

**Computer Science:**
- `cs.AI` — Artificial Intelligence
- `cs.CL` — Computation and Language (NLP)
- `cs.CV` — Computer Vision
- `cs.LG` — Machine Learning
- `cs.RO` — Robotics
- `cs.CR` — Cryptography and Security
- `cs.DB` — Databases
- `cs.DS` — Data Structures and Algorithms
- `cs.SE` — Software Engineering

**Statistics:**
- `stat.ML` — Machine Learning
- `stat.TH` — Statistics Theory

**Mathematics:**
- `math.OC` — Optimization and Control
- `math.ST` — Statistics Theory

**Physics:**
- `quant-ph` — Quantum Physics
- `physics.comp-ph` — Computational Physics

Full taxonomy: https://arxiv.org/category_taxonomy

---

## 💡 Pro Tips

**Literature review workflow:**
```bash
# 1. Find recent influential papers
renderarxiv "multimodal learning" --mode influential --max-results 20

# 2. Switch to LLM view in browser
# 3. Copy the text
# 4. Paste into Claude: "Summarize these papers and identify key trends"
```

**Finding foundational papers:**
```bash
renderarxiv "attention is all you need" --mode cited --max-results 10
```

**Tracking latest research:**
```bash
renderarxiv "diffusion models" --mode recent --category cs.CV --max-results 15
```

**Semantic deep-dive:**
```bash
renderarxiv "few-shot learning meta-learning" --mode semantic --fetch-citations
```

**Category exploration:**
```bash
# Find what's hot in NLP
renderarxiv "language models" --category cs.CL --mode influential

# Quantum computing breakthroughs
renderarxiv "quantum algorithms" --category quant-ph --mode recent
```

---

## 🔗 APIs Used

**arXiv API** (free, no key required)
- Official arXiv search API
- Returns metadata in Atom/XML format
- Rate limit: ~1 request per 3 seconds (built-in throttling)
- Docs: https://arxiv.org/help/api

**Semantic Scholar API** (free, no key required)
- Provides citation counts for papers
- Rate limit: ~100 requests/second
- Docs: https://api.semanticscholar.org/

Both APIs are free and require no authentication. Citation fetching adds ~1-2 seconds per batch of papers.

---

## 🛠️ Development

**Clone the repo:**
```bash
git clone https://github.com/yourusername/renderarxiv.git
cd renderarxiv
```

**Install in editable mode:**
```bash
pip install -e .
```

**Run tests:**
```bash
python -m renderarxiv.arxiv_client  # Test API client
python -m renderarxiv.cli "test query"  # Test full workflow
```

**Project structure:**
```
renderarxiv/
├── renderarxiv/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface + HTML generation
│   ├── models.py           # Data models (Paper)
│   └── arxiv_client.py     # arXiv + Semantic Scholar API clients
├── .gitignore
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## 🤝 Contributing

Contributions welcome! Ideas for new features:

- [ ] PDF download and local storage
- [ ] Export to BibTeX format
- [ ] Author/institution filtering
- [ ] Date range queries
- [ ] Save/load favorite searches
- [ ] Integration with Zotero/Mendeley
- [ ] Paper similarity recommendations
- [ ] Track papers over time (watch for updates)

---

## 📝 Notes

- Uses official arXiv API (no web scraping!)
- Citation counts from Semantic Scholar API
- Works offline after initial fetch (HTML is self-contained)
- Category tags show human-readable names with tooltips
- Handles edge cases (no citations, missing metadata, etc.)
- Respects API rate limits with built-in throttling

---

## 🆚 Comparison with renderscholar

| Feature | renderarxiv | renderscholar |
|---------|-------------|---------------|
| Source | arXiv preprints | Google Scholar (all papers) |
| Coverage | CS/Physics/Math focus | All academic fields |
| API | Official arXiv API | Web scraping (no API) |
| Speed | Fast (~2 seconds) | Slower (browser automation) |
| Citations | Semantic Scholar API | Scraped from Google Scholar |
| Best For | Recent ML/AI research | Published papers, established work |

**Use both!** arXiv for cutting-edge preprints, Scholar for peer-reviewed publications.

---

## 📄 License

MIT © 2025 Your Name

---

## 🙏 Credits

- Inspired by [rendergit](https://github.com/karpathy/rendergit) by Andrej Karpathy
- Built on the [arXiv API](https://arxiv.org/help/api)
- Citations from [Semantic Scholar](https://www.semanticscholar.org/)
- Related projects: [renderscholar](https://github.com/peterdunson/renderscholar), [renderstack](https://github.com/yourusername/renderstack)

---

## 🔥 Examples

**Machine Learning:**
```bash
renderarxiv "large language models" --category cs.LG --mode influential
renderarxiv "transformer architecture" --mode cited
renderarxiv "reinforcement learning from human feedback" --mode recent
```

**Computer Vision:**
```bash
renderarxiv "diffusion models" --category cs.CV --mode recent
renderarxiv "object detection" --mode cited --max-results 25
```

**NLP:**
```bash
renderarxiv "prompt engineering" --category cs.CL --mode recent
renderarxiv "question answering" --mode semantic
```

**Quantum Computing:**
```bash
renderarxiv "quantum error correction" --category quant-ph --mode influential
```

---

## 📧 Support

Found a bug? Have a feature request?

- Open an issue: https://github.com/yourusername/renderarxiv/issues
- arXiv API docs: https://arxiv.org/help/api
- Semantic Scholar API: https://api.semanticscholar.org/