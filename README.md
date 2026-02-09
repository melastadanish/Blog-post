# Blog Content E-E-A-T Improver

A Python CLI tool that analyzes blog posts and generates improved content following Google's E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) standards while maintaining human authenticity.

## What It Does

1. **Scrapes** a blog post from any URL (WordPress, Medium, Ghost, Hugo, custom sites)
2. **Analyzes** the content for E-E-A-T signals, gaps, and AI-generic phrasing
3. **Generates** improved content with human-input markers via the Claude API
4. **Outputs** three files: improved content, analysis report, and implementation guide

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"
```

### Requirements

- Python 3.10+
- Anthropic API key (get one at https://console.anthropic.com)

## Usage

```bash
# Full analysis and improvement
python improve_seo.py https://example.com/blog-post

# Analysis only (no API calls needed)
python improve_seo.py https://example.com/blog-post --dry-run

# Specify output directory
python improve_seo.py https://example.com/blog-post --output-dir ./improved

# Verbose mode with style preservation
python improve_seo.py https://example.com/blog-post --verbose --preserve-style

# Pass API key directly
python improve_seo.py https://example.com/blog-post --api-key sk-ant-...
```

### CLI Options

| Option | Description |
|---|---|
| `url` | Blog post URL to analyze (required) |
| `--api-key` | Anthropic API key (or set `ANTHROPIC_API_KEY` env var) |
| `--output-dir` | Output directory (default: `./eeat_output`) |
| `--dry-run` | Analyze only — no Claude API calls |
| `--verbose` | Detailed progress with timing |
| `--preserve-style` | Match the original author's writing style |
| `--no-cache` | Re-fetch URL instead of using cache |

## Output Files

### `improved_content.md`
The rewritten blog post with:
- Quick Answer / TL;DR section at the top
- `[MANUAL INPUT NEEDED: ...]` markers where human input is critical
- `<!-- SUGGESTION: ... -->` comments with recommendations
- Question-format headings for featured snippets
- FAQ section with schema-ready answers
- Structured data (JSON-LD) for Article and FAQ schemas

### `eeat_report.txt`
Analysis report showing:
- Current vs. projected E-E-A-T scores (1-10 scale)
- Scores per dimension (Experience, Expertise, Authoritativeness, Trust)
- Strengths and gaps identified
- AI-generic phrases detected with rewrite suggestions
- Outdated statistics flagged
- Manual action checklist
- Automated improvement checklist

### `implementation_guide.txt`
Step-by-step instructions:
1. How and where to add personal experiences
2. Expertise questions to answer in the content
3. Where to find citations and statistics (with source recommendations)
4. Trust signals to implement
5. Technical SEO additions (schema markup, meta tags, heading optimization)

## Architecture

```
improve_seo.py    — CLI entry point and orchestration
scraper.py        — Content extraction from URLs
analyzer.py       — E-E-A-T scoring and gap detection
improver.py       — Claude API integration for content improvement
formatter.py      — Output file generation
```

### How the Analysis Works

The analyzer checks for signals in four dimensions:

- **Experience**: First-person narratives, case studies, hands-on testing language
- **Expertise**: Data citations, research references, concrete examples, methodology
- **Authoritativeness**: External links, expert quotes, credentials, citations
- **Trust**: Publication dates, author attribution, disclosures, fact-checking language

It also detects 25+ AI-generic phrases (e.g., "in today's digital world", "game-changer", "delve into") and flags statistics that may be outdated.

### How Improvements Are Generated

The improver makes 5 focused Claude API calls:

1. **Experience & expertise suggestions** — where to add personal stories and data
2. **FAQ & trust signals** — questions to cover, trust recommendations
3. **Phrase rewrites & headings** — fix generic language, optimize heading structure
4. **Full improved markdown** — complete rewrite with markers and comments
5. **Schema markup** — Article and FAQ JSON-LD structured data

## Caching

Scraped content is cached in `~/.cache/blog_eeat_improver/` so you can re-run the tool without re-fetching. Use `--no-cache` to force a fresh fetch.

## Example

See the `examples/` directory for sample output files demonstrating the format for each output type.

```bash
# Run the dry-run analysis on a URL
python improve_seo.py https://example.com/my-blog-post --dry-run

# Output:
#   → Fetching blog content...
#   ✓ Extracted content (1,500 words)
#   ✓ Analyzed E-E-A-T (Current score: 4/10)
#   ✓ Identified 7 improvement opportunities
#
#   DRY-RUN ANALYSIS SUMMARY
#   ...
```
