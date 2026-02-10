import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re

# Konfigurasi Halaman
st.set_page_config(page_title="Den Abi Multi-Generator", page_icon="🚀", layout="centered")

# Custom CSS untuk tampilan premium
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; background-color: #5c49f5; color: white; }
    .stTextInput>div>div>input { color: #000000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Den Abi Multi-Generator V5")
st.info("Alat ini bekerja di sisi server. Bebas blokir CORS dan lancar di semua browser HP/Laptop.")

# Form Input
with st.container():
    target_url = st.text_input("Target URL:", placeholder="https://example.com/post-link")
    
    col1, col2 = st.columns(2)
    with col1:
        platform = st.selectbox("Tipe Website:", ["Auto-Detect", "WordPress", "Blogger"])
    with col2:
        mode = st.selectbox("Mode Grab:", ["Semua File", "Konten Teks", "Hanya Video"])

# Fungsi Grabber
def perform_grab(url, platform_type, grab_mode):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Penentuan Judul
        title = soup.find('h1').text.strip() if soup.find('h1') else (soup.title.string if soup.title else "No Title")
        
        # Logika Pengambilan Konten
        final_html = ""
        
        if grab_mode == "Konten Teks":
            # Mencari kontainer konten umum
            body = soup.find(class_=re.compile(r'post-body|entry-content|article-post'))
            final_html = str(body) if body else "Konten teks tidak ditemukan."
            
        elif grab_mode == "Hanya Video":
            iframes = soup.find_all('iframe')
            for f in iframes:
                src = f.get('src', '')
                if any(x in src for x in ['embed', 'video', 'player', 'bebas']):
                    final_html += str(f)
                    
        else: # Semua File
            img = soup.find("meta", property="og:image")
            img_tag = f'<img src="{img["content"]}" style="max-width:100%;"/><br/>' if img else ""
            vids = ""
            for f in soup.find_all('iframe'):
                if any(x in f.get('src', '') for x in ['embed', 'video']):
                    vids += str(f)
            final_html = f"{img_tag}\n{vids}"

        return title, final_html
    except Exception as e:
        st.error(f"Gagal menarik data: {str(e)}")
        return None, None

# Fungsi Membuat XML Blogger Valid
def generate_xml(items):
    now = datetime.now().isoformat() + "Z"
    entries = ""
    for item in items:
        post_id = int(datetime.now().timestamp() * 1000)
        entries += f"""
    <entry>
        <category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/>
        <title type='text'>{item['title']}</title>
        <content type='html'>{item['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</content>
        <published>{now}</published>
        <author><name>Den Abi</name></author>
    </entry>"""
    
    xml_full = f"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom' xmlns:blogger='http://schemas.google.com/blogger/2008'>
    <title type='text'>Den Abi Export</title>
    <updated>{now}</updated>
    <generator version='7.00' uri='http://www.blogger.com'>Blogger</generator>
    {entries}
</feed>"""
    return xml_full

# Inisialisasi Antrean di Session State
if 'antrean' not in st.session_state:
    st.session_state.antrean = []

# Tombol Aksi
if st.button("MULAI GRAB KONTEN"):
    if target_url:
        with st.spinner('Server sedang memproses...'):
            t, c = perform_grab(target_url, platform, mode)
            if t and c:
                st.session_state.antrean.append({'title': t, 'content': c})
                st.success(f"Berhasil menambahkan: {t}")
    else:
        st.warning("Masukkan URL terlebih dahulu!")

# Tampilan Antrean & Download
st.write("---")
st.subheader(f"📊 Antrean XML: {len(st.session_state.antrean)} Item")

if len(st.session_state.antrean) > 0:
    col_dl, col_rs = st.columns(2)
    with col_dl:
        xml_output = generate_xml(st.session_state.antrean)
        b64 = base64.b64encode(xml_output.encode()).decode()
        href = f'<a href="data:file/xml;base64,{b64}" download="DenAbi_AGC_{datetime.now().strftime("%d%m%y")}.xml"><button style="width:100%; padding:10px; background-color:#fbc02d; color:black; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">DOWNLOAD FILE .XML</button></a>'
        st.markdown(href, unsafe_allow_html=True)
    
    with col_rs:
        if st.button("RESET DAFTAR"):
            st.session_state.antrean = []
            st.rerun()

st.caption("Developed by Den Abi Project © 2026")
