import re
import math
import json
import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl

import streamlit as st
import requests
import xml.etree.ElementTree as ET


# =========================
# Utils
# =========================
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
}

DEFAULT_MAX_RESULTS = 500

def normalize_blog_url(raw: str) -> str:
    """
    Accepts:
      - https://example.com
      - example.com
      - example.blogspot.com
    Returns normalized base URL with scheme and no trailing slash.
    """
    s = (raw or "").strip()
    if not s:
        return ""
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    p = urlparse(s)
    # Remove path/query/fragment, keep netloc
    netloc = p.netloc.strip()
    if not netloc:
        return ""
    return f"{p.scheme}://{netloc}"

def build_atom_url(
    blog_base: str,
    start_index: int = 1,
    max_results: int = DEFAULT_MAX_RESULTS,
    redirect_false: bool = True,
) -> str:
    """
    Build: https://domain/atom.xml?redirect=false&start-index=1&max-results=500
    """
    base = normalize_blog_url(blog_base)
    if not base:
        return ""

    path = "/atom.xml"
    query_items = []
    if redirect_false:
        query_items.append(("redirect", "false"))
    query_items.extend([
        ("start-index", str(start_index)),
        ("max-results", str(max_results)),
    ])
    query = urlencode(query_items)

    p = urlparse(base)
    return urlunparse((p.scheme, p.netloc, path, "", query, ""))

def chunk_start_indices(total_posts: int, max_results: int) -> List[int]:
    """
    Returns [1, 1+max_results, 1+2*max_results, ...]
    """
    if total_posts <= 0:
        return [1]
    batches = math.ceil(total_posts / max_results)
    return [1 + i * max_results for i in range(batches)]

def safe_int(x: str, default: int, min_v: int, max_v: int) -> int:
    try:
        v = int(str(x).strip())
    except Exception:
        v = default
    return max(min_v, min(max_v, v))

@dataclass
class FeedEntry:
    title: str
    link: str
    published: Optional[str] = None
    updated: Optional[str] = None

def parse_atom_feed(xml_text: str) -> Tuple[Optional[str], List[FeedEntry]]:
    """
    Parse Atom XML and return (feed_title, entries).
    """
    root = ET.fromstring(xml_text)
    feed_title_el = root.find("atom:title", ATOM_NS)
    feed_title = feed_title_el.text.strip() if feed_title_el is not None and feed_title_el.text else None

    entries: List[FeedEntry] = []
    for e in root.findall("atom:entry", ATOM_NS):
        title_el = e.find("atom:title", ATOM_NS)
        title = title_el.text.strip() if title_el is not None and title_el.text else "(no title)"

        link = ""
        for l in e.findall("atom:link", ATOM_NS):
            # prefer rel="alternate"
            rel = l.attrib.get("rel", "")
            href = l.attrib.get("href", "")
            if rel == "alternate" and href:
                link = href
                break
            if not link and href:
                link = href

        pub_el = e.find("atom:published", ATOM_NS)
        upd_el = e.find("atom:updated", ATOM_NS)
        published = pub_el.text.strip() if pub_el is not None and pub_el.text else None
        updated = upd_el.text.strip() if upd_el is not None and upd_el.text else None

        entries.append(FeedEntry(title=title, link=link, published=published, updated=updated))

    return feed_title, entries

