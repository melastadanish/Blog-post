"""
Output formatter module.
Generates the three output files: improved_content.md, eeat_report.txt,
and implementation_guide.txt.
"""

import json
import os
import textwrap
from datetime import datetime, timezone

from analyzer import EEATReport
from improver import ImprovementResult
from scraper import BlogContent


def _bar(score: float, width: int = 20) -> str:
    """Render a text-based progress bar."""
    filled = round(score / 10 * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {score}/10"


def _wrap(text: str, indent: str = "  ", width: int = 78) -> str:
    """Wrap text with hanging indent."""
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def write_improved_content(
    result: ImprovementResult,
    content: BlogContent,
    output_dir: str,
) -> str:
    """Write improved_content.md and return the file path."""
    path = os.path.join(output_dir, "improved_content.md")

    lines = []
    lines.append(f"<!-- Improved version of: {content.url} -->")
    lines.append(f"<!-- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} -->")
    lines.append(f"<!-- Original word count: {content.word_count} -->")
    lines.append("")
    lines.append(result.improved_markdown)

    # Append schema markup as a reference section
    if result.schema_suggestions:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("<!-- STRUCTURED DATA — Add to your page's <head> section -->")
        lines.append("")
        if "article_schema" in result.schema_suggestions:
            lines.append("<!-- Article Schema -->")
            lines.append("```html")
            lines.append('<script type="application/ld+json">')
            lines.append(json.dumps(result.schema_suggestions["article_schema"], indent=2))
            lines.append("</script>")
            lines.append("```")
            lines.append("")
        if "faq_schema" in result.schema_suggestions:
            lines.append("<!-- FAQ Schema -->")
            lines.append("```html")
            lines.append('<script type="application/ld+json">')
            lines.append(json.dumps(result.schema_suggestions["faq_schema"], indent=2))
            lines.append("</script>")
            lines.append("```")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


def write_eeat_report(
    report: EEATReport,
    content: BlogContent,
    result: ImprovementResult,
    output_dir: str,
) -> str:
    """Write eeat_report.txt and return the file path."""
    path = os.path.join(output_dir, "eeat_report.txt")

    lines = []
    lines.append("=" * 70)
    lines.append("  E-E-A-T ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  URL:    {content.url}")
    lines.append(f"  Title:  {content.title}")
    lines.append(f"  Words:  {content.word_count}")
    lines.append(f"  Date:   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Scores overview
    lines.append("-" * 70)
    lines.append("  SCORES")
    lines.append("-" * 70)
    lines.append("")
    lines.append(f"  Overall (current):   {_bar(report.overall_score)}")
    lines.append(f"  Overall (projected): {_bar(report.projected_score)}")
    lines.append("")
    for dim in [report.experience, report.expertise, report.authoritativeness, report.trust]:
        lines.append(f"  {dim.name:<20s} {_bar(dim.score)}")
    lines.append("")

    # Strengths
    if report.strengths:
        lines.append("-" * 70)
        lines.append("  STRENGTHS")
        lines.append("-" * 70)
        lines.append("")
        for s in report.strengths:
            lines.append(f"  + {s}")
        lines.append("")

    # Gaps by dimension
    lines.append("-" * 70)
    lines.append("  GAPS IDENTIFIED")
    lines.append("-" * 70)
    lines.append("")
    for dim in [report.experience, report.expertise, report.authoritativeness, report.trust]:
        if dim.gaps:
            lines.append(f"  [{dim.name}]")
            for g in dim.gaps:
                lines.append(f"    - {g}")
            lines.append("")

    # Missing elements
    if report.missing_elements:
        lines.append("-" * 70)
        lines.append("  MISSING ELEMENTS")
        lines.append("-" * 70)
        lines.append("")
        for m in report.missing_elements:
            lines.append(f"  [ ] {m}")
        lines.append("")

    # AI-generic phrases
    if report.ai_phrases_found:
        lines.append("-" * 70)
        lines.append("  AI-GENERIC PHRASES DETECTED")
        lines.append("-" * 70)
        lines.append("")
        for phrase in report.ai_phrases_found:
            lines.append(f'  ! "{phrase}"')
        lines.append("")
        if result.ai_phrase_rewrites:
            lines.append("  Suggested rewrites:")
            lines.append("")
            for rw in result.ai_phrase_rewrites:
                lines.append(f'    Original: "{rw.get("original", "")}"')
                for i, opt in enumerate(rw.get("options", []), 1):
                    lines.append(f'      Option {i}: "{opt}"')
                if rw.get("why"):
                    lines.append(f"      Reason: {rw['why']}")
                lines.append("")

    # Outdated stats
    if report.outdated_stats:
        lines.append("-" * 70)
        lines.append("  POTENTIALLY OUTDATED INFORMATION")
        lines.append("-" * 70)
        lines.append("")
        for stat in report.outdated_stats:
            lines.append(f"  ? {stat}")
        lines.append("")

    # Manual actions checklist
    lines.append("-" * 70)
    lines.append("  MANUAL ACTIONS NEEDED")
    lines.append("-" * 70)
    lines.append("")
    actions = []
    if not content.author:
        actions.append("Add author name, photo, and credentials")
    if not content.publish_date:
        actions.append("Add publication and last-updated date")
    for sug in result.experience_suggestions:
        placeholder = sug.get("placeholder", sug.get("suggestion", ""))
        actions.append(f"Add personal experience: {placeholder}")
    for q in result.expertise_questions[:5]:
        actions.append(f"Answer expertise question: {q}")
    for d in result.data_opportunities[:3]:
        actions.append(f"Add data point: {d.get('suggestion', '')}")
    for c in result.citation_spots[:3]:
        actions.append(f"Add citation: {c.get('topic', '')}")
    for t in result.trust_recommendations[:4]:
        actions.append(f"Trust signal: {t}")

    for i, action in enumerate(actions, 1):
        lines.append(f"  {i:2d}. [ ] {action}")
    lines.append("")

    # Improvements checklist
    lines.append("-" * 70)
    lines.append("  AUTOMATED IMPROVEMENTS MADE")
    lines.append("-" * 70)
    lines.append("")
    checks = [
        ("Quick Answer / TL;DR section added", bool(result.quick_answer)),
        ("FAQ section generated", bool(result.faq_questions)),
        ("Heading restructuring suggested", bool(result.heading_rewrites)),
        ("AI-phrase rewrites provided", bool(result.ai_phrase_rewrites)),
        ("Schema markup generated", bool(result.schema_suggestions)),
        ("Experience placeholders inserted", bool(result.experience_suggestions)),
        ("Citation opportunities identified", bool(result.citation_spots)),
        ("Related questions listed", bool(result.related_questions)),
    ]
    for label, done in checks:
        mark = "x" if done else " "
        lines.append(f"  [{mark}] {label}")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


def write_implementation_guide(
    report: EEATReport,
    content: BlogContent,
    result: ImprovementResult,
    output_dir: str,
) -> str:
    """Write implementation_guide.txt and return the file path."""
    path = os.path.join(output_dir, "implementation_guide.txt")

    lines = []
    lines.append("=" * 70)
    lines.append("  IMPLEMENTATION GUIDE")
    lines.append(f"  For: {content.title}")
    lines.append("=" * 70)
    lines.append("")

    # Step 1: Personal experiences
    lines.append("-" * 70)
    lines.append("  STEP 1: ADD PERSONAL EXPERIENCES")
    lines.append("-" * 70)
    lines.append("")
    lines.append("  These are the highest-impact changes. Only YOU can provide this")
    lines.append("  content — it's what separates your post from AI-generated filler.")
    lines.append("")

    if result.experience_suggestions:
        for i, sug in enumerate(result.experience_suggestions, 1):
            lines.append(f"  {i}. Location: {sug.get('location', 'See improved content')}")
            lines.append(f"     What to add: {sug.get('suggestion', '')}")
            lines.append(f"     Marker: {sug.get('placeholder', '')}")
            lines.append("")
            lines.append("     Tips:")
            lines.append("     - Include specific numbers (dates, timeframes, results)")
            lines.append("     - Name tools, products, or methods you actually used")
            lines.append("     - Mention what surprised you or what you'd do differently")
            lines.append("")
    else:
        lines.append("  No specific suggestions generated. Review the improved content")
        lines.append("  for [MANUAL INPUT NEEDED] markers.")
        lines.append("")

    # Step 2: Expertise questions
    lines.append("-" * 70)
    lines.append("  STEP 2: ANSWER EXPERTISE QUESTIONS")
    lines.append("-" * 70)
    lines.append("")
    lines.append("  Answering these questions in your content demonstrates deep knowledge.")
    lines.append("")

    if result.expertise_questions:
        for i, q in enumerate(result.expertise_questions, 1):
            lines.append(f"  {i}. {q}")
        lines.append("")
        lines.append("  How to use these:")
        lines.append("  - Weave answers naturally into existing sections")
        lines.append("  - Or add a dedicated subsection for complex answers")
        lines.append("  - Use your real experience to answer, not generic advice")
        lines.append("")
    else:
        lines.append("  No expertise questions generated.")
        lines.append("")

    # Step 3: Citations and statistics
    lines.append("-" * 70)
    lines.append("  STEP 3: ADD CITATIONS & STATISTICS")
    lines.append("-" * 70)
    lines.append("")

    if result.data_opportunities:
        lines.append("  Data points to find and add:")
        lines.append("")
        for i, d in enumerate(result.data_opportunities, 1):
            lines.append(f"  {i}. {d.get('suggestion', '')}")
            lines.append(f"     Where: {d.get('location', '')}")
            lines.append(f"     Source tip: {d.get('search_tip', 'Search Google Scholar or Statista')}")
            lines.append("")

    if result.citation_spots:
        lines.append("  Citation opportunities:")
        lines.append("")
        for i, c in enumerate(result.citation_spots, 1):
            lines.append(f"  {i}. Topic: {c.get('topic', '')}")
            lines.append(f"     Where: {c.get('location', '')}")
            lines.append(f"     Source type: {c.get('suggested_source_type', '')}")
            lines.append("")

    lines.append("  Where to find good sources:")
    lines.append("  - Google Scholar (scholar.google.com) — peer-reviewed research")
    lines.append("  - Statista (statista.com) — industry statistics")
    lines.append("  - Government data (data.gov, census.gov, bls.gov)")
    lines.append("  - Industry reports (Gartner, Forrester, McKinsey)")
    lines.append("  - Original surveys and studies from major companies")
    lines.append("")

    # Step 4: Trust signals
    lines.append("-" * 70)
    lines.append("  STEP 4: IMPLEMENT TRUST SIGNALS")
    lines.append("-" * 70)
    lines.append("")

    if result.trust_recommendations:
        for i, t in enumerate(result.trust_recommendations, 1):
            lines.append(f"  {i}. {t}")
        lines.append("")
    else:
        lines.append("  General trust signals to add:")
        lines.append("")

    lines.append("  Essential trust checklist:")
    lines.append("  [ ] Author bio with credentials, photo, and links")
    lines.append("  [ ] Publication date clearly visible")
    lines.append("  [ ] 'Last updated' date if content has been revised")
    lines.append("  [ ] Editorial standards or fact-checking note")
    lines.append("  [ ] Disclosure for affiliate links or sponsored content")
    lines.append("  [ ] Contact information or about page linked")
    lines.append("  [ ] Sources linked inline (not just listed at bottom)")
    lines.append("")

    # Step 5: Technical SEO
    lines.append("-" * 70)
    lines.append("  STEP 5: TECHNICAL SEO ADDITIONS")
    lines.append("-" * 70)
    lines.append("")

    lines.append("  A. STRUCTURED DATA (Schema Markup)")
    lines.append("  ----------------------------------")
    lines.append("  Add these JSON-LD scripts to your page's <head> section.")
    lines.append("  See improved_content.md for the complete code.")
    lines.append("")

    if result.schema_suggestions:
        if "article_schema" in result.schema_suggestions:
            lines.append("  Article schema: included in improved_content.md")
            lines.append("  - Helps Google understand the article type, author, date")
            lines.append("")
        if "faq_schema" in result.schema_suggestions:
            lines.append("  FAQ schema: included in improved_content.md")
            lines.append("  - Can trigger FAQ rich results in search")
            lines.append("  - Must match visible FAQ content on the page")
            lines.append("")

    lines.append("  B. META TAGS")
    lines.append("  ------------")
    if content.meta_description:
        lines.append(f"  Current meta description: {content.meta_description}")
    else:
        lines.append("  No meta description found!")
    lines.append("")
    if result.quick_answer:
        lines.append(f"  Suggested meta description:")
        lines.append(f"  {result.quick_answer[:155]}")
    lines.append("")

    lines.append("  C. HEADING OPTIMIZATION")
    lines.append("  -----------------------")
    if result.heading_rewrites:
        for rw in result.heading_rewrites:
            lines.append(f'  Before: {rw.get("original", "")}')
            lines.append(f'  After:  {rw.get("rewrite", "")}')
            lines.append(f'  Why:    {rw.get("rationale", "")}')
            lines.append("")
    else:
        lines.append("  No heading rewrites suggested.")
        lines.append("")

    lines.append("  D. RELATED QUESTIONS TO COVER")
    lines.append("  -----------------------------")
    lines.append("  Adding sections that answer these questions can help you")
    lines.append("  appear in 'People Also Ask' and AI Overview results:")
    lines.append("")
    if result.related_questions:
        for q in result.related_questions:
            lines.append(f"  - {q}")
    lines.append("")

    # Summary
    lines.append("=" * 70)
    lines.append("  PRIORITY ORDER")
    lines.append("=" * 70)
    lines.append("")
    lines.append("  1. Add personal experiences (highest E-E-A-T impact)")
    lines.append("  2. Insert citations and data points")
    lines.append("  3. Implement trust signals (author bio, dates)")
    lines.append("  4. Add FAQ section with schema markup")
    lines.append("  5. Optimize headings and meta description")
    lines.append("  6. Replace AI-generic phrases with specific language")
    lines.append("  7. Add structured data to page source")
    lines.append("")
    lines.append("  Time estimate: 1-2 hours for manual additions,")
    lines.append("  15 minutes for technical/schema changes.")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


def write_all_outputs(
    content: BlogContent,
    report: EEATReport,
    result: ImprovementResult,
    output_dir: str,
) -> list[str]:
    """
    Write all three output files. Creates the output directory if needed.

    Returns a list of file paths created.
    """
    os.makedirs(output_dir, exist_ok=True)

    paths = [
        write_improved_content(result, content, output_dir),
        write_eeat_report(report, content, result, output_dir),
        write_implementation_guide(report, content, result, output_dir),
    ]

    return paths
