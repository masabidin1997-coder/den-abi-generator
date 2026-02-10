import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re

# Konfigurasi Halaman
st.set_page_config(page_title="Den Abi Multi-Generator", page_icon="🚀", layout="centered")

# Custom CSS untuk tampilan premium - PERBAIKAN: Font Putih agar terbaca
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; background-color: #5c49f5; color: white; }
    .stTextInput>div>div>input { color: #ffffff !important; background-color: #333 !important; font-weight: bold; }
    .stSelectbox div div { color: #ffffff !important; }
    /* Menghilangkan Menu Github & Share */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Den Abi Multi-Generator V10")
st.info("Alat ini bekerja di sisi server. Bebas blokir CORS dan lancar di semua browser HP/Laptop.")

# Form Input
with st.container():
    target_url = st.text_input("Target URL (Beranda untuk Bulk / Post untuk Single):", placeholder="https://example.com/")
    
    col1, col2 = st.columns(2)
    with col1:
        output_format = st.selectbox("Format XML Output:", ["Blogger (Atom)", "WordPress (WXR)"])
        mode = st.selectbox("Mode Grab:", ["Semua File", "Konten Teks", "Hanya Video"])
    with col2:
        limit_post = st.number_input("Jumlah Maksimal Konten:", min_value=1, max_value=50, value=10)
        platform = st.selectbox("Tipe Website Target:", ["Auto-Detect", "WordPress", "Blogger"])

# --- FUNGSI GRABBER (TIDAK DIUBAH FUNGSINYA) ---
def perform_grab(url, platform_type, grab_mode):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Perbaikan Judul agar lebih spesifik ke postingan
        title_tag = soup.find('h1') or soup.find('h3', class_='post-title')
        title = title_tag.text.strip() if title_tag else (soup.title.string if soup.title else "No Title")
        
        final_html = ""
        if grab_mode == "Konten Teks":
            body = soup.find(class_=re.compile(r'post-body|entry-content|article-post'))
            final_html = str(body) if body else "Konten teks tidak ditemukan."
            
        elif grab_mode == "Hanya Video":
            iframes = soup.find_all('iframe')
            for f in iframes:
                src = f.get('src', '')
                if any(x in src for x in ['embed', 'video', 'player', 'youtube']):
                    final_html += str(f)
                    
        else: # Semua File
            img = soup.find("meta", property="og:image")
            img_tag = f'<img src="{img["content"]}" style="max-width:100%;"/><br/>' if img else ""
            vids = ""
            for f in soup.find_all('iframe'):
                if any(x in f.get('src', '') for x in ['embed', 'video']):
                    vids += str(f)
            body = soup.find(class_=re.compile(r'post-body|entry-content'))
            body_text = str(body) if body else ""
            final_html = f"{img_tag}\n{vids}\n{body_text}"

        return title, final_html
    except Exception as e:
        st.error(f"Gagal menarik data: {str(e)}")
        return None, None

# --- FUNGSI XML (DIPERBAIKI AGAR PUBLISHED & SUPPORT WP) ---
def generate_xml_output(items, format_type):
    now_iso = datetime.now().isoformat() + "Z"
    now_wp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if format_type == "Blogger (Atom)":
        entries = ""
        for item in items:
            # Perbaikan: Escape XML agar tidak error saat impor
            c_safe = item['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            entries += f"""
    <entry>
        <category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/>
        <title type='text'>{item['title']}</title>
        <content type='html'>{c_safe}</content>
        <published>{now_iso}</published>
        <control xmlns='http://www.w3.org/2007/app'><draft xmlns='http://purl.org/atom/app#'>no</draft></control>
        <author><name>Den Abi</name></author>
    </entry>"""
        return f"<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' xmlns:blogger='http://schemas.google.com/blogger/2008'><title type='text'>Den Abi Export</title><updated>{now_iso}</updated><generator version='7.00' uri='http://www.blogger.com'>Blogger</generator>{entries}</feed>"
    
    else: # WordPress (WXR)
        entries = ""
        for item in items:
            entries += f"""
        <item>
            <title>{item['title']}</title>
            <pubDate>{now_wp}</pubDate>
            <dc:creator>Den Abi</dc:creator>
            <content:encoded><![CDATA[{item['content']}]]></content:encoded>
            <wp:status>publish</wp:status>
            <wp:post_type>post</wp:post_type>
        </item>"""
        return f"<?xml version='1.0' encoding='UTF-8' ?><rss version='2.0' xmlns:content='http://purl.org/rss/1.0/modules/content/' xmlns:dc='http://purl.org/dc/elements/1.1/' xmlns:wp='http://wordpress.org/export/1.2/'><channel><wp:wxr_version>1.2</wp:wxr_version>{entries}</channel></rss>"

# Inisialisasi Antrean
if 'antrean' not in st.session_state:
    st.session_state.antrean = []

# Tombol Aksi
if st.button("MULAI GRAB KONTEN"):
    if target_url:
        st.session_state.antrean = [] # Reset untuk grab baru
        with st.spinner('Memproses permintaan...'):
            # Logika Bulk Grab Sederhana jika link adalah beranda
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
        xml_data = generate_xml_output(st.session_state.antrean, output_format)
        b64 = base64.b64encode(xml_data.encode()).decode()
        ext = "xml"
        href = f'<a href="data:file/xml;base64,{b64}" download="DenAbi_{output_format}_{datetime.now().strftime("%H%M%S")}.{ext}"><button style="width:100%; padding:10px; background-color:#fbc02d; color:black; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">DOWNLOAD FILE {output_format.upper()}</button></a>'
        st.markdown(href, unsafe_allow_html=True)
    
    with col_rs:
        if st.button("RESET DAFTAR"):
            st.session_state.antrean = []
            st.rerun()

st.caption("Developed by Den Abi Project © 2026")
