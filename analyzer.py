"""
E-E-A-T analysis module.
Scores blog content on Experience, Expertise, Authoritativeness, and Trust.
"""

import re
from dataclasses import dataclass, field

from scraper import BlogContent

# Phrases that commonly signal AI-generated or generic content
AI_GENERIC_PHRASES = [
    r"\bin today'?s (?:fast-paced|digital|modern|ever-changing) world\b",
    r"\bin conclusion\b",
    r"\bit'?s (?:important|worth noting|crucial|essential) to (?:note|remember|understand)\b",
    r"\bwithout further ado\b",
    r"\blook no further\b",
    r"\bunlock (?:the (?:power|potential|secrets?)|your)\b",
    r"\bgame[- ]?changer\b",
    r"\btake .+ to the next level\b",
    r"\bdelve (?:into|deeper)\b",
    r"\bseamless(?:ly)?\b",
    r"\bleverage\b",
    r"\bsynerg(?:y|ize|ies)\b",
    r"\bholistic(?:ally)?\b",
    r"\bin the realm of\b",
    r"\btapestry\b",
    r"\bnavigat(?:e|ing) the (?:landscape|world|complexities)\b",
    r"\brobust\b",
    r"\bcutting[- ]?edge\b",
    r"\bparadigm shift\b",
    r"\bat the end of the day\b",
    r"\bone size fits all\b",
    r"\brest assured\b",
    r"\bdigital landscape\b",
    r"\bever-evolving\b",
    r"\bstands out (?:from|as)\b",
]

# Signals for each E-E-A-T dimension
EXPERIENCE_SIGNALS = [
    r"\bi (?:found|noticed|discovered|learned|tried|tested|used|experienced)\b",
    r"\bin my experience\b",
    r"\bwhen i (?:was|worked|started)\b",
    r"\bover (?:the )?(?:past |last )?\d+ years?\b",
    r"\bi['']ve (?:been|seen|worked)\b",
    r"\bpersonally\b",
    r"\bfirst[- ]?hand\b",
    r"\bmy (?:team|company|client|project)\b",
    r"\bwe (?:found|discovered|noticed|implemented|built|tested)\b",
    r"\bcase study\b",
    r"\breal[- ]?world example\b",
]

EXPERTISE_SIGNALS = [
    r"\baccording to (?:research|studies|data|a \d{4} (?:study|report|survey))\b",
    r"\bresearch (?:shows|suggests|indicates|from)\b",
    r"\bstud(?:y|ies) (?:show|suggest|found|from)\b",
    r"\bdata (?:shows|suggests|indicates|from)\b",
    r"\b\d+(?:\.\d+)?%\b",  # percentages
    r"\bstatistic(?:s|ally)\b",
    r"\bpeer[- ]?reviewed\b",
    r"\bpublished in\b",
    r"\btechnical(?:ly)?\b",
    r"\bmethodolog(?:y|ies|ical)\b",
    r"\bspecifically\b",
    r"\bfor (?:example|instance)\b",
]

AUTHORITY_SIGNALS = [
    r"\b(?:source|citation|reference)s?\b",
    r"https?://",
    r"\baccording to\b",
    r"\bquote[ds]?\b",
    r"\b(?:expert|specialist|professional)s?\b",
    r"\bindustry\b",
    r"\bcredential\b",
    r"\bcertifi(?:ed|cation)\b",
    r"\baward\b",
    r"\brecogni[sz]ed\b",
    r"\bfeatured (?:in|on|by)\b",
]

TRUST_SIGNALS = [
    r"\bupdated?\b.*\b\d{4}\b",
    r"\bfact[- ]?check\b",
    r"\btranspar(?:ent|ency)\b",
    r"\bdisclosure\b",
    r"\baffiliates?\b",
    r"\bsponsored\b",
    r"\beditorial (?:policy|guidelines|standards)\b",
    r"\bverif(?:y|ied|ication)\b",
    r"\baccura(?:te|cy)\b",
    r"\bmedically reviewed\b",
]


@dataclass
class DimensionScore:
    """Score and details for one E-E-A-T dimension."""
    name: str
    score: float  # 1-10
    signals_found: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


