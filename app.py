# app.py
# Personal Blog Migration Tool (Blogger <-> WordPress) — Streamlit
# NOTE: Designed for backing up/migrating YOUR OWN content. Respect robots.txt / ToS.

from __future__ import annotations

import re
import uuid
import html
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urljoin, urlencode, parse_qs

import requests
import streamlit as st
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


# ---------------------------
# UI / THEME (Premium Dark)
# ---------------------------
DARK_CSS = """
<style>
/* ---- Base page / gradient ---- */
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 800px at 20% 10%, #0b2a4a 0%, #050b12 45%, #010409 100%) !important;
  color: #ffffff !important;
}

/* ---- Hide Streamlit chrome (Stealth Mode) ---- */
header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, [data-testid="stStatusWidget"], [data-testid="stHeader"] {
  visibility: hidden !important;
  height: 0px !important;
}
a[href*="share"], button[title="Share"], button[title="View app"], button[title="Open in GitHub"] {
  display: none !important;
}

/* ---- Typography ---- */
* { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; }
label, .stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label {
  color: #ffffff !important;
  font-weight: 600 !important;
}

/* ---- Inputs ---- */
input, textarea, select, .stTextInput input, .stTextArea textarea {
  color: #ffffff !important;
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 12px !important;
}
div[data-baseweb="select"] * {
  color: #ffffff !important;
}
div[data-baseweb="select"] > div {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 12px !important;
}

/* ---- Cards / containers ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 18px !important;
  box-shadow: 0 10px 35px rgba(0,0,0,0.35) !important;
}

/* ---- Buttons (default) ---- */
.stButton button {
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,0.16) !important;
  background: rgba(255,255,255,0.08) !important;
  color: #ffffff !important;
  padding: 0.7rem 1rem !important;
  font-weight: 700 !important;
}

/* ---- Download button: golden-yellow ---- */
div[data-testid="stDownloadButton"] button {
  border-radius: 14px !important;
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%) !important;
  color: #1a1a1a !important;
  border: none !important;
  font-weight: 900 !important;
  padding: 0.85rem 1.1rem !important;
  box-shadow: 0 10px 30px rgba(253,160,133,0.20) !important;
}
div[data-testid="stDownloadButton"] button:hover {
  filter: brightness(1.05);
}

/* ---- Progress ---- */
div[role="progressbar"] {
  border-radius: 999px !important;
}

/* ---- Links ---- */
a, a:visited { color: #8bd3ff !important; }
</style>
"""

st.set_page_config(
    page_title="Personal Blog Migration Tool",
    page_icon="🗂️",
    layout="wide",
)

st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---------------------------
# Data model
# ---------------------------
@dataclass
class Post:
    title: str
    content_html: str
    source_url: str = ""
    updated_iso: str = ""
    post_id: str = ""


# ---------------------------
# Helpers
# ---------------------------
DEFAULT_HEADERS = {
    "User-Agent": "PersonalBlogMigrationTool/1.0 (+Streamlit; for personal backups)"
}

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "app": "http://www.w3.org/2007/app",
    "thr": "http://purl.org/syndication/thread/1.0",
    "gd": "http://schemas.google.com/g/2005",
    "georss": "http://www.georss.org/georss",
    "media": "http://search.yahoo.com/mrss/",
}

WP_NS = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}

def now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def safe_text(s: str) -> str:
    return (s or "").strip()

def strip_to_text(html_str: str) -> str:
    soup = BeautifulSoup(html_str or "", "html.parser")
    txt = soup.get_text("\n", strip=True)
    return txt

