#!/usr/bin/env python3
"""
Test script for the Blog E-E-A-T Improver.

Tests scraping, analysis, and formatting without needing network access
or an API key. Uses a sample HTML blog post served locally.
"""

import http.server
import json
import os
import shutil
import threading

from analyzer import analyze_eeat
from formatter import write_all_outputs
from improver import ImprovementResult
from scraper import scrape_blog

# ---------------------------------------------------------------------------
# Sample blog post HTML (simulates a real WordPress-style page)
# ---------------------------------------------------------------------------

SAMPLE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <title>10 Tips for Remote Work Productivity | TechBlog</title>
    <meta name="description" content="Learn how to be productive working from home with these tips.">
    <meta name="author" content="Jane Smith">
    <meta property="og:title" content="10 Tips for Remote Work Productivity">
    <script type="application/ld+json">
    {
        "@type": "Article",
        "datePublished": "2024-03-15",
        "author": {"@type": "Person", "name": "Jane Smith"}
    }
    </script>
</head>
<body>
<nav><a href="/">Home</a></nav>
<article>
    <h1 class="entry-title">10 Tips for Remote Work Productivity</h1>
    <div class="entry-content">
        <p>In today's fast-paced world, remote work has become a game-changer
        for millions of professionals. It's important to note that staying
        productive while working from home requires discipline and the right
        strategies. Let's delve into the best practices.</p>

        <h2>Setting Up Your Workspace</h2>
        <p>Having a dedicated workspace is crucial for maintaining focus.
        You need to leverage the right tools and create an environment that
        seamlessly supports your workflow. A robust setup can take your
        productivity to the next level.</p>

        <p>Consider investing in a good desk and ergonomic chair. The right
        equipment makes a huge difference in your daily comfort and output.
        According to a 2019 study, ergonomic setups reduce fatigue by 30%.</p>

        <h2>Managing Your Time</h2>
        <p>Time management is essential for remote workers. Without the
        structure of an office, you need to create your own routine.
        72% of workers prefer remote work for its flexibility.</p>

        <p>Try time-blocking your calendar. Dedicate specific hours to deep
        work, meetings, and breaks. This approach helps you stay on track
        and avoid the common pitfalls of working from home.</p>

        <h2>Staying Connected</h2>
        <p>Communication is key when working remotely. Use tools like Slack
        and Zoom to stay connected with your team. Regular check-ins help
        maintain alignment and prevent misunderstandings.</p>

        <p>Don't forget about social connections too. Schedule virtual coffee
        chats and team building activities to maintain the human element
        of your workplace relationships.</p>

        <h2>Avoiding Burnout</h2>
        <p>One of the biggest challenges of remote work is knowing when to
        stop. Set clear boundaries between work and personal time. Take
        regular breaks and step away from your screen throughout the day.</p>

        <p>Remember, productivity isn't about working more hours. It's about
        working smarter and taking care of your wellbeing. A healthy work-life
        balance is the foundation of sustainable productivity.</p>

        <img src="/images/workspace.jpg" alt="A productive home workspace">
        <img src="/images/schedule.png" alt="Time blocking schedule example">

        <p>For more tips, check out our
        <a href="https://example.com/guide">complete remote work guide</a> and
        <a href="https://example.com/tools">recommended tools list</a>.</p>
    </div>
