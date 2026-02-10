import re
import uuid
import time
import html
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dateutil import parser as dtparser
from lxml import etree

# ----------------------------
# Config
# ----------------------------
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)
REQ_TIMEOUT = 25

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "app": "http://www.w3.org/2007/app",
}

WXR_NS = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}

# ----------------------------
# UI CSS (Premium Dark + Stealth + Gold download)
# ----------------------------
PREMIUM_CSS = """
<style>
/* Background gradient */
.stApp {
  background: radial-gradient(1200px 600px at 20% 0%, rgba(35, 74, 150, 0.55), rgba(0,0,0,0) 60%),
              radial-gradient(1000px 600px at 80% 20%, rgba(20, 120, 140, 0.35), rgba(0,0,0,0) 55%),
              linear-gradient(180deg, #05070f 0%, #02030a 100%);
}

/* Global typography */
html, body, [class*="css"]  {
  color: #ffffff !important;
}

/* Labels, help, captions */
label, .stMarkdown, .stTextInput label, .stSelectbox label, .stTextArea label {
  color: #ffffff !important;
}

/* Inputs and selects */
input, textarea, .stTextInput input, .stTextArea textarea {
  background: rgba(255,255,255,0.04) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 12px !important;
}
div[data-baseweb="select"] > div {
  background: rgba(255,255,255,0.04) !important;
  color: #ffffff !important;
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}

/* Make dropdown text white */
div[data-baseweb="select"] span {
  color: #ffffff !important;
}

/* Buttons */
.stButton>button {
  background: rgba(255,255,255,0.06);
  color: #ffffff;
  border: 1px solid rgba(255,255,255,0.16);
  border-radius: 14px;
  padding: 0.55rem 1.0rem;
  transition: all .15s ease-in-out;
}
.stButton>button:hover{
  border-color: rgba(255,255,255,0.35);
  transform: translateY(-1px);
}

/* Gold Download button (Streamlit renders download button as a normal button) */
div.stDownloadButton>button {
  background: linear-gradient(180deg, #f1d36b 0%, #caa63a 100%) !important;
  color: #111111 !important;
  border: 0 !important;
  border-radius: 14px !important;
  font-weight: 700 !important;
}
div.stDownloadButton>button:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

/* Progress bar tweaks */
div[role="progressbar"] > div {
  border-radius: 999px !important;
}
div[role="progressbar"] {
  background-color: rgba(255,255,255,0.08) !important;
}

/* "Stealth Mode" - hide Streamlit header/footer/menu */
header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
/* Hide "share/github" (varies by deployment) */
a[title="View source"] {display: none !important;}
a[title="Share"] {display: none !important;}
button[title="View options"] {display: none !important;}
</style>
"""