def extract_videos_only(html_str: str) -> str:
    soup = BeautifulSoup(html_str or "", "html.parser")
    video_bits = []

    for tag in soup.find_all(["iframe", "embed", "video"]):
        # keep only likely video embeds
        if tag.name == "iframe":
            src = (tag.get("src") or "").lower()
            if any(x in src for x in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "player", "embed"]):
                video_bits.append(str(tag))
        else:
            video_bits.append(str(tag))

    # Also capture <a> links to youtube/vimeo
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if any(x in href for x in ["youtube.com/watch", "youtu.be/", "vimeo.com/"]):
            video_bits.append(f'<p><a href="{html.escape(a["href"])}">{html.escape(a.get_text(strip=True) or a["href"])}</a></p>')

    return "\n".join(video_bits).strip()

def apply_content_filter(content_html: str, mode: str) -> str:
    if mode == "Full Content":
        return content_html or ""
    if mode == "Text Only":
        text = strip_to_text(content_html)
        # wrap as minimal HTML so exports remain valid
        return "<p>" + "<br/>".join(html.escape(line) for line in text.splitlines() if line.strip()) + "</p>"
    if mode == "Videos Only":
        vids = extract_videos_only(content_html)
        return vids if vids else "<p>(No videos detected)</p>"
    return content_html or ""

def normalize_atom_feed_url(url: str) -> str:
    """
    Accepts:
      - domain.com/atom.xml?redirect=false&start-index=1&max-results=500
      - https://domain.com/feeds/posts/default?max-results=500
      - or similar
    Returns the given url (trimmed), no heavy rewriting except ensuring scheme.
    """
    url = safe_text(url)
    if not url:
        return url
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    return url

def request_get(url: str, timeout: int = 30) -> requests.Response:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp

# ---------------------------
# BULK MODE: Atom discovery
# ---------------------------
def parse_atom_entries(atom_xml: str) -> List[Post]:
    """
    Parse Atom feed XML and extract posts (title + HTML content).
    Works well for Blogger atom.xml feeds.
    """
    root = ET.fromstring(atom_xml)

    # Some feeds use default namespace; ElementTree needs explicit ns in queries.
    entries = root.findall("atom:entry", ATOM_NS)
    posts: List[Post] = []

    for e in entries:
        title_el = e.find("atom:title", ATOM_NS)
        title = safe_text(title_el.text if title_el is not None else "Untitled")

        # Prefer <content type="html|xhtml">; fallback to <summary>
        content_el = e.find("atom:content", ATOM_NS)
        summary_el = e.find("atom:summary", ATOM_NS)

        content_html = ""
        if content_el is not None and content_el.text:
            content_html = content_el.text
        elif summary_el is not None and summary_el.text:
            content_html = summary_el.text

        # Find a canonical link
        link_url = ""
        for link_el in e.findall("atom:link", ATOM_NS):
            rel = (link_el.get("rel") or "").lower()
            href = link_el.get("href") or ""
            if rel in ("alternate", "") and href:
                link_url = href
                break

        # Updated timestamp if present
        updated_el = e.find("atom:updated", ATOM_NS)
        updated_iso = safe_text(updated_el.text if updated_el is not None else "")

        # Entry id if present
        id_el = e.find("atom:id", ATOM_NS)
        post_id = safe_text(id_el.text if id_el is not None else "")

        posts.append(Post(
            title=title,
            content_html=content_html,
            source_url=link_url,
            updated_iso=updated_iso,
            post_id=post_id
        ))

    return posts