</article>
<footer><p>Copyright 2024 TechBlog</p></footer>
</body>
</html>
"""


def start_test_server(port: int = 8899) -> http.server.HTTPServer:
    """Start a local HTTP server that serves the sample blog post."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SAMPLE_HTML.encode())

        def log_message(self, format, *args):
            pass  # suppress request logs

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def make_mock_improvements(content, report) -> ImprovementResult:
    """Create a mock ImprovementResult without calling the Claude API."""
    return ImprovementResult(
        improved_markdown=f"""\
# How to Actually Stay Productive Working From Home

## Quick Answer

Remote work productivity comes down to three things: a consistent workspace,
structured time blocks, and clear boundaries. Most tips overcomplicate it.

---

## Why Standard Remote Work Advice Falls Short

[MANUAL INPUT NEEDED: Share your personal remote work journey — when did it
start working for you, and what was the breakthrough moment?]

The shift to remote work isn't slowing down. Yet most advice reads like it
was written by someone who's never actually done it past week two.

<!-- SUGGESTION: Add a statistic about remote work adoption rates in 2024 -->

## What Does a Real Productive Home Setup Look Like?

Forget the Pinterest-perfect offices. What matters is *separation* — your
brain needs a physical cue that says "work mode."

[MANUAL INPUT NEEDED: Describe your actual setup — desk, chair, monitor.
Be honest about what you tried that didn't work first.]

## How Should You Structure Your Remote Work Day?

[MANUAL INPUT NEEDED: Walk through your real daily schedule including the
messy parts — not the idealized version.]

Time-blocking beats to-do lists when there's no office structure to lean on.
A 2024 study found that remote workers who time-block report 27% higher
task completion rates [CITE: productivity research on time-blocking].

## What Are the Biggest Distractions (and What Actually Fixes Them)?

[MANUAL INPUT NEEDED: Describe your biggest distraction and the specific
system you built to handle it.]

## How Do You Avoid Burnout Without an Office "Off Switch"?

[MANUAL INPUT NEEDED: Share your shutdown ritual — what signals the end
of your work day?]

The answer isn't "just set boundaries." It's building a physical ritual
that your brain recognizes as the transition from work to not-work.

## Frequently Asked Questions

### How many hours should you actually work from home?
Research suggests 5-6 genuinely productive hours in an 8-hour day.
Remote work doesn't change this — it just makes idle time more visible.

### Does remote work hurt career advancement?
It can if you're invisible. Send a weekly summary to your manager.
Document everything. Make your output undeniable.

### Is a dedicated home office necessary?
No, but a dedicated *spot* is. Consistency matters more than square footage.
""",
        experience_suggestions=[
            {
                "location": "Opening section",
                "suggestion": "Share when remote work started working for you",
                "placeholder": "[MANUAL INPUT NEEDED: Your remote work turning point]",
            },
            {
                "location": "Workspace section",
                "suggestion": "Describe your real desk setup with honest pros and cons",
                "placeholder": "[MANUAL INPUT NEEDED: Your actual workspace setup]",
            },
            {
                "location": "Time management section",
                "suggestion": "Walk through a real workday including the messy parts",
                "placeholder": "[MANUAL INPUT NEEDED: Your real daily schedule]",
            },
        ],
        expertise_questions=[
            "What metrics do you use to measure your own remote productivity?",
            "How does productivity differ between developer and manager roles remotely?",
            "What's the biggest misconception about remote work productivity?",
        ],
        data_opportunities=[
            {
                "location": "Introduction",
                "suggestion": "Remote work adoption statistics for 2024",
                "search_tip": "Stanford WFH Research (wfhresearch.com)",
            },
            {
                "location": "Time management section",
                "suggestion": "Average productive hours per day for knowledge workers",
                "search_tip": "Google Scholar: 'knowledge worker productive hours'",
            },
        ],
        citation_spots=[
            {
                "location": "Ergonomics paragraph",
                "topic": "Updated ergonomic impact research",
                "suggested_source_type": "Peer-reviewed study (2023+)",
            },
        ],
        faq_questions=[
            "How many hours should you actually work from home?",
            "Does remote work hurt career advancement?",
            "Is a dedicated home office necessary?",
            "How do you stay motivated long-term?",
            "What's the best daily routine for remote workers?",
        ],
        trust_recommendations=[
            "Add author bio with remote work experience and credentials",
            "Display 'Last updated' date prominently",
            "Add editorial note about how tips were developed",
            "Link to author's LinkedIn profile",
        ],
        ai_phrase_rewrites=[
            {
                "original": "in today's fast-paced world",
                "options": ["Since the 2020 shift to remote work", "With 27% of work days now remote"],
                "why": "Most common AI-generated opener",
            },
            {
                "original": "game-changer",
                "options": ["the single biggest shift in how we work", "a permanent change"],
                "why": "Overused buzzword with no specific meaning",
            },
        ],
        quick_answer="Remote work productivity comes down to three things: a consistent workspace, structured time blocks, and clear boundaries.",
        heading_rewrites=[
            {
                "original": "Setting Up Your Workspace",
                "rewrite": "What Does a Productive Remote Workspace Actually Look Like?",
                "rationale": "Question format matches People Also Ask queries",
            },
            {
                "original": "Managing Your Time",
                "rewrite": "How Should You Structure Your Remote Work Day?",
                "rationale": "Targets featured snippet for scheduling queries",
            },
        ],
        related_questions=[
            "How do you stay motivated working from home long-term?",
            "What equipment do you need for a home office?",
            "How do managers track remote worker productivity?",
        ],
        schema_suggestions={
            "article_schema": {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "How to Actually Stay Productive Working From Home",
                "author": {"@type": "Person", "name": "[AUTHOR NAME]"},
            },
            "faq_schema": {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "How many hours should you actually work from home?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Research suggests 5-6 genuinely productive hours in an 8-hour day.",
                        },
                    }
                ],
            },
        },
    )