# ----------------------------
# Helpers
# ----------------------------
def now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def iso_from_any(dt_str: str) -> str:
    """Parse many date formats and normalize to ISO8601 Z."""
    try:
        dt = dtparser.parse(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception:
        return now_iso_z()

def rfc2822_from_iso(iso_z: str) -> str:
    """Convert ISO8601 to RFC2822 for WXR pubDate."""
    try:
        dt = dtparser.parse(iso_z)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    except Exception:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

def stable_post_id(seed: str) -> str:
    """Stable-ish unique ID (Blogger import likes unique <id>)."""
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"tag:personal-migration:{h}:{uuid.uuid4().hex[:8]}"

def strip_html_to_text(html_str: str) -> str:
    soup = BeautifulSoup(html_str or "", "html.parser")
    return soup.get_text("\n", strip=True)

def keep_only_video(html_str: str) -> str:
    soup = BeautifulSoup(html_str or "", "html.parser")
    # remove everything except iframes/videos/embeds + their immediate wrappers
    for el in soup.find_all(True):
        if el.name not in {"iframe", "video", "source", "embed"}:
            # keep element if it contains any video-like tag
            if not el.find(["iframe", "video", "embed"]):
                el.decompose()
    return str(soup)

def apply_filter(content_html: str, mode: str) -> str:
    if mode == "Konten Lengkap":
        return content_html or ""
    if mode == "Hanya Teks":
        text = strip_html_to_text(content_html or "")
        # preserve line breaks into <p>
        paras = [f"<p>{html.escape(p)}</p>" for p in re.split(r"\n{2,}|\r\n{2,}", text) if p.strip()]
        return "\n".join(paras) if paras else f"<p>{html.escape(text)}</p>"
    if mode == "Hanya Video":
        return keep_only_video(content_html or "")
    return content_html or ""

def http_get(url: str) -> requests.Response:
    headers = {"User-Agent": DEFAULT_UA, "Accept": "*/*"}
    return requests.get(url, headers=headers, timeout=REQ_TIMEOUT)

def normalize_url(u: str) -> str:
    u = u.strip()
    if not u:
        return u
    if not re.match(r"^https?://", u, flags=re.I):
        u = "https://" + u
    return u

# ----------------------------
# Blogger Atom Parsing (Mass + from feed)
# ----------------------------
def parse_blogger_feed(xml_text: str) -> list[dict]:
    """
    Return list of posts from Blogger Atom feed.
    Each dict: title, content_html, link, published_iso, updated_iso, raw_id(optional).
    """
    posts = []
    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except Exception as e:
        raise ValueError(f"Gagal parse XML Atom: {e}")

    entries = root.findall("atom:entry", namespaces=ATOM_NS)
    for entry in entries:
        # Blogger often includes non-post entries. Filter by category kind=post if present.
        is_post = False
        for cat in entry.findall("atom:category", namespaces=ATOM_NS):
            term = cat.get("term", "") or ""
            if "kind#post" in term:
                is_post = True
                break
        if not is_post and entries:
            # If kind markers absent, still include (some feeds omit)
            is_post = True

        if not is_post:
            continue

        title_el = entry.find("atom:title", namespaces=ATOM_NS)
        content_el = entry.find("atom:content", namespaces=ATOM_NS)
        updated_el = entry.find("atom:updated", namespaces=ATOM_NS)
        published_el = entry.find("atom:published", namespaces=ATOM_NS)
        id_el = entry.find("atom:id", namespaces=ATOM_NS)

        link = ""
        for l in entry.findall("atom:link", namespaces=ATOM_NS):
            if l.get("rel") in (None, "", "alternate"):
                link = l.get("href", "") or link

        title = (title_el.text or "").strip() if title_el is not None else ""
        content_html = content_el.text or "" if content_el is not None else ""

        updated_iso = iso_from_any(updated_el.text) if updated_el is not None and updated_el.text else now_iso_z()
        published_iso = iso_from_any(published_el.text) if published_el is not None and published_el.text else updated_iso
        raw_id = (id_el.text or "").strip() if id_el is not None else ""

        posts.append(
            {
                "title": title,
                "content_html": content_html,
                "link": link,
                "published_iso": published_iso,
                "updated_iso": updated_iso,
                "raw_id": raw_id,
            }
        )

    return posts

def fetch_blogger_mass(feed_url_template: str, max_results: int, progress_cb=None) -> list[dict]:
    """
    Fetch atom.xml in chunks using start-index & max-results.
    feed_url_template should already include redirect=false&start-index={}&max-results={}
    """
    all_posts = []
    start = 1
    page = 0

    while True:
        page += 1
        url = feed_url_template.format(start, max_results)
        resp = http_get(url)
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code} saat ambil feed: {url}")

        posts = parse_blogger_feed(resp.text)
        if not posts:
            break

        all_posts.extend(posts)

        # progress heuristic: unknown total; just animate a bit
        if progress_cb:
            progress_cb(page, len(all_posts))

        # Blogger feed returns <= max_results each page
        if len(posts) < max_results:
            break

        start += max_results
        # be polite
        time.sleep(0.3)

    return all_posts