def fetch_atom_bulk(feed_url: str, max_results: int = 500, hard_limit_pages: int = 40) -> Tuple[List[Post], List[str]]:
    """
    Fetch paginated Blogger-style Atom:
      ...atom.xml?redirect=false&start-index=1&max-results=500

    We increment start-index until no entries are returned or a page limit is hit.
    Returns (posts, page_urls)
    """
    feed_url = normalize_atom_feed_url(feed_url)
    parsed = urlparse(feed_url)
    qs = parse_qs(parsed.query)

    # If start-index/max-results not present, we will add them.
    base_qs = {k: v[:] for k, v in qs.items()}

    def build_url(start_index: int) -> str:
        q = {k: v[:] for k, v in base_qs.items()}
        q["start-index"] = [str(start_index)]
        q["max-results"] = [str(max_results)]
        # default redirect=false for blogger atom.xml usage
        if "redirect" not in q:
            q["redirect"] = ["false"]
        new_query = urlencode({k: v[0] for k, v in q.items()})
        rebuilt = parsed._replace(query=new_query)
        return rebuilt.geturl()

    all_posts: List[Post] = []
    page_urls: List[str] = []
    start = 1

    for _ in range(hard_limit_pages):
        page_url = build_url(start)
        page_urls.append(page_url)

        resp = request_get(page_url)
        posts = parse_atom_entries(resp.text)

        if not posts:
            break

        all_posts.extend(posts)
        start += max_results

    return all_posts, page_urls

# ---------------------------
# MANUAL MODE: Single Grab
# ---------------------------
def scrape_single_post(url: str) -> Post:
    """
    Generic single-page scraper:
      - title from <meta property="og:title">, <title>, or <h1>
      - content from <article> or common blog containers
      - includes images/iframes as HTML
    """
    url = safe_text(url)
    if not urlparse(url).scheme:
        url = "https://" + url

    resp = request_get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Title heuristics
    title = ""
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        title = og["content"].strip()
    if not title and soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
    title = title or "Untitled"

    # Content heuristics (best-effort)
    candidates = []
    for sel in [
        "article",
        "div.post-body",
        "div.post-content",
        "div.entry-content",
        "div.blog-posts",
        "div#post-body",
        "main",
    ]:
        el = soup.select_one(sel)
        if el:
            candidates.append(el)

    content_el = None
    if candidates:
        # pick the largest by text length
        content_el = max(candidates, key=lambda x: len(x.get_text(" ", strip=True)))
    else:
        # fallback to body
        content_el = soup.body or soup

    # Remove obvious nav/footer/sidebars inside chosen element
    for junk_sel in ["nav", "footer", "aside", ".sidebar", ".comment", "#comments", ".share", ".cookie", ".breadcrumbs"]:
        for j in content_el.select(junk_sel):
            j.decompose()

    # Make image URLs absolute
    for img in content_el.find_all("img"):
        src = img.get("src") or ""
        if src:
            img["src"] = urljoin(url, src)

    for iframe in content_el.find_all("iframe"):
        src = iframe.get("src") or ""
        if src:
            iframe["src"] = urljoin(url, src)

    # Keep a clean-ish HTML fragment
    content_html = str(content_el)

    return Post(
        title=title,
        content_html=content_html,
        source_url=url,
        updated_iso=now_iso_z(),
        post_id=f"urn:uuid:{uuid.uuid4()}",
    )