def main():
    output_dir = "./test_output"

    # Clean previous test output
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    print()
    print("=" * 60)
    print("  Blog E-E-A-T Improver — Test Suite")
    print("=" * 60)
    print()

    # --- Test 1: Scraping ---
    print("[1/4] Testing content scraper...")
    server = start_test_server(8899)
    try:
        content = scrape_blog("http://127.0.0.1:8899/blog/remote-work", verbose=True)
    finally:
        server.shutdown()

    assert content.title == "10 Tips for Remote Work Productivity", f"Title mismatch: {content.title!r}"
    assert content.author == "Jane Smith", f"Author mismatch: {content.author!r}"
    assert content.publish_date == "2024-03-15", f"Date mismatch: {content.publish_date!r}"
    assert content.word_count > 100, f"Word count too low: {content.word_count}"
    assert len(content.headings) >= 4, f"Too few headings: {len(content.headings)}"
    assert len(content.images) == 2, f"Image count mismatch: {len(content.images)}"
    assert len(content.links) >= 2, f"Link count mismatch: {len(content.links)}"
    assert content.meta_description != "", "Meta description missing"
    print(f"  OK  Title: {content.title}")
    print(f"  OK  Author: {content.author}")
    print(f"  OK  Date: {content.publish_date}")
    print(f"  OK  Words: {content.word_count}")
    print(f"  OK  Headings: {len(content.headings)}")
    print(f"  OK  Images: {len(content.images)}")
    print(f"  OK  Links: {len(content.links)}")
    print()

    # --- Test 2: E-E-A-T Analysis ---
    print("[2/4] Testing E-E-A-T analyzer...")
    report = analyze_eeat(content)

    assert 1.0 <= report.overall_score <= 10.0, f"Score out of range: {report.overall_score}"
    assert report.experience.score >= 0
    assert report.expertise.score >= 0
    assert report.authoritativeness.score >= 0
    assert report.trust.score >= 0
    assert len(report.ai_phrases_found) >= 3, f"Should detect AI phrases: {report.ai_phrases_found}"
    assert report.projected_score > report.overall_score, "Projected should be higher"
    print(f"  OK  Overall score: {report.overall_score}/10")
    print(f"  OK  Experience:    {report.experience.score}/10")
    print(f"  OK  Expertise:     {report.expertise.score}/10")
    print(f"  OK  Authority:     {report.authoritativeness.score}/10")
    print(f"  OK  Trust:         {report.trust.score}/10")
    print(f"  OK  AI phrases:    {len(report.ai_phrases_found)} detected")
    print(f"  OK  Outdated stats: {len(report.outdated_stats)} flagged")
    print(f"  OK  Projected:     {report.projected_score}/10")
    print()

    # --- Test 3: Mock improvements (no API key needed) ---
    print("[3/4] Testing improvement structure (mock, no API call)...")
    result = make_mock_improvements(content, report)

    assert "[MANUAL INPUT NEEDED" in result.improved_markdown
    assert len(result.experience_suggestions) >= 3
    assert len(result.faq_questions) >= 3
    assert len(result.trust_recommendations) >= 3
    assert result.quick_answer != ""
    assert "article_schema" in result.schema_suggestions
    assert "faq_schema" in result.schema_suggestions
    print(f"  OK  Improved markdown: {len(result.improved_markdown)} chars")
    print(f"  OK  Experience suggestions: {len(result.experience_suggestions)}")
    print(f"  OK  Expertise questions: {len(result.expertise_questions)}")
    print(f"  OK  FAQ questions: {len(result.faq_questions)}")
    print(f"  OK  Trust recommendations: {len(result.trust_recommendations)}")
    print(f"  OK  Schema suggestions: {list(result.schema_suggestions.keys())}")
    print()

    # --- Test 4: Output file generation ---
    print("[4/4] Testing output file generation...")
    paths = write_all_outputs(content, report, result, output_dir)

    assert len(paths) == 3
    for p in paths:
        assert os.path.exists(p), f"Missing output file: {p}"
        size = os.path.getsize(p)
        assert size > 100, f"File too small: {p} ({size} bytes)"
        print(f"  OK  {os.path.basename(p)} ({size:,} bytes)")

    # Verify content of each file
    with open(os.path.join(output_dir, "improved_content.md")) as f:
        md = f.read()
        assert "[MANUAL INPUT NEEDED" in md, "Missing manual markers"
        assert "schema.org" in md, "Missing schema markup"

    with open(os.path.join(output_dir, "eeat_report.txt")) as f:
        rpt = f.read()
        assert "SCORES" in rpt, "Missing scores section"
        assert "GAPS" in rpt, "Missing gaps section"
        assert "MANUAL ACTIONS" in rpt, "Missing actions section"

    with open(os.path.join(output_dir, "implementation_guide.txt")) as f:
        guide = f.read()
        assert "STEP 1" in guide, "Missing step 1"
        assert "STEP 5" in guide, "Missing step 5"
        assert "PRIORITY ORDER" in guide, "Missing priority section"

    print()
    print("=" * 60)
    print(f"  ALL TESTS PASSED")
    print(f"  Output files saved to: {output_dir}/")
    print("=" * 60)
    print()
    print("  To test with real Claude API improvements:")
    print("  export ANTHROPIC_API_KEY='your-key'")
    print("  python improve_seo.py https://your-blog.com/post --output-dir ./real_output")
    print()


if __name__ == "__main__":
    main()
