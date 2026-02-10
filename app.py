import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Den Abi Master Generator V11", 
    page_icon="🚀", 
    layout="centered"
)

# 2. TAMPILAN PREMIUM & SEMBUNYIKAN MENU BAWAAN
st.markdown("""
    <style>
    /* Sembunyikan Menu GitHub, Share, dan Header Streamlit */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Background Gelap Gradasi */
    .stApp {
        background: linear-gradient(135deg, #0d0d0d, #1a1a2e, #16213e);
        color: #ffffff;
    }
    
    /* Paksa Font Putih di Semua Input */
    input, select, .stSelectbox div {
        background-color: #252525 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border-radius: 10px !important;
    }
    
    label { color: #ffffff !important; font-weight: bold; }

    /* Tombol Utama */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 800;
        height: 3.8em;
        background: linear-gradient(90deg, #5c49f5, #8e2de2);
        color: white;
        border: none;
        box-shadow: 0px 4px 15px rgba(92, 73, 245, 0.4);
    }

    /* Tombol Download Kuning Emas */
    .btn-download {
        display: block;
        width: 100%;
        padding: 15px;
        background: linear-gradient(45deg, #fbc02d, #f57f17);
        color: #000 !important;
        text-align: center;
        border-radius: 12px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #5c49f5;'>🚀 DEN ABI MASTER GENERATOR V11</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.8;'>Alat Migrasi Konten Blog Profesional (Blogger & WordPress)</p>", unsafe_allow_html=True)

# 3. AREA KONFIGURASI
with st.container():
    st.markdown("### 🛠️ Pengaturan Konten")
    target_url = st.text_input("Link Beranda atau Link Postingan Target:", placeholder="https://example.blogspot.com/")
    
    c1, c2 = st.columns(2)
    with c1:
        output_format = st.selectbox("Format XML Output:", ["Blogger (Atom)", "WordPress (WXR)"])
        grab_mode = st.selectbox("Mode Generate:", ["Semua Isi File", "Hanya Konten Teks", "Hanya Video"])
    with c2:
        limit_post = st.number_input("Jumlah Postingan (Max 500):", 1, 500, 10)
        grab_type = st.radio("Metode Pengambilan:", ["Otomatis (Massal)", "Manual (Satuan)"])

# 4. LOGIKA PENGAMBILAN DATA
if 'antrean' not in st.session_state:
    st.session_state.antrean = []

def get_atom_links(url, limit):
    links = []
    base = url.rstrip('/')
    # Jalur Atom XML untuk menembus konten massal
    atom_url = f"{base}/atom.xml?redirect=false&start-index=1&max-results={limit}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(atom_url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'xml')
            entries = soup.find_all('entry')
            for entry in entries:
                link_tag = entry.find('link', rel='alternate')
                if link_tag: links.append(link_tag['href'])
    except: pass
    return list(set(links))

def grab_core(url, mode):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        t = s.find('h1').text.strip() if s.find('h1') else (s.title.string if s.title else "Tanpa Judul")
        
        final_c = ""
        if mode in ["Semua Isi File", "Hanya Konten Teks"]:
            body = s.find(class_=re.compile(r'post-body|entry-content|article-post'))
            if body: final_c += str(body)

        if mode in ["Semua Isi File", "Hanya Video"]:
            for f in s.find_all('iframe'):
                if any(x in f.get('src', '').lower() for x in ['embed', 'video', 'youtube']):
                    final_c += str(f)
                    
        return t, final_c
    except: return None, None

# 5. FUNGSI PEMBUAT XML (FIXED ID & PUBLISHED)
def build_xml(items, format_type):
    now_iso = datetime.now().isoformat() + "Z"
    if format_type == "Blogger (Atom)":
        entries = ""
        for i in items:
            c_safe = i['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            p_id = f"tag:blogger.com,1999:blog-{int(datetime.now().timestamp())}.post-{hash(i['title'])}"
            entries += f"""<entry><id>{p_id}</id><published>{now_iso}</published><updated>{now_iso}</updated><category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/><title type='text'>{i['title']}</title><content type='html'>{c_safe}</content><control xmlns='http://www.w3.org/2007/app'><draft xmlns='http://purl.org/atom/app#'>no</draft></control><author><name>Den Abi</name></author></entry>"""
        return f"<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom'>{entries}</feed>"
    else:
        e = ""
        for i in items:
            now_wp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            e += f"""<item><title>{i['title']}</title><pubDate>{now_wp}</pubDate><content:encoded><![CDATA[{i['content']}]]></content:encoded><wp:status>publish</wp:status></item>"""
        return f"<?xml version='1.0' encoding='UTF-8' ?><rss version='2.0' xmlns:content='http://purl.org/rss/1.0/modules/content/' xmlns:wp='http://wordpress.org/export/1.2/'><channel><wp:wxr_version>1.2</wp:wxr_version>{e}</channel></rss>"

# 6. EKSEKUSI TOMBOL
st.write("---")
if st.button("🔥 MULAI EKSEKUSI SEKARANG"):
    if target_url:
        st.session_state.antrean = []
        with st.spinner('Server sedang memproses data...'):
            if grab_type == "Otomatis (Massal)":
                links = get_atom_links(target_url, limit_post)
                if links:
                    p_bar = st.progress(0)
                    for idx, l in enumerate(links):
                        title, content = grab_core(l, grab_mode)
                        if title and content:
                            st.session_state.antrean.append({'title': title, 'content': content})
                        p_bar.progress((idx + 1) / len(links))
                    st.success(f"Berhasil! {len(st.session_state.antrean)} postingan siap diunduh.")
                else:
                    st.error("Gagal mendeteksi jalur Atom. Pastikan URL adalah Beranda Blog.")
            else:
                t, c = grab_core(target_url, grab_mode)
                if t and c:
                    st.session_state.antrean.append({'title': t, 'content': c})
                    st.success(f"Berhasil mengambil secara manual: {t}")
    else:
        st.warning("Silakan masukkan URL target terlebih dahulu.")

# 7. AREA DOWNLOAD
if st.session_state.antrean:
    st.write("---")
    xml_final = build_xml(st.session_state.antrean, output_format)
    b64 = base64.b64encode(xml_final.encode()).decode()
    st.markdown(f'<a href="data:file/xml;base64,{b64}" download="DenAbi_Hasil_Migrasi.xml" class="btn-download">📥 DOWNLOAD {len(st.session_state.antrean)} ITEM ({output_format})</a>', unsafe_allow_html=True)
    if st.button("🔄 RESET DAFTAR"):
        st.session_state.antrean = []
        st.rerun()

st.markdown("<br><p style='text-align:center; font-size:12px; opacity:0.5;'>Dikembangkan oleh Proyek Den Abi © 2026 | Versi Tanpa GitHub</p>", unsafe_allow_html=True)