# ---------------------------
# EXPORT: Blogger Atom XML
# ---------------------------
def build_blogger_atom(posts: List[Post], blog_title: str = "Migrated Blog") -> bytes:
    """
    Blogger Import Fix requirements:
      - Every <entry> MUST include:
        <id> unique
        <updated> valid timestamp
        <control><draft>no</draft></control>
    """
    ns_atom = ATOM_NS["atom"]
    ns_app = ATOM_NS["app"]

    ET.register_namespace("", ns_atom)
    ET.register_namespace("app", ns_app)

    feed = ET.Element(f"{{{ns_atom}}}feed")
    t = ET.SubElement(feed, f"{{{ns_atom}}}title")
    t.text = blog_title

    feed_id = ET.SubElement(feed, f"{{{ns_atom}}}id")
    feed_id.text = f"urn:uuid:{uuid.uuid4()}"

    feed_updated = ET.SubElement(feed, f"{{{ns_atom}}}updated")
    feed_updated.text = now_iso_z()

    author = ET.SubElement(feed, f"{{{ns_atom}}}author")
    ET.SubElement(author, f"{{{ns_atom}}}name").text = "Personal Blog Migration Tool"

    for p in posts:
        entry = ET.SubElement(feed, f"{{{ns_atom}}}entry")

        e_title = ET.SubElement(entry, f"{{{ns_atom}}}title")
        e_title.text = p.title or "Untitled"

        e_id = ET.SubElement(entry, f"{{{ns_atom}}}id")
        e_id.text = p.post_id or f"urn:uuid:{uuid.uuid4()}"

        e_updated = ET.SubElement(entry, f"{{{ns_atom}}}updated")
        e_updated.text = p.updated_iso or now_iso_z()

        # Published (optional but helps some importers)
        e_published = ET.SubElement(entry, f"{{{ns_atom}}}published")
        e_published.text = p.updated_iso or now_iso_z()

        # Control draft -> no (publish)
        control = ET.SubElement(entry, f"{{{ns_app}}}control")
        draft = ET.SubElement(control, f"{{{ns_app}}}draft")
        draft.text = "no"

        # Content as HTML
        content = ET.SubElement(entry, f"{{{ns_atom}}}content", attrib={"type": "html"})
        content.text = p.content_html or ""

        if p.source_url:
            ET.SubElement(entry, f"{{{ns_atom}}}link", attrib={"rel": "alternate", "href": p.source_url})

    xml_bytes = ET.tostring(feed, encoding="utf-8", xml_declaration=True)
    return xml_bytes

