"""
Content scraper module for extracting blog post content from URLs.
Handles various blog platforms (WordPress, Medium, custom sites).
"""

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# Common selectors for blog content across platforms
CONTENT_SELECTORS = [
    # WordPress
    "article .entry-content",
    ".post-content",
    ".entry-content",
    ".article-content",
    # Medium
    "article section",
    # Ghost
    ".post-full-content",
    ".gh-content",
    # Hugo / static site generators
    ".content",
    ".post-body",
    # Generic
    "article",
    '[role="article"]',
    "main",
    ".main-content",
    "#content",
]

TITLE_SELECTORS = [
    "h1.entry-title",
    "h1.post-title",
    "article h1",
    ".post-header h1",
    "header h1",
    "h1",
]

AUTHOR_SELECTORS = [
    ".author-name",
    ".post-author",
    '[rel="author"]',
    ".byline",
    ".entry-author",
    'meta[name="author"]',
    ".author",
]

DATE_SELECTORS = [
    "time[datetime]",
    ".post-date",
    ".entry-date",
    ".published",
    'meta[property="article:published_time"]',
    'meta[name="date"]',
]


@dataclass
class BlogContent:
    """Structured representation of extracted blog content."""

    url: str
    title: str = ""
    body_text: str = ""
    body_html: str = ""
    headings: list[dict[str, str]] = field(default_factory=list)
    meta_description: str = ""
    author: str = ""
    publish_date: str = ""
    word_count: int = 0
    images: list[dict[str, str]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    raw_html: str = ""
    platform: str = "unknown"


class ScrapingError(Exception):
    """Raised when content extraction fails."""


def fetch_page(url: str, timeout: int = 30) -> str:
    """Fetch the HTML content of a URL with proper headers."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        raise ScrapingError(f"Request timed out after {timeout}s: {url}")
    except requests.exceptions.ConnectionError:
        raise ScrapingError(f"Could not connect to: {url}")
    except requests.exceptions.HTTPError as e:
        raise ScrapingError(f"HTTP error {e.response.status_code}: {url}")
    except requests.exceptions.RequestException as e:
        raise ScrapingError(f"Failed to fetch URL: {e}")


def detect_platform(soup: BeautifulSoup, url: str) -> str:
    """Detect the blogging platform from HTML clues."""
    html_str = str(soup)

    if "wp-content" in html_str or "wordpress" in html_str.lower():
        return "wordpress"
    if "medium.com" in url or soup.find("meta", {"property": "al:android:package", "content": "com.medium.reader"}):
        return "medium"
    if "ghost" in html_str.lower() or soup.find("meta", {"name": "generator", "content": re.compile(r"Ghost")}):
        return "ghost"
    if soup.find("meta", {"name": "generator", "content": re.compile(r"Hugo")}):
        return "hugo"
    if soup.find("meta", {"name": "generator", "content": re.compile(r"Jekyll")}):
        return "jekyll"

    return "unknown"


def _extract_first_match(soup: BeautifulSoup, selectors: list[str]) -> Tag | None:
    """Try each CSS selector and return the first match."""
    for selector in selectors:
        result = soup.select_one(selector)
        if result:
            return result
    return None


def extract_title(soup: BeautifulSoup) -> str:
    """Extract the blog post title."""
    # Try content selectors first
    tag = _extract_first_match(soup, TITLE_SELECTORS)
    if tag:
        return tag.get_text(strip=True)

    # Fallback to <title> tag
    title_tag = soup.find("title")
    if title_tag:
        # Strip common suffixes like " | Blog Name" or " - Site Name"
        title = title_tag.get_text(strip=True)
        for sep in [" | ", " - ", " – ", " — "]:
            if sep in title:
                title = title.split(sep)[0].strip()
                break
        return title

    # OG title
    og = soup.find("meta", {"property": "og:title"})
    if og and og.get("content"):
        return og["content"]

    return ""


def extract_meta_description(soup: BeautifulSoup) -> str:
    """Extract the meta description."""
    for attr in [
        {"name": "description"},
        {"property": "og:description"},
        {"name": "twitter:description"},
    ]:
        tag = soup.find("meta", attr)
        if tag and tag.get("content"):
            return tag["content"]
    return ""


def extract_author(soup: BeautifulSoup) -> str:
    """Extract author information."""
    # Meta tag
    meta = soup.find("meta", {"name": "author"})
    if meta and meta.get("content"):
        return meta["content"]

    # JSON-LD
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        text = script.string or ""
        if '"author"' in text:
            # Simple extraction without importing json to keep it light
            match = re.search(r'"author"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"', text)
            if match:
                return match.group(1)
            match = re.search(r'"author"\s*:\s*"([^"]+)"', text)
            if match:
                return match.group(1)

    # DOM selectors
    for selector in AUTHOR_SELECTORS:
        tag = soup.select_one(selector)
        if tag:
            if tag.name == "meta":
                return tag.get("content", "")
            return tag.get_text(strip=True)

    return ""


def extract_publish_date(soup: BeautifulSoup) -> str:
    """Extract the publication date."""
    # Time tag with datetime attribute
    time_tag = soup.find("time", {"datetime": True})
    if time_tag:
        return time_tag["datetime"]

    # Meta tags
    for prop in ["article:published_time", "datePublished", "date"]:
        meta = soup.find("meta", {"property": prop}) or soup.find("meta", {"name": prop})
        if meta and meta.get("content"):
            return meta["content"]

    # JSON-LD
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        text = script.string or ""
        match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', text)
        if match:
            return match.group(1)

    return ""


def extract_body(soup: BeautifulSoup) -> tuple[str, str]:
    """Extract the main body content. Returns (plain_text, html)."""
    container = _extract_first_match(soup, CONTENT_SELECTORS)
    if not container:
        logger.warning("Could not find content container, falling back to <body>")
        container = soup.find("body")
        if not container:
            return "", ""

    # Remove unwanted elements
    for tag_name in ["script", "style", "nav", "footer", "aside", "iframe", "noscript"]:
        for tag in container.find_all(tag_name):
            tag.decompose()

    # Remove common non-content elements
    for cls in ["sidebar", "widget", "advertisement", "ad-", "social-share", "related-posts", "comments"]:
        for tag in container.find_all(class_=re.compile(cls, re.I)):
            tag.decompose()

    html = str(container)
    text = container.get_text(separator="\n", strip=True)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text, html


def extract_headings(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Extract all headings from the content in order."""
    container = _extract_first_match(soup, CONTENT_SELECTORS)
    if not container:
        container = soup.find("body") or soup

    headings = []
    for tag in container.find_all(re.compile(r"^h[1-6]$")):
        headings.append({
            "level": tag.name,
            "text": tag.get_text(strip=True),
        })
    return headings


def extract_images(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Extract images with their alt text."""
    container = _extract_first_match(soup, CONTENT_SELECTORS)
    if not container:
        container = soup.find("body") or soup

    images = []
    for img in container.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "")
        if src:
            images.append({"src": src, "alt": alt})
    return images


def extract_links(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Extract outbound links."""
    container = _extract_first_match(soup, CONTENT_SELECTORS)
    if not container:
        container = soup.find("body") or soup

    links = []
    for a in container.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if href.startswith("http"):
            links.append({"href": href, "text": text})
    return links


def scrape_blog(url: str, verbose: bool = False) -> BlogContent:
    """
    Main entry point: fetch a blog URL and extract structured content.

    Args:
        url: The blog post URL to scrape.
        verbose: If True, log detailed extraction info.

    Returns:
        BlogContent dataclass with all extracted fields.

    Raises:
        ScrapingError: If fetching or parsing fails.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ScrapingError(f"Invalid URL: {url}")

    if verbose:
        logger.info("Fetching %s", url)

    html = fetch_page(url)
    soup = BeautifulSoup(html, "lxml")

    platform = detect_platform(soup, url)
    if verbose:
        logger.info("Detected platform: %s", platform)

    title = extract_title(soup)
    meta_description = extract_meta_description(soup)
    author = extract_author(soup)
    publish_date = extract_publish_date(soup)
    body_text, body_html = extract_body(soup)
    headings = extract_headings(soup)
    images = extract_images(soup)
    links = extract_links(soup)

    word_count = len(body_text.split()) if body_text else 0

    content = BlogContent(
        url=url,
        title=title,
        body_text=body_text,
        body_html=body_html,
        headings=headings,
        meta_description=meta_description,
        author=author,
        publish_date=publish_date,
        word_count=word_count,
        images=images,
        links=links,
        raw_html=html,
        platform=platform,
    )

    if verbose:
        logger.info(
            "Extracted: title=%r, words=%d, headings=%d, images=%d, links=%d",
            title, word_count, len(headings), len(images), len(links),
        )

    return content