# ----------------------------
# Manual Single-Post Fetch (HTML)
# ----------------------------
def extract_main_html(soup: BeautifulSoup) -> str:
    """
    Heuristics: try common containers for Blogger/WP then fallback to article/body.
    """
    selectors = [
        "article",
        "div.post-body",
        "div.post-content",
        "div.entry-content",
        "div.post-content-container",
        "div#content",
        "main",
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node and node.get_text(strip=True):
            return str(node)
    body = soup.body
    return str(body) if body else str(soup)

def fetch_single_post(url: str) -> dict:
    url = normalize_url(url)
    resp = http_get(url)
    if resp.status_code != 200:
        raise ValueError(f"HTTP {resp.status_code} saat ambil posting: {url}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title heuristics
    title = ""
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        title = og["content"].strip()
    if not title:
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
    if not title and soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)

    # Content heuristics
    content_html = extract_main_html(soup)

    # Extract media (for reporting/debug)
    media = {"images": [], "videos": [], "iframes": []}
    content_soup = BeautifulSoup(content_html, "html.parser")
    for img in content_soup.find_all("img"):
        src = img.get("src") or ""
        if src:
            media["images"].append(src)
    for vid in content_soup.find_all("video"):
        media["videos"].append("video_tag")
    for ifr in content_soup.find_all("iframe"):
        src = ifr.get("src") or ""
        if src:
            media["iframes"].append(src)

    # Try published time
    published_iso = now_iso_z()
    # common meta tags
    for key in ["article:published_time", "og:updated_time"]:
        mt = soup.find("meta", property=key)
        if mt and mt.get("content"):
            published_iso = iso_from_any(mt["content"])
            break

    return {
        "title": title or "(Tanpa Judul)",
        "content_html": content_html,
        "link": url,
        "published_iso": published_iso,
        "updated_iso": published_iso,
        "raw_id": "",
        "media": media,
    }

# ----------------------------
# Export Builders
# ----------------------------
def build_blogger_atom(posts: list[dict], blog_title="Migrated Blog", blog_id_seed="") -> bytes:
    """
    Blogger Atom import feed:
    - Each <entry> MUST include unique <id>, valid <updated>, and <control><draft>no</draft></control>
    - Use <content type="html">...</content>
    """
    nsmap = {
        None: ATOM_NS["atom"],
        "app": ATOM_NS["app"],
    }

    feed = etree.Element("{http://www.w3.org/2005/Atom}feed", nsmap=nsmap)
    etree.SubElement(feed, "{http://www.w3.org/2005/Atom}title").text = blog_title
    etree.SubElement(feed, "{http://www.w3.org/2005/Atom}updated").text = now_iso_z()

    # feed id
    feed_id = stable_post_id(blog_id_seed or blog_title or "feed")
    etree.SubElement(feed, "{http://www.w3.org/2005/Atom}id").text = feed_id

    author = etree.SubElement(feed, "{http://www.w3.org/2005/Atom}author")
    etree.SubElement(author, "{http://www.w3.org/2005/Atom}name").text = "Personal Blog Migration Tool"

    for p in posts:
        entry = etree.SubElement(feed, "{http://www.w3.org/2005/Atom}entry")
        etree.SubElement(entry, "{http://www.w3.org/2005/Atom}title").text = p.get("title", "")

        # required Blogger import fields
        unique_id = stable_post_id(p.get("link", "") or p.get("title", "") or uuid.uuid4().hex)
        etree.SubElement(entry, "{http://www.w3.org/2005/Atom}id").text = unique_id

        upd = p.get("updated_iso") or now_iso_z()
        pub = p.get("published_iso") or upd
        etree.SubElement(entry, "{http://www.w3.org/2005/Atom}updated").text = iso_from_any(upd)
        etree.SubElement(entry, "{http://www.w3.org/2005/Atom}published").text = iso_from_any(pub)

        # category kind#post for Blogger
        cat = etree.SubElement(entry, "{http://www.w3.org/2005/Atom}category")
        cat.set("scheme", "http://schemas.google.com/g/2005#kind")
        cat.set("term", "http://schemas.google.com/blogger/2008/kind#post")

        # content html
        content = etree.SubElement(entry, "{http://www.w3.org/2005/Atom}content")
        content.set("type", "html")
        content.text = p.get("content_html", "") or ""

        # alternate link if available
        link = p.get("link", "")
        if link:
            l = etree.SubElement(entry, "{http://www.w3.org/2005/Atom}link")
            l.set("rel", "alternate")
            l.set("type", "text/html")
            l.set("href", link)

        # control draft = no (Published)
        control = etree.SubElement(entry, "{http://www.w3.org/2007/app}control")
        draft = etree.SubElement(control, "{http://www.w3.org/2007/app}draft")
        draft.text = "no"

    xml_bytes = etree.tostring(feed, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return xml_bytes

def build_wordpress_wxr(posts: list[dict], site_title="Migrated Blog", site_url="https://example.com") -> bytes:
    """
    Minimal WXR (WordPress eXtended RSS) for import.
    """
    rss = etree.Element("rss", version="2.0", nsmap=WXR_NS)

    channel = etree.SubElement(rss, "channel")
    etree.SubElement(channel, "title").text = site_title
    etree.SubElement(channel, "link").text = site_url
    etree.SubElement(channel, "description").text = "Exported by Personal Blog Migration Tool"

    etree.SubElement(channel, f"{{{WXR_NS['wp']}}}wxr_version").text = "1.2"

    for idx, p in enumerate(posts, start=1):
        item = etree.SubElement(channel, "item")
        etree.SubElement(item, "title").text = p.get("title", "")

        link = p.get("link", "") or f"{site_url.rstrip('/')}/?p={idx}"
        etree.SubElement(item, "link").text = link

        upd = iso_from_any(p.get("updated_iso") or now_iso_z())
        etree.SubElement(item, "pubDate").text = rfc2822_from_iso(upd)

        creator = etree.SubElement(item, f"{{{WXR_NS['dc']}}}creator")
        creator.text = "Personal Blog Migration Tool"

        content = etree.SubElement(item, f"{{{WXR_NS['content']}}}encoded")
        # WXR expects CDATA often; lxml: use etree.CDATA
        content.text = etree.CDATA(p.get("content_html", "") or "")

        post_id = etree.SubElement(item, f"{{{WXR_NS['wp']}}}post_id")
        post_id.text = str(idx)

        post_date = etree.SubElement(item, f"{{{WXR_NS['wp']}}}post_date")
        # wp expects local time; we use UTC formatted without tz
        dt = dtparser.parse(upd).astimezone(timezone.utc)
        post_date.text = dt.strftime("%Y-%m-%d %H:%M:%S")

        post_date_gmt = etree.SubElement(item, f"{{{WXR_NS['wp']}}}post_date_gmt")
        post_date_gmt.text = dt.strftime("%Y-%m-%d %H:%M:%S")

        status = etree.SubElement(item, f"{{{WXR_NS['wp']}}}status")
        status.text = "publish"

        ptype = etree.SubElement(item, f"{{{WXR_NS['wp']}}}post_type")
        ptype.text = "post"

        # Optional: set to open
        comment_status = etree.SubElement(item, f"{{{WXR_NS['wp']}}}comment_status")
        comment_status.text = "open"
        ping_status = etree.SubElement(item, f"{{{WXR_NS['wp']}}}ping_status")
        ping_status.text = "open"

    xml_bytes = etree.tostring(rss, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return xml_bytes

# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(
    page_title="Personal Blog Migration Tool",
    page_icon="🧳",
    layout="wide",
)

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

st.title("🧳 Personal Blog Migration Tool")
st.caption("Backup & migrasi konten blog pribadi antara Blogger ↔ WordPress dengan output Blogger Atom atau WordPress WXR.")

with st.sidebar:
    st.subheader("⚙️ Mode & Opsi")
    mode = st.selectbox("Mode Pengambilan", ["Penemuan Otomatis (Massal) - Blogger Atom", "Mode Manual (Ambil Satuan)"])
    content_filter = st.selectbox("Filter Konten", ["Konten Lengkap", "Hanya Teks", "Hanya Video"])
    export_format = st.selectbox("Format Ekspor", ["Blogger (Atom XML)", "WordPress (WXR)"])

    st.divider()
    st.subheader("🧾 Metadata Ekspor")
    out_title = st.text_input("Judul Blog/Channel Ekspor", value="Migrated Blog")
    out_site_url = st.text_input("Site URL (untuk WXR)", value="https://example.com")
    polite_delay = st.slider("Delay antar request (detik)", 0.0, 2.0, 0.3, 0.1)

st.write("")

if "posts" not in st.session_state:
    st.session_state["posts"] = []

# allow changing polite delay globally
def sleep_polite():
    d = float(polite_delay)
    if d > 0:
        time.sleep(d)

colA, colB = st.columns([1.1, 0.9], gap="large")

with colA:
    st.subheader("📥 Input")
    if mode.startswith("Penemuan Otomatis"):
        st.markdown(
            "Masukkan domain atau URL feed Atom Blogger. Tool akan melakukan paging otomatis via `start-index` & `max-results`."
        )
        domain = st.text_input("Domain (contoh: domain.com) atau URL Atom feed", value="domain.com")
        max_results = st.number_input("max-results per halaman", min_value=50, max_value=500, value=500, step=50)
        start_index = 1  # keep fixed; we will paginate

        # Build template
        domain_or_url = domain.strip()
        if "atom.xml" in domain_or_url:
            base = normalize_url(domain_or_url)
            # If user already provided params, normalize to template:
            # We'll override start-index/max-results if present.
            if "?" in base:
                base = base.split("?")[0]
            feed_template = f"{base}?redirect=false&start-index={{}}&max-results={{}}"
        else:
            base = normalize_url(domain_or_url).rstrip("/")
            feed_template = f"{base}/atom.xml?redirect=false&start-index={{}}&max-results={{}}"

        st.code(feed_template.format(start_index, int(max_results)), language="text")

        fetch_btn = st.button("🚀 Ambil Postingan Massal")

        if fetch_btn:
            try:
                prog = st.progress(0)
                status = st.empty()

                def progress_cb(page, total):
                    # We don't know total; we animate within 0..95% while fetching
                    val = min(95, 10 + page * 10)
                    prog.progress(val / 100.0)
                    status.write(f"Sedang mengambil halaman #{page} • total terkumpul: **{total}** posting…")

                # temporarily set global sleep delay by monkeypatching time.sleep usage around loop
                # (we keep the original 0.3 in fetch_blogger_mass but add extra polite delay here)
                posts = []
                start = 1
                page = 0
                while True:
                    page += 1
                    url = feed_template.format(start, int(max_results))
                    resp = http_get(url)
                    if resp.status_code != 200:
                        raise ValueError(f"HTTP {resp.status_code} saat ambil feed: {url}")

                    batch = parse_blogger_feed(resp.text)
                    if not batch:
                        break

                    posts.extend(batch)
                    progress_cb(page, len(posts))

                    if len(batch) < int(max_results):
                        break

                    start += int(max_results)
                    sleep_polite()

                # Apply filter
                for p in posts:
                    p["content_html"] = apply_filter(p.get("content_html", ""), content_filter)

                st.session_state["posts"] = posts
                prog.progress(1.0)
                status.success(f"Selesai. Total posting ditemukan: **{len(posts)}**")
            except Exception as e:
                st.error(str(e))

    else:
        st.markdown("Ambil satu postingan dari URL tertentu (Blogger/WordPress/umum).")
        post_url = st.text_input("URL Postingan", value="")
        fetch_one_btn = st.button("🎯 Ambil Postingan Ini")

        if fetch_one_btn:
            try:
                prog = st.progress(0)
                status = st.empty()
                status.write("Mengambil halaman…")
                prog.progress(0.25)

                post = fetch_single_post(post_url)
                prog.progress(0.65)

                post["content_html"] = apply_filter(post.get("content_html", ""), content_filter)
                prog.progress(0.85)

                st.session_state["posts"] = [post]
                prog.progress(1.0)
                status.success("Selesai ambil 1 posting.")
            except Exception as e:
                st.error(str(e))

with colB:
    st.subheader("🧠 Preview & Ekspor")

    posts = st.session_state.get("posts", [])
    if not posts:
        st.info("Belum ada posting yang diambil. Jalankan mode Massal atau Manual terlebih dulu.")
    else:
        st.write(f"Total siap diekspor: **{len(posts)}**")
        # Preview first few
        with st.expander("🔎 Preview 3 posting pertama", expanded=True):
            for p in posts[:3]:
                st.markdown(f"**{p.get('title','(Tanpa Judul)')}**")
                if p.get("link"):
                    st.caption(p.get("link"))
                st.markdown(p.get("content_html", "")[:1200] + ("…" if len(p.get("content_html", "")) > 1200 else ""), unsafe_allow_html=True)
                st.divider()

        # Build export
        if export_format.startswith("Blogger"):
            out_bytes = build_blogger_atom(posts, blog_title=out_title, blog_id_seed=out_title)
            mime = "application/xml"
            filename = "blogger_import.atom.xml"
        else:
            out_bytes = build_wordpress_wxr(posts, site_title=out_title, site_url=out_site_url)
            mime = "application/xml"
            filename = "wordpress_import.wxr.xml"

        st.download_button(
            label="⬇️ Download File Ekspor",
            data=out_bytes,
            file_name=filename,
            mime=mime,
            use_container_width=True,
        )

        st.caption("Tips: untuk WordPress, impor via Tools → Import → WordPress (WXR). Untuk Blogger, impor via Settings/Import & Back up.")