# ---------------------------
# EXPORT: WordPress WXR (RSS)
# ---------------------------
def build_wordpress_wxr(posts: List[Post], site_title: str = "Migrated Site", site_url: str = "https://example.com") -> bytes:
    """
    Minimal WXR (WordPress eXtended RSS) compatible export.
    """
    rss = ET.Element("rss", attrib={"version": "2.0"})
    # namespaces
    for prefix, uri in WP_NS.items():
        rss.set(f"xmlns:{prefix}", uri)

    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = site_title
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = "Exported by Personal Blog Migration Tool"
    ET.SubElement(channel, "language").text = "en"

    wxr_version = ET.SubElement(channel, f"{{{WP_NS['wp']}}}wxr_version")
    wxr_version.text = "1.2"

    for p in posts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = p.title or "Untitled"
        if p.source_url:
            ET.SubElement(item, "link").text = p.source_url

        guid = ET.SubElement(item, "guid", attrib={"isPermaLink": "false"})
        guid.text = p.post_id or f"urn:uuid:{uuid.uuid4()}"

        # pubDate in RFC822
        dt = None
        try:
            dt = datetime.fromisoformat((p.updated_iso or now_iso_z()).replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
        pubdate = ET.SubElement(item, "pubDate")
        pubdate.text = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

        # creator
        dc_creator = ET.SubElement(item, f"{{{WP_NS['dc']}}}creator")
        dc_creator.text = "Personal Blog Migration Tool"

        # content:encoded
        content_encoded = ET.SubElement(item, f"{{{WP_NS['content']}}}encoded")
        content_encoded.text = p.content_html or ""

        # wp fields
        ET.SubElement(item, f"{{{WP_NS['wp']}}}post_type").text = "post"
        ET.SubElement(item, f"{{{WP_NS['wp']}}}status").text = "publish"
        ET.SubElement(item, f"{{{WP_NS['wp']}}}post_date").text = dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        ET.SubElement(item, f"{{{WP_NS['wp']}}}post_date_gmt").text = dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    return xml_bytes

# ---------------------------
# App State
# ---------------------------
if "posts" not in st.session_state:
    st.session_state.posts: List[Post] = []

if "last_fetch_log" not in st.session_state:
    st.session_state.last_fetch_log = []

# ---------------------------
# Header
# ---------------------------
st.title("🗂️ Personal Blog Migration Tool")
st.caption("Backup & migrate your own blog content between **Blogger** (Atom) and **WordPress** (WXR).")

left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.subheader("1) Collect Content")

    mode = st.radio(
        "Mode",
        ["Automated Discovery (Bulk Mode)", "Manual Mode (Single Grab)"],
        horizontal=True,
    )

    filter_mode = st.selectbox(
        "Content Filtering",
        ["Full Content", "Text Only", "Videos Only"],
        index=0,
        help="Choose what to keep inside exported posts.",
    )

    st.markdown("---")

    if mode == "Automated Discovery (Bulk Mode)":
        st.markdown("**Bulk Atom Feed URL** (example: `domain.com/atom.xml?redirect=false&start-index=1&max-results=500`)")
        feed_url = st.text_input("Atom feed URL", placeholder="yourdomain.com/atom.xml?redirect=false&start-index=1&max-results=500")

        max_results = st.select_slider("Max results per page", options=[50, 100, 150, 250, 500], value=500)
        hard_pages = st.slider("Safety cap (max pages to fetch)", min_value=1, max_value=80, value=20)

        colA, colB = st.columns([0.55, 0.45])
        with colA:
            start_fetch = st.button("🚀 Fetch posts (bulk)", use_container_width=True)
        with colB:
            clear_posts = st.button("🧹 Clear collected posts", use_container_width=True)

        if clear_posts:
            st.session_state.posts = []
            st.session_state.last_fetch_log = []
            st.success("Cleared collected posts.")

        if start_fetch and feed_url.strip():
            progress = st.progress(0, text="Starting fetch...")
            status = st.empty()

            all_posts: List[Post] = []
            page_urls: List[str] = []

            # We fetch with incremental progress approximation
            try:
                # Wrap our bulk fetch to report progress each page
                feed_url_norm = normalize_atom_feed_url(feed_url)
                parsed = urlparse(feed_url_norm)
                qs = parse_qs(parsed.query)
                base_qs = {k: v[:] for k, v in qs.items()}

                def build_url(start_index: int) -> str:
                    q = {k: v[:] for k, v in base_qs.items()}
                    q["start-index"] = [str(start_index)]
                    q["max-results"] = [str(max_results)]
                    if "redirect" not in q:
                        q["redirect"] = ["false"]
                    new_query = urlencode({k: v[0] for k, v in q.items()})
                    return parsed._replace(query=new_query).geturl()

                start_index = 1
                for page_i in range(hard_pages):
                    page_url = build_url(start_index)
                    page_urls.append(page_url)

                    status.markdown(f"Fetching page {page_i+1}/{hard_pages} …")
                    resp = request_get(page_url)
                    posts = parse_atom_entries(resp.text)
                    if not posts:
                        break

                    all_posts.extend(posts)
                    start_index += max_results

                    # progress is based on attempted pages; not perfect, but visually helpful
                    pct = int(((page_i + 1) / hard_pages) * 100)
                    progress.progress(min(pct, 100), text=f"Fetched {len(all_posts)} posts so far…")

                    # light pacing to keep UI smooth
                    time.sleep(0.05)

                # Apply filter
                cleaned: List[Post] = []
                for p in all_posts:
                    cleaned.append(Post(
                        title=p.title,
                        content_html=apply_content_filter(p.content_html, filter_mode),
                        source_url=p.source_url,
                        updated_iso=p.updated_iso or now_iso_z(),
                        post_id=p.post_id or f"urn:uuid:{uuid.uuid4()}",
                    ))

                st.session_state.posts = cleaned
                st.session_state.last_fetch_log = page_urls

                progress.progress(100, text=f"Done. Collected {len(cleaned)} posts.")
                st.success(f"Collected {len(cleaned)} posts.")
            except Exception as e:
                progress.empty()
                st.error(f"Bulk fetch failed: {e}")

    else:
        post_url = st.text_input("Post URL", placeholder="https://yourblog.com/2024/01/your-post.html")
        colA, colB = st.columns([0.55, 0.45])
        with colA:
            grab_one = st.button("🕵️ Grab this post", use_container_width=True)
        with colB:
            clear_posts = st.button("🧹 Clear collected posts", use_container_width=True)

        if clear_posts:
            st.session_state.posts = []
            st.success("Cleared collected posts.")

        if grab_one and post_url.strip():
            with st.spinner("Scraping post…"):
                try:
                    p = scrape_single_post(post_url)
                    p.content_html = apply_content_filter(p.content_html, filter_mode)
                    # Ensure required fields for export
                    p.updated_iso = p.updated_iso or now_iso_z()
                    p.post_id = p.post_id or f"urn:uuid:{uuid.uuid4()}"

                    st.session_state.posts.append(p)
                    st.success("Added 1 post to the collection.")
                except Exception as e:
                    st.error(f"Manual grab failed: {e}")

    st.markdown("---")
    st.subheader("2) Preview")

    posts = st.session_state.posts
    st.write(f"**Collected posts:** {len(posts)}")

    if posts:
        # Show a compact preview list
        with st.expander("Show titles", expanded=True):
            for i, p in enumerate(posts[:50], start=1):
                st.markdown(f"**{i}.** {html.escape(p.title)}")
            if len(posts) > 50:
                st.caption(f"Showing first 50 of {len(posts)} posts.")

        # Optional: inspect a single post
        idx = st.number_input("Inspect post #", min_value=1, max_value=len(posts), value=1, step=1)
        p = posts[int(idx) - 1]
        st.markdown(f"### {html.escape(p.title)}")
        st.caption(p.source_url or "(no source url)")
        st.markdown(p.content_html, unsafe_allow_html=True)
    else:
        st.info("No posts collected yet. Use Bulk Mode or Manual Mode to gather content.")

with right:
    st.subheader("3) Export")

    export_format = st.selectbox("Export format", ["Blogger (Atom XML)", "WordPress (WXR)"], index=0)

    site_title = st.text_input("Blog/Site title (metadata)", value="Migrated Blog")
    site_url = st.text_input("Site URL (metadata, for WXR)", value="https://example.com")

    st.markdown("---")

    if st.session_state.posts:
        # Build export bytes
        try:
            if export_format == "Blogger (Atom XML)":
                blob = build_blogger_atom(st.session_state.posts, blog_title=site_title.strip() or "Migrated Blog")
                filename = "blogger-import.xml"
                mime = "application/atom+xml"
                st.caption("Blogger export includes required `<id>`, `<updated>`, and `<app:control><app:draft>no</app:draft></app:control>` for **auto-published imports**.")
            else:
                blob = build_wordpress_wxr(
                    st.session_state.posts,
                    site_title=site_title.strip() or "Migrated Site",
                    site_url=site_url.strip() or "https://example.com",
                )
                filename = "wordpress-wxr.xml"
                mime = "application/rss+xml"
                st.caption("WXR export is a minimal RSS+WordPress namespace file compatible with WordPress importers.")

            st.download_button(
                label="⬇️ Download Export File",
                data=blob,
                file_name=filename,
                mime=mime,
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Export failed: {e}")
    else:
        st.warning("Collect at least one post to enable export.")

    st.markdown("---")
    st.subheader("Diagnostics")

    if st.session_state.last_fetch_log:
        st.caption("Last bulk page URLs fetched:")
        for u in st.session_state.last_fetch_log[:10]:
            st.code(u)
        if len(st.session_state.last_fetch_log) > 10:
            st.caption(f"(Showing first 10 of {len(st.session_state.last_fetch_log)} URLs)")

    st.markdown("---")
    st.subheader("Notes")
    st.markdown(
        """
- **Bulk Mode** expects an Atom feed that returns `<entry>` items (Blogger-style Atom works best).
- **Manual Mode** is a best-effort scraper using common blog HTML patterns (`<article>`, `.entry-content`, `.post-body`).
- If your theme uses a unique structure, update the selectors inside `scrape_single_post()`.
        """
    )