@dataclass
class EEATReport:
    """Full E-E-A-T analysis report."""
    overall_score: float
    experience: DimensionScore = field(default_factory=lambda: DimensionScore("Experience", 0))
    expertise: DimensionScore = field(default_factory=lambda: DimensionScore("Expertise", 0))
    authoritativeness: DimensionScore = field(default_factory=lambda: DimensionScore("Authoritativeness", 0))
    trust: DimensionScore = field(default_factory=lambda: DimensionScore("Trust", 0))
    ai_phrases_found: list[str] = field(default_factory=list)
    outdated_stats: list[str] = field(default_factory=list)
    missing_elements: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    projected_score: float = 0.0


def _count_signals(text: str, patterns: list[str]) -> list[str]:
    """Return unique matches for a list of regex patterns in text."""
    found = []
    lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, lower, re.IGNORECASE)
        for m in matches:
            readable = m.strip() if isinstance(m, str) else str(m)
            if readable and readable not in found:
                found.append(readable)
    return found


def _score_dimension(signal_count: int, max_expected: int, has_structural: bool = False) -> float:
    """Convert signal count to a 1-10 score."""
    base = min(signal_count / max_expected, 1.0) * 8  # max 8 from signals
    bonus = 2.0 if has_structural else 0.0
    return round(min(base + bonus, 10.0), 1)


def find_ai_phrases(text: str) -> list[str]:
    """Identify generic AI-sounding phrases in the text."""
    found = []
    for pattern in AI_GENERIC_PHRASES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            readable = m.strip()
            if readable and readable not in found:
                found.append(readable)
    return found


def find_outdated_stats(text: str) -> list[str]:
    """Flag statistics or dates that might be outdated (before 2023)."""
    outdated = []
    # Find year references
    year_pattern = r'(?:in |from |since |as of |circa |a )(\d{4})'
    for match in re.finditer(year_pattern, text):
        year = int(match.group(1))
        if 1990 <= year <= 2022:
            context_start = max(0, match.start() - 40)
            context_end = min(len(text), match.end() + 40)
            snippet = text[context_start:context_end].strip()
            outdated.append(f"Possibly outdated ({year}): ...{snippet}...")

    # Find "X% of" stats without a year
    stat_pattern = r'\b\d+(?:\.\d+)?%\s+of\b'
    for match in re.finditer(stat_pattern, text):
        context_start = max(0, match.start() - 20)
        context_end = min(len(text), match.end() + 60)
        snippet = text[context_start:context_end].strip()
        # Check if there's a year nearby
        nearby = text[max(0, match.start() - 80):min(len(text), match.end() + 80)]
        if not re.search(r'\b20(?:2[3-9]|[3-9]\d)\b', nearby):
            outdated.append(f"Statistic without recent source: ...{snippet}...")

    return outdated


