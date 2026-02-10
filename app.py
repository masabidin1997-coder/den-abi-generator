import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Den Abi Master Generator V11", page_icon="🚀", layout="centered")

# Custom CSS Premium & Hide Streamlit Elements
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .main { background-color: #1a1a1a; color: #ffffff; }
    /* Paksa Font Putih di Semua Input */
    input, select, .stSelectbox div { 
        color: #ffffff !important; 
        background-color: #333 !important; 
        -webkit-text-fill-color: #ffffff !important;
    }
    label { color: #ffffff !important; }
    
    .stButton>button { 
        width: 100%; border-radius: 8px; font-weight: bold; height: 3em; 
        background-color: #5c49f5; color: white; border: none;
    }
    .btn-download {
        display: block; width: 100%; padding: 10px; background-color: #fbc02d; 
        color: black !important; text-align: center; border-radius: 8px; 
        font-weight: bold; text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Den Abi Master Generator V11")
st.info("Mode: Jalur Atom XML (Max 500 Post) & Single Grab Manual.")

# --- AREA INPUT ---
with st.container():
    target_url = st.text_input("Target URL (Masukkan Link Beranda atau Link Postingan):", placeholder="https://example.blogspot.com/")
    
    col1, col2 = st.columns(2)
    with col1:
        output_format = st.selectbox("Format XML Output:", ["Blogger (Atom)", "WordPress (WXR)"])
        mode = st.selectbox("Mode Grab:", ["Semua File", "Konten Teks", "Hanya Video"])
    with col2:
        limit_post = st.number_input("Limit Post (Bulk):", min_value=1, max_value=500, value=10)
        grab_type = st.radio("Metode Grab:", ["Otomatis (Bulk)", "Manual (Single)"])

# --- FUNGSI CORE GRABBER ---
def perform_grab(url, grab_mode):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        title_tag = soup.find('h1') or soup.find('h3', class_='post-title') or soup.find('title')
        title = title_tag.text.strip() if title_tag else "No Title"
        
        final_html = ""
        # Filter Konten berdasarkan Mode
        if grab_mode in ["Semua File", "Hanya Konten Teks"]:
            body = soup.find(class_=re.compile(r'post-body|entry-content|article-post'))
            if body: final_html += str(body)
            
        if grab_mode in ["Semua File", "Hanya Video"]:
            iframes = soup.find_all('iframe')
            for f in iframes:
                if any(x in f.get('src', '').lower() for x in ['embed', 'video', 'youtube']):
                    final_html += str(f)
                    
        if grab_mode == "Semua File":
            img = soup.find("meta", property="og:image")
            if img: final_html = f'<img src="{img["content"]}" style="width:100%;"/><br/>' + final_html

        return title, final_html
    except:
        return None, None

# --- FUNGSI JALUR ATOM (BULK) ---
def get_atom_links(url, limit):
    base = url.rstrip('/')
    atom_url = f"{base}/atom.xml?redirect=false&start-index=1&max-results={limit}"
    links = []
    try:
        r = requests.get(atom_url, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'xml')
            entries = soup.find_all('entry')
            for entry in entries:
                link_tag = entry.find('link', rel='alternate')
                if link_tag: links.append(link_tag['href'])
    except: pass
    return list(set(links))

# --- FUNGSI XML GENERATOR ---
def generate_xml_output(items, format_type):
    now_iso = datetime.now().isoformat() + "Z"
    
    if format_type == "Blogger (Atom)":
        entries = ""
        for i in items:
            # Escape XML agar konten HTML tidak rusak
            c_safe = i['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Membuat ID Unik agar Blogger mengenali ini sebagai postingan baru
            post_id = f"tag:blogger.com,1999:blog-denabi.{int(datetime.now().timestamp())}"
            
            entries += f"""
    <entry>
        <id>{post_id}</id>
        <published>{now_iso}</published>
        <updated>{now_iso}</updated>
        <category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/>
        <title type='text'>{i['title']}</title>
        <content type='html'>{c_safe}</content>
        <link rel='edit' type='application/atom+xml' href='#'/>
        <link rel='self' type='application/atom+xml' href='#'/>
        <link rel='alternate' type='text/html' href='http://www.prostream.my.id/'/>
        <author><name>Den Abi</name></author>
        <control xmlns='http://www.w3.org/2007/app'><draft xmlns='http://purl.org/atom/app#'>no</draft></control>
    </entry>"""
        
        # Header XML Blogger harus Lengkap
        return f"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom' xmlns:blogger='http://schemas.google.com/blogger/2008' xmlns:thr='http://purl.org/syndication/thread/1.0'>
<id>tag:blogger.com,1999:blog-denabi.archive</id>
<updated>{now_iso}</updated>
<title type='text'>Den Abi Master Export</title>
<generator version='7.00' uri='http://www.blogger.com'>Blogger</generator>
{entries}
</feed>"""
    
    else: # WordPress Tetap
        entries = ""
        for i in items:
            entries += f"<item><title>{i['title']}</title><pubDate>{now_iso}</pubDate><content:encoded><![CDATA[{i['content']}]]></content:encoded><wp:status>publish</wp:status></item>"
        return f"<?xml version='1.0' encoding='UTF-8' ?><rss version='2.0' xmlns:content='http://purl.org/rss/1.0/modules/content/' xmlns:wp='http://wordpress.org/export/1.2/'><channel><wp:wxr_version>1.2</wp:wxr_version>{entries}</channel></rss>"

# --- EKSEKUSI ---
if 'antrean' not in st.session_state:
    st.session_state.antrean = []

if st.button("🔥 MULAI EKSEKUSI GENERATOR"):
    if target_url:
        st.session_state.antrean = []
        with st.spinner('Sedang memproses jalur Atom...'):
            if grab_type == "Otomatis (Bulk)":
                links = get_atom_links(target_url, limit_post)
                if links:
                    p_bar = st.progress(0)
                    for idx, l in enumerate(links):
                        t, c = perform_grab(l, mode)
                        if t and c: st.session_state.antrean.append({'title': t, 'content': c})
                        p_bar.progress((idx + 1) / len(links))
                    st.success(f"Berhasil mengumpulkan {len(st.session_state.antrean)} postingan!")
                else:
                    st.error("Gagal mendeteksi jalur Atom. Pastikan URL adalah Beranda Blog.")
            else:
                t, c = perform_grab(target_url, mode)
                if t and c:
                    st.session_state.antrean.append({'title': t, 'content': c})
                    st.success(f"Berhasil Manual Grab: {t}")
    else:
        st.warning("Masukkan URL terlebih dahulu!")

# --- DOWNLOAD AREA ---
st.write("---")
if st.session_state.antrean:
    xml_data = generate_xml_output(st.session_state.antrean, output_format)
    b64 = base64.b64encode(xml_data.encode()).decode()
    st.markdown(f'<a href="data:file/xml;base64,{b64}" download="DenAbi_V11_{output_format}.xml" class="btn-download">📥 DOWNLOAD {len(st.session_state.antrean)} ITEM ({output_format})</a>', unsafe_allow_html=True)
    if st.button("RESET DAFTAR"):
        st.session_state.antrean = []
        st.rerun()

st.caption("Developed by Den Abi Project © 2026 | Atom XML Path V11")

