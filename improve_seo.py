#!/usr/bin/env python3
"""
Blog Content E-E-A-T Improver — CLI Tool

Analyzes a blog post URL and generates improved content following Google's
E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) standards
while maintaining human authenticity.

Usage:
    python improve_seo.py <blog_url> [options]

Examples:
    python improve_seo.py https://example.com/my-post --output-dir ./improved
    python improve_seo.py https://example.com/my-post --dry-run --verbose
    python improve_seo.py https://example.com/my-post --preserve-style
"""

import argparse
import json
import logging
import os
import sys
import textwrap
import time

from analyzer import EEATReport, analyze_eeat
from formatter import write_all_outputs, write_eeat_report
from improver import ImprovementResult, generate_improvements
from scraper import BlogContent, ScrapingError, scrape_blog

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(message)s"


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stderr)


# ---------------------------------------------------------------------------
# Progress display
# ---------------------------------------------------------------------------

class ProgressPrinter:
    """Simple progress indicator for CLI output."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._start = time.monotonic()

    def step(self, message: str, done: bool = False) -> None:
        mark = "\u2713" if done else "\u2192"
        elapsed = time.monotonic() - self._start
        if self.verbose:
            print(f"  {mark} {message} ({elapsed:.1f}s)", file=sys.stderr)
        else:
            print(f"  {mark} {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        print(f"  \u2717 {message}", file=sys.stderr)

    def blank(self) -> None:
        print(file=sys.stderr)


# ---------------------------------------------------------------------------
# Cache helpers — store scraped content so runs can be resumed
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "blog_eeat_improver")


def _cache_path(url: str) -> str:
    """Return a filesystem-safe cache path for a URL."""
    import hashlib
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{url_hash}.json")


def _save_cache(content: BlogContent) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    data = {
        "url": content.url,
        "title": content.title,
        "body_text": content.body_text,
        "body_html": content.body_html,
        "headings": content.headings,
        "meta_description": content.meta_description,
        "author": content.author,
        "publish_date": content.publish_date,
        "word_count": content.word_count,
        "images": content.images,
        "links": content.links,
        "platform": content.platform,
    }
    with open(_cache_path(content.url), "w", encoding="utf-8") as f:
        json.dump(data, f)


def _load_cache(url: str) -> BlogContent | None:
    path = _cache_path(url)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BlogContent(
            url=data["url"],
            title=data["title"],
            body_text=data["body_text"],
            body_html=data["body_html"],
            headings=data["headings"],
            meta_description=data["meta_description"],
            author=data["author"],
            publish_date=data["publish_date"],
            word_count=data["word_count"],
            images=data["images"],
            links=data["links"],
            raw_html="",
            platform=data["platform"],
        )
    except (json.JSONDecodeError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Dry-run output
# ---------------------------------------------------------------------------

def _print_dry_run(content: BlogContent, report: EEATReport, output_dir: str) -> None:
    """Print analysis-only output without calling the Claude API."""
    # Write just the report
    dummy_result = ImprovementResult()
    os.makedirs(output_dir, exist_ok=True)
    path = write_eeat_report(report, content, dummy_result, output_dir)

    # Also print a summary to stdout
    print()
    print("=" * 60)
    print("  DRY-RUN ANALYSIS SUMMARY")
    print("=" * 60)
    print()
    print(f"  URL:    {content.url}")
    print(f"  Title:  {content.title}")
    print(f"  Words:  {content.word_count}")
    print(f"  Platform: {content.platform}")
    print()
    print(f"  E-E-A-T Score: {report.overall_score}/10")
    print(f"    Experience:        {report.experience.score}/10")
    print(f"    Expertise:         {report.expertise.score}/10")
    print(f"    Authoritativeness: {report.authoritativeness.score}/10")
    print(f"    Trust:             {report.trust.score}/10")
    print()

    if report.strengths:
        print("  Strengths:")
        for s in report.strengths:
            print(f"    + {s}")
        print()

    if report.missing_elements:
        print("  Missing elements:")
        for m in report.missing_elements:
            print(f"    - {m}")
        print()

    if report.ai_phrases_found:
        print(f"  AI-generic phrases found ({len(report.ai_phrases_found)}):")
        for p in report.ai_phrases_found[:5]:
            print(f'    ! "{p}"')
        if len(report.ai_phrases_found) > 5:
            print(f"    ... and {len(report.ai_phrases_found) - 5} more")
        print()

    if report.outdated_stats:
        print(f"  Potentially outdated info ({len(report.outdated_stats)}):")
        for s in report.outdated_stats[:3]:
            print(f"    ? {s}")
        print()

    print(f"  Projected score after improvements: {report.projected_score}/10")
    print()
    print(f"  Full report saved to: {path}")
    print()
    print("  Run without --dry-run to generate improved content.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="improve_seo",
        description=(
            "Analyze and improve blog content for Google E-E-A-T standards. "
            "Generates improved content with human-input markers, an analysis "
            "report, and a step-by-step implementation guide."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s https://example.com/post --output-dir ./improved
              %(prog)s https://example.com/post --dry-run --verbose
              %(prog)s https://example.com/post --preserve-style --api-key sk-...
        """),
    )

    parser.add_argument(
        "url",
        help="URL of the blog post to analyze and improve",
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save output files (default: ./eeat_output)",
        default="./eeat_output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only analyze the content — skip improvement generation (no API calls)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress and timing information",
    )
    parser.add_argument(
        "--preserve-style",
        action="store_true",
        help="Instruct the AI to match the original author's writing style",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cached content and re-fetch the URL",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    progress = ProgressPrinter(verbose=args.verbose)

    print(file=sys.stderr)
    print("  Blog E-E-A-T Content Improver", file=sys.stderr)
    print("  " + "=" * 40, file=sys.stderr)
    print(file=sys.stderr)

    # ---- Step 1: Fetch / cache content ----
    content: BlogContent | None = None
    if not args.no_cache:
        content = _load_cache(args.url)
        if content:
            progress.step(f"Loaded cached content ({content.word_count} words)", done=True)

    if content is None:
        try:
            progress.step("Fetching blog content...")
            content = scrape_blog(args.url, verbose=args.verbose)
            _save_cache(content)
            progress.step(f"Extracted content ({content.word_count} words)", done=True)
        except ScrapingError as e:
            progress.error(f"Scraping failed: {e}")
            return 1

    if content.word_count == 0:
        progress.error("No content could be extracted from the URL.")
        return 1

    # ---- Step 2: Analyze E-E-A-T ----
    progress.step("Analyzing E-E-A-T signals...")
    report = analyze_eeat(content)
    progress.step(f"Analyzed E-E-A-T (Current score: {report.overall_score}/10)", done=True)

    improvement_count = sum(
        len(d.gaps)
        for d in [report.experience, report.expertise, report.authoritativeness, report.trust]
    )
    progress.step(f"Identified {improvement_count} improvement opportunities", done=True)

    # ---- Dry-run: print analysis and exit ----
    if args.dry_run:
        _print_dry_run(content, report, args.output_dir)
        return 0

    # ---- Step 3: Check API key ----
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        progress.error(
            "Anthropic API key required for content improvement.\n"
            "  Set ANTHROPIC_API_KEY env var or pass --api-key.\n"
            "  Use --dry-run to see analysis without an API key."
        )
        return 1

    # ---- Step 4: Generate improvements ----
    progress.step("Generating improvements via Claude API...")
    try:
        result = generate_improvements(
            content,
            report,
            api_key=api_key,
            preserve_style=args.preserve_style,
            verbose=args.verbose,
        )
    except RuntimeError as e:
        progress.error(str(e))
        return 1

    manual_markers = result.improved_markdown.count("[MANUAL INPUT NEEDED")
    progress.step(
        f"Generated improved content with {manual_markers} manual input markers",
        done=True,
    )

    # ---- Step 5: Write output files ----
    progress.step("Writing output files...")
    paths = write_all_outputs(content, report, result, args.output_dir)
    for p in paths:
        progress.step(f"Wrote {os.path.basename(p)}", done=True)

    # ---- Done ----
    progress.blank()
    print(f"  Files saved to {args.output_dir}/", file=sys.stderr)
    progress.blank()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