def fetch_feed(url: str, timeout_s: int = 15) -> Tuple[int, str]:
    """
    Returns (status_code, body_text). Raises for network errors.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Streamlit AGC Tool; +https://streamlit.io)",
        "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=timeout_s)
    return r.status_code, r.text

def entries_to_csv(entries: List[FeedEntry]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["title", "link", "published", "updated"])
    for e in entries:
        writer.writerow([e.title, e.link, e.published or "", e.updated or ""])
    return output.getvalue().encode("utf-8")

def entries_to_json(entries: List[FeedEntry]) -> bytes:
    data = [{
        "title": e.title,
        "link": e.link,
        "published": e.published,
        "updated": e.updated,
    } for e in entries]
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


# =========================
# UI
# =========================
st.set_page_config(
    page_title="Blogger Atom Feed Builder",
    page_icon="🧭",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
      .stTabs [data-baseweb="tab-list"] { gap: 6px; }
      .stTabs [data-baseweb="tab"] { padding-left: 14px; padding-right: 14px; }
      .card {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 14px;
        padding: 14px 16px;
        background: rgba(255,255,255,0.02);
      }
      .muted { opacity: 0.75; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧭 Blogger Atom Feed Builder")
st.write("Bangun URL Atom (`atom.xml`) dengan parameter rapi, generate batch sitemap, preview entries, dan export data.")

with st.sidebar:
    st.header("⚙️ Konfigurasi")
    blog_input = st.text_input(
        "Base Blog URL",
        value="https://namablogkamu.blogspot.com",
        help="Bisa pakai custom domain atau blogspot. Contoh: https://example.com atau example.blogspot.com",
    )

    redirect_false = st.toggle("Gunakan redirect=false", value=True, help="Biasanya dipakai agar URL konsisten.")
    max_results = st.number_input(
        "max-results",
        min_value=1,
        max_value=500,
        value=DEFAULT_MAX_RESULTS,
        step=1,
        help="Blogger Atom feed biasanya efektif sampai 500 per request.",
    )

    st.divider()
    st.subheader("Batch Generator")
    batch_mode = st.radio(
        "Mode batch",
        ["Berdasarkan total posting", "Berdasarkan jumlah batch"],
        index=0,
        help="Untuk blog besar, pecah menjadi beberapa URL start-index.",
    )
    if batch_mode == "Berdasarkan total posting":
        total_posts = st.number_input("Perkiraan total posting", min_value=1, max_value=200000, value=1200, step=1)
        batch_count = math.ceil(total_posts / max_results)
    else:
        batch_count = st.number_input("Jumlah batch", min_value=1, max_value=1000, value=3, step=1)
        total_posts = int(batch_count * max_results)

    st.caption(f"Estimasi batch: **{batch_count}** (max-results={max_results}).")

    st.divider()
    preview_limit = st.number_input("Preview ambil berapa batch?", min_value=1, max_value=20, value=2, step=1)
    timeout_s = st.number_input("Timeout fetch (detik)", min_value=5, max_value=60, value=15, step=1)

# Normalize blog url
blog_base = normalize_blog_url(blog_input)

# Top cards
c1, c2, c3 = st.columns([1.2, 1, 1])
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Base URL (normalized)**")
    st.markdown(f'<div class="mono">{blog_base or "—"}</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Contoh final: <span class="mono">/atom.xml?redirect=false&start-index=1&max-results=500</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Konfigurasi**")
    st.write(f"- redirect=false: `{redirect_false}`")
    st.write(f"- max-results: `{int(max_results)}`")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Batch**")
    st.write(f"- Total posting (estimasi): `{int(total_posts)}`")
    st.write(f"- Jumlah batch: `{int(batch_count)}`")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

tabs = st.tabs(["URL Builder", "Batch URLs", "Preview & Export", "Tips Import/Search Console"])

# =========================
# Tab 1: URL Builder
# =========================
with tabs[0]:
    st.subheader("🔧 URL Builder")

    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        start_index = st.number_input("start-index", min_value=1, max_value=200000, value=1, step=1)
    with colB:
        st.write("")
        st.write("")
        single_url = build_atom_url(
            blog_base=blog_base,
            start_index=int(start_index),
            max_results=int(max_results),
            redirect_false=redirect_false,
        )
    with colC:
        st.write("")
        st.write("")
        copy_help = "Copy manual dari field ini (Streamlit Cloud kadang tidak support clipboard direct)."

    st.markdown("**URL hasil**")
    st.text_input(" ", value=single_url, label_visibility="collapsed", help=copy_help)

    st.caption("Gunakan URL ini untuk cek feed, atau submit sebagai sitemap alternatif (tergantung kebutuhan).")

# =========================
# Tab 2: Batch URLs
# =========================
with tabs[1]:
    st.subheader("🧩 Batch URLs (Multi start-index)")

    if not blog_base:
        st.warning("Isi Base Blog URL dulu di sidebar.")
    else:
        starts = chunk_start_indices(int(total_posts), int(max_results))
        urls = [
            build_atom_url(blog_base, s, int(max_results), redirect_false)
            for s in starts
        ]

        st.write(f"Total URL batch: **{len(urls)}**")
        st.markdown("**Daftar URL**")
        st.code("\n".join(urls), language="text")

        st.download_button(
            "Download daftar URL (.txt)",
            data=("\n".join(urls)).encode("utf-8"),
            file_name="atom-batch-urls.txt",
            mime="text/plain",
        )

# =========================
# Tab 3: Preview & Export
# =========================
with tabs[2]:
    st.subheader("👀 Preview Feed & Export")

    if not blog_base:
        st.warning("Isi Base Blog URL dulu di sidebar.")
    else:
        starts = chunk_start_indices(int(total_posts), int(max_results))
        starts_preview = starts[: int(preview_limit)]
        preview_urls = [
            build_atom_url(blog_base, s, int(max_results), redirect_false)
            for s in starts_preview
        ]

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("**URL yang akan di-fetch (preview)**")
            st.code("\n".join(preview_urls), language="text")
        with col2:
            st.markdown("**Aksi**")
            do_preview = st.button("Fetch & Preview", type="primary")

        if "preview_entries" not in st.session_state:
            st.session_state.preview_entries = []
        if "preview_meta" not in st.session_state:
            st.session_state.preview_meta = {}

        if do_preview:
            all_entries: List[FeedEntry] = []
            meta = {"fetched": [], "errors": []}

            with st.spinner("Mengambil feed..."):
                for u in preview_urls:
                    try:
                        status, body = fetch_feed(u, timeout_s=int(timeout_s))
                        meta["fetched"].append({"url": u, "status": status})
                        if status >= 400:
                            meta["errors"].append({"url": u, "status": status, "message": "HTTP error"})
                            continue
                        feed_title, entries = parse_atom_feed(body)
                        # attach feed title if available
                        if feed_title and "feed_title" not in meta:
                            meta["feed_title"] = feed_title
                        all_entries.extend(entries)
                    except Exception as e:
                        meta["errors"].append({"url": u, "status": None, "message": str(e)})

            st.session_state.preview_entries = all_entries
            st.session_state.preview_meta = meta

        meta = st.session_state.get("preview_meta", {})
        entries: List[FeedEntry] = st.session_state.get("preview_entries", [])

        if meta:
            st.markdown("### Status Fetch")
            st.write(f"Feed title: **{meta.get('feed_title','(tidak terdeteksi)')}**")
            st.write(f"Total entries terkumpul: **{len(entries)}**")

            if meta.get("errors"):
                st.warning("Sebagian request gagal. Lihat detail di bawah.")
                st.json(meta["errors"], expanded=False)

        if entries:
            # Show a clean table-like view
            st.markdown("### Entries (preview)")
            # Build rows
            rows = []
            for e in entries[: min(len(entries), 2000)]:  # safety cap
                rows.append({
                    "Title": e.title,
                    "Link": e.link,
                    "Published": e.published or "",
                    "Updated": e.updated or "",
                })
            st.dataframe(rows, use_container_width=True, height=420)

            # Exports
            colx, coly, colz = st.columns([1, 1, 1])
            with colx:
                st.download_button(
                    "Download CSV",
                    data=entries_to_csv(entries),
                    file_name="atom-preview-entries.csv",
                    mime="text/csv",
                )
            with coly:
                st.download_button(
                    "Download JSON",
                    data=entries_to_json(entries),
                    file_name="atom-preview-entries.json",
                    mime="application/json",
                )
            with colz:
                # Also offer a cleaned list of post URLs
                links = [e.link for e in entries if e.link]
                st.download_button(
                    "Download Links (.txt)",
                    data=("\n".join(links)).encode("utf-8"),
                    file_name="atom-post-links.txt",
                    mime="text/plain",
                )
        else:
            st.info("Belum ada preview. Klik **Fetch & Preview** untuk melihat isi feed.")

# =========================
# Tab 4: Tips
# =========================
with tabs[3]:
    st.subheader("💡 Tips Pemakaian")
    st.markdown(
        """
- **Untuk blog besar**, gunakan **Batch URLs** lalu submit beberapa `start-index` agar mencakup semua posting.
- Kalau feed sulit diakses (HTTP 403/404):
  - pastikan blog tidak private,
  - coba pakai custom domain vs blogspot,
  - cek apakah ada proteksi / firewall / setting.
- `max-results=500` biasanya paling efisien (lebih besar dari itu tidak selalu didukung).
- Preview ini menampilkan **judul/link/tanggal** dari Atom. Cocok untuk audit cepat atau export daftar URL posting.
        """
    )
