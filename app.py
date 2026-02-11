import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re
import random
import string

# 1. KONFIGURASI HALAMAN & TAMPILAN PREMIUM
st.set_page_config(page_title="Den Abi Master Generator V12", page_icon="🚀", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    .main { background: linear-gradient(135deg, #0d0d0d, #1a1a2e); color: #ffffff; }
    input, select, .stSelectbox div { 
        color: #ffffff !important; 
        background-color: #333 !important; 
        -webkit-text-fill-color: #ffffff !important;
    }
    label { color: #ffffff !important; font-weight: bold; }
    .stButton>button { 
        width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; 
        background: linear-gradient(90deg, #5c49f5, #8e2de2); color: white; border: none;
    }
    .btn-download {
        display: block; width: 100%; padding: 15px; background: #fbc02d; 
        color: black !important; text-align: center; border-radius: 12px; 
        font-weight: bold; text-decoration: none; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 DEN ABI MASTER V12")
st.info("Fitur: Jalur Atom 500 Post, Anti-Duplikat ID, & Full Bahasa Indonesia.")

# 2. INPUT PENGGUNA
with st.container():
    target_url = st.text_input("Link Beranda (Bulk) atau Link Postingan (Single):", placeholder="https://example.blogspot.com/")
    col1, col2 = st.columns(2)
    with col1:
        output_format = st.selectbox("Format XML:", ["Blogger (Atom)", "WordPress (WXR)"])
        mode = st.selectbox("Mode Grab:", ["Semua File", "Konten Teks", "Hanya Video"])
    with col2:
        limit_post = st.number_input("Limit Postingan:", 1, 500, 10)
        grab_type = st.radio("Metode:", ["Otomatis (Bulk)", "Manual (Single)"])

# 3. LOGIKA PENGAMBILAN DATA (GRABBER)
def grab_content(url, grab_mode):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Cari Judul
        title_tag = soup.find('h1') or soup.find('h3', class_='post-title') or soup.find('title')
        title = title_tag.text.strip() if title_tag else "Tanpa Judul"
        
        content_html = ""
        # Cari Body Konten
        if grab_mode in ["Semua File", "Konten Teks"]:
            body = soup.find(class_=re.compile(r'post-body|entry-content|article-post'))
            if body: content_html += str(body)
            
        if grab_mode in ["Semua File", "Hanya Video"]:
            for f in soup.find_all('iframe'):
                if any(x in f.get('src', '').lower() for x in ['embed', 'video', 'youtube']):
                    content_html += str(f)
                    
        return title, content_html
    except:
        return None, None

def get_bulk_links(url, limit):
    base = url.rstrip('/')
    # Jalur Atom XML 500 Post sesuai permintaan
    atom_path = f"{base}/atom.xml?redirect=false&start-index=1&max-results={limit}"
    links = []
    try:
        r = requests.get(atom_path, timeout=15)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'xml')
            for entry in s.find_all('entry'):
                l = entry.find('link', rel='alternate')
                if l: links.append(l['href'])
    except: pass
    return list(set(links))

# 4. PEMBUAT XML (ANTI-ERROR & ANTI-DUPLIKAT)
def build_xml(items, format_type):
    now_iso = datetime.now().isoformat() + "Z" # Postingan jadi hari ini
    
    if format_type == "Blogger (Atom)":
        entries = ""
        for i in items:
            # Generate Random ID agar tembus Blogger
            rand_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            p_id = f"tag:blogger.com,1999:blog-{rand_id}.post-{int(datetime.now().timestamp())}"
            
            c_safe = i['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            entries += f"""
    <entry>
        <id>{p_id}</id>
        <published>{now_iso}</published>
        <updated>{now_iso}</updated>
        <category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/>
        <title type='text'>{i['title']}</title>
        <content type='html'>{c_safe}</content>
        <control xmlns='http://www.w3.org/2007/app'><draft xmlns='http://purl.org/atom/app#'>no</draft></control>
        <author><name>Den Abi Digital Store</name></author>
    </entry>"""
        return f"<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom'>{entries}</feed>"
    else:
        # Format WordPress WXR
        e = ""
        for i in items:
            e += f"<item><title>{i['title']}</title><pubDate>{now_iso}</pubDate><content:encoded><![CDATA[{i['content']}]]></content:encoded><wp:status>publish</wp:status></item>"
        return f"<?xml version='1.0' encoding='UTF-8' ?><rss version='2.0' xmlns:content='http://purl.org/rss/1.0/modules/content/' xmlns:wp='http://wordpress.org/export/1.2/'><channel><wp:wxr_version>1.2</wp:wxr_version>{e}</channel></rss>"

# 5. EKSEKUSI
if 'data_grab' not in st.session_state:
    st.session_state.data_grab = []

if st.button("🔥 GENERATE KONTEN SEKARANG"):
    if target_url:
        st.session_state.data_grab = []
        with st.spinner('Menembus sistem target...'):
            if grab_type == "Otomatis (Bulk)":
                list_links = get_bulk_links(target_url, limit_post)
                if list_links:
                    bar = st.progress(0)
                    for idx, link in enumerate(list_links):
                        t, c = grab_content(link, mode)
                        if t and c: st.session_state.data_grab.append({'title': t, 'content': c})
                        bar.progress((idx + 1) / len(list_links))
                    st.success(f"Berhasil! {len(st.session_state.data_grab)} konten siap unduh.")
                else:
                    st.error("Gagal! Jalur Atom tidak ditemukan atau blog diproteksi.")
            else:
                t, c = grab_content(target_url, mode)
                if t and c:
                    st.session_state.data_grab.append({'title': t, 'content': c})
                    st.success(f"Berhasil Manual: {t}")
    else:
        st.warning("Masukkan URL dulu Bosku!")

# 6. DOWNLOAD AREA
if st.session_state.data_grab:
    xml_out = build_xml(st.session_state.data_grab, output_format)
    b64_xml = base64.b64encode(xml_out.encode()).decode()
    st.markdown(f'<a href="data:file/xml;base64,{b64_xml}" download="DenAbi_Store_{output_format}.xml" class="btn-download">📥 DOWNLOAD {len(st.session_state.data_grab)} ITEM</a>', unsafe_allow_html=True)
    if st.button("Hapus Antrean"):
        st.session_state.data_grab = []
        st.rerun()

st.caption("Den Abi Digital Store © 2026 | Master Generator V12")