def analyze_eeat(content: BlogContent) -> EEATReport:
    """
    Perform E-E-A-T analysis on extracted blog content.

    Returns an EEATReport with scores, signals, and gaps.
    """
    text = content.body_text
    report = EEATReport(overall_score=0)

    # --- Experience ---
    exp_signals = _count_signals(text, EXPERIENCE_SIGNALS)
    has_personal = bool(re.search(r'\bi\b', text.lower()[:500]))  # first-person in opening
    report.experience = DimensionScore(
        name="Experience",
        score=_score_dimension(len(exp_signals), 6, has_personal),
        signals_found=exp_signals,
        gaps=[],
    )
    if len(exp_signals) < 2:
        report.experience.gaps.append("No personal experience or anecdotes shared")
    if not re.search(r'\bcase study\b', text, re.I):
        report.experience.gaps.append("No case studies or real-world examples")
    if not re.search(r'\bI (?:tried|tested|used|built)\b', text, re.I):
        report.experience.gaps.append("No first-hand testing or hands-on evidence")

    # --- Expertise ---
    exp_signals_e = _count_signals(text, EXPERTISE_SIGNALS)
    has_data = bool(re.search(r'\b\d+(?:\.\d+)?%\b', text))
    report.expertise = DimensionScore(
        name="Expertise",
        score=_score_dimension(len(exp_signals_e), 8, has_data),
        signals_found=exp_signals_e,
        gaps=[],
    )
    if not has_data:
        report.expertise.gaps.append("No statistics or data points cited")
    if not re.search(r'\bresearch|stud(?:y|ies)\b', text, re.I):
        report.expertise.gaps.append("No references to research or studies")
    if not re.search(r'\bfor (?:example|instance)\b', text, re.I):
        report.expertise.gaps.append("No concrete examples provided")
    if not re.search(r'\bstep[- ]by[- ]step|how to\b', text, re.I):
        report.expertise.gaps.append("No step-by-step guidance or methodology")

    # --- Authoritativeness ---
    auth_signals = _count_signals(text, AUTHORITY_SIGNALS)
    has_external_links = len(content.links) >= 2
    report.authoritativeness = DimensionScore(
        name="Authoritativeness",
        score=_score_dimension(len(auth_signals), 6, has_external_links),
        signals_found=auth_signals,
        gaps=[],
    )
    if len(content.links) < 2:
        report.authoritativeness.gaps.append("Few or no external references/citations")
    if not content.author:
        report.authoritativeness.gaps.append("No author information found")
    if not re.search(r'\baccording to\b', text, re.I):
        report.authoritativeness.gaps.append("No expert quotes or authoritative references")

    # --- Trust ---
    trust_signals = _count_signals(text, TRUST_SIGNALS)
    has_date = bool(content.publish_date)
    report.trust = DimensionScore(
        name="Trust",
        score=_score_dimension(len(trust_signals), 5, has_date),
        signals_found=trust_signals,
        gaps=[],
    )
    if not has_date:
        report.trust.gaps.append("No publication or update date visible")
    if not content.author:
        report.trust.gaps.append("No author attribution for accountability")
    if not content.meta_description:
        report.trust.gaps.append("Missing meta description")
    if not re.search(r'\bdisclosure|disclaimer|affiliate\b', text, re.I):
        # Only a gap if the content looks commercial
        if re.search(r'\bbuy|purchase|price|cost|product|service|recommend\b', text, re.I):
            report.trust.gaps.append("No disclosure or disclaimer for potentially commercial content")

    # --- AI Phrases ---
    report.ai_phrases_found = find_ai_phrases(text)

    # --- Outdated Stats ---
    report.outdated_stats = find_outdated_stats(text)

    # --- Missing Elements ---
    missing = []
    if not content.author:
        missing.append("Author name and credentials")
    if not content.publish_date:
        missing.append("Publication / last-updated date")
    if not content.meta_description:
        missing.append("Meta description")
    if len(content.headings) < 3:
        missing.append("Sufficient heading structure (needs more subheadings)")
    if content.word_count < 800:
        missing.append(f"Content depth (only {content.word_count} words — aim for 1,000+)")
    if not any(h["text"].endswith("?") for h in content.headings):
        missing.append("Question-based headings for featured snippets")
    has_faq = any("faq" in h["text"].lower() or "frequently" in h["text"].lower() for h in content.headings)
    if not has_faq:
        missing.append("FAQ section")
    report.missing_elements = missing

    # --- Strengths ---
    strengths = []
    if content.word_count >= 1500:
        strengths.append(f"Good content length ({content.word_count} words)")
    if len(content.headings) >= 5:
        strengths.append(f"Well-structured with {len(content.headings)} headings")
    if len(content.links) >= 3:
        strengths.append(f"Includes {len(content.links)} external links")
    if len(content.images) >= 2:
        strengths.append(f"Includes {len(content.images)} images")
    if content.author:
        strengths.append(f"Author attributed: {content.author}")
    if content.publish_date:
        strengths.append(f"Date provided: {content.publish_date}")
    if len(exp_signals) >= 3:
        strengths.append("Contains personal experience signals")
    report.strengths = strengths

    # --- Overall score ---
    scores = [
        report.experience.score,
        report.expertise.score,
        report.authoritativeness.score,
        report.trust.score,
    ]
    report.overall_score = round(sum(scores) / len(scores), 1)

    # Penalize for AI phrases
    penalty = min(len(report.ai_phrases_found) * 0.3, 2.0)
    report.overall_score = round(max(report.overall_score - penalty, 1.0), 1)

    # Projected score assumes all gaps are addressed
    total_gaps = sum(
        len(d.gaps)
        for d in [report.experience, report.expertise, report.authoritativeness, report.trust]
    )
    improvement = min(total_gaps * 0.5, 4.0)  # each gap addressed adds ~0.5
    report.projected_score = round(min(report.overall_score + improvement, 9.5), 1)

    return report
