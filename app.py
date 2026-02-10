import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Den Abi Master Generator V10.1", 
    page_icon="🚀", 
    layout="centered"
)

# 2. TAMPILAN PREMIUM & FIX FONT WARNA PUTIH
st.markdown("""
    <style>
    /* Sembunyikan Menu GitHub & Share */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Background & Warna Dasar */
    .stApp {
        background: linear-gradient(135deg, #0d0d0d, #1a1a2e, #16213e);
        color: #ffffff;
    }
    
    /* PAKSA WARNA FONT PUTIH DI SEMUA INPUT */
    input, select, textarea, .stSelectbox div {
        background-color: #252525 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Warna Label Input */
    label, p, span {
        color: #ffffff !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 800;
        height: 3.8em;
        background: linear-gradient(90deg, #5c49f5, #8e2de2);
        color: white;
        border: none;
    }
    
    .download-card {
        padding: 20px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        border: 1px solid #5c49f5;
        text-align: center;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #5c49f5;'>🚀 DEN ABI MASTER GENERATOR V10.1</h1>", unsafe_allow_html=True)

# 3. AREA KONFIGURASI
with st.container():
    st.markdown("### 🛠️ Pengaturan Konten")
    target_url = st.text_input("Link Beranda Blog Target:", placeholder="https://example.com/")
    
    c1, c2 = st.columns(2)
    with c1:
        output_format = st.selectbox("Format XML:", ["Blogger (Atom)", "WordPress (WXR)"])
        grab_mode = st.selectbox("Mode Generate:", ["Semua Isi File", "Hanya Konten Teks", "Hanya Video"])
    with c2:
        limit_post = st.number_input("Jumlah Postingan (Max 50):", 1, 50, 10)

# 4. LOGIKA PENGAMBILAN DATA (DENGAN RE-TRY & HEADERS KUAT)
if 'antrean' not in st.session_state:
    st.session_state.antrean = []

def get_feed_links(url):
    links = []
    base = url.rstrip('/')
    # Daftar Feed yang lebih lengkap
    f_urls = [
        f"{base}/feeds/posts/default?alt=rss&max-results={limit_post}", 
        f"{base}/feed/", 
        f"{base}/rss.xml",
        f"{base}/?feed=rss2"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    
    for f in f_urls:
        try:
            r = requests.get(f, headers=headers, timeout=15)
            if r.status_code == 200:
                s = BeautifulSoup(r.content, 'xml')
                items = s.find_all('item') or s.find_all('entry')
                for i in items[:limit_post]:
                    # Deteksi link untuk Blogger dan WordPress
                    lnk = None
                    if i.find('link') and i.find('link').has_attr('href'):
                        lnk = i.find('link')['href']
                    elif i.find('link'):
                        lnk = i.find('link').text
                    
                    if lnk: links.append(lnk)
                if links: break
        except: continue
    return list(set(links))

def grab_core(url, mode):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        t = s.find('h1').text.strip() if s.find('h1') else (s.title.string if s.title else "No Title")
        
        final_c = ""
        # Grab Gambar & Konten
        if mode == "Semua Isi File":
            og_img = s.find("meta", property="og:image")
            if og_img: final_c += f'<img src="{og_img["content"]}" style="width:100%; border-radius:10px;"/><br/>'

        if mode in ["Semua Isi File", "Hanya Konten Teks"]:
            body = s.find(class_=re.compile(r'post-body|entry-content|article-post|article-content'))
            if body: final_c += str(body)

        if mode in ["Semua Isi File", "Hanya Video"]:
            for f in s.find_all('iframe'):
                if any(x in f.get('src', '').lower() for x in ['embed', 'video', 'youtube', 'bebas']):
                    final_c += str(f)
                    
        return t, final_c
    except: return None, None

# 5. FUNGSI XML (FORMAT STANDAR)
def build_blogger(items):
    e = ""
    for i in items:
        now = datetime.now().isoformat() + "Z"
        # Membersihkan teks untuk XML agar tidak error
        safe_c = i['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        e += f"""<entry><category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/><title type='text'>{i['title']}</title><content type='html'>{safe_c}</content><published>{now}</published><control xmlns='http://www.w3.org/2007/app'><draft xmlns='http://purl.org/atom/app#'>no</draft></control><author><name>Den Abi</name></author></entry>"""
    return f"<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' xmlns:blogger='http://schemas.google.com/blogger/2008'>{e}</feed>"

def build_wordpress(items):
    e = ""
    for i in items:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        e += f"""<item><title>{i['title']}</title><pubDate>{now}</pubDate><dc:creator>Den Abi</dc:creator><content:encoded><![CDATA[{i['content']}]]></content:encoded><wp:status>publish</wp:status><wp:post_type>post</wp:post_type></item>"""
    return f"""<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:wp="http://wordpress.org/export/1.2/"><channel><wp:wxr_version>1.2</wp:wxr_version>{e}</channel></rss>"""

# 6. EKSEKUSI
st.write("---")
if st.button("🔥 GENERATE SEKARANG"):
    if target_url:
        st.session_state.antrean = []
        with st.spinner('Menganalisis dan menarik data...'):
            all_links = get_feed_links(target_url)
            if all_links:
                p_bar = st.progress(0)
                for idx, l in enumerate(all_links):
                    title, content = grab_core(l, grab_mode)
                    if title and content:
                        st.session_state.antrean.append({'title': title, 'content': content})
                    p_bar.progress((idx + 1) / len(all_links))
                st.success(f"Berhasil mengumpulkan {len(st.session_state.antrean)} postingan!")
            else:
                st.error("Gagal mendeteksi postingan. Pastikan link aktif.")
    else:
        st.warning("Masukkan URL target.")

# 7. DOWNLOAD
if st.session_state.antrean:
    st.markdown("<div class='download-card'>", unsafe_allow_html=True)
    xml_final = build_blogger(st.session_state.antrean) if output_format == "Blogger (Atom)" else build_wordpress(st.session_state.antrean)
    b64 = base64.b64encode(xml_final.encode()).decode()
    st.markdown(f'<h3>📦 {len(st.session_state.antrean)} File Siap Diunduh</h3>', unsafe_allow_html=True)
    st.markdown(f'<a href="data:file/xml;base64,{b64}" download="DenAbi_Result.xml" style="text-decoration:none;"><button style="width:100%; background:#fbc02d; color:black; border:none; padding:15px; border-radius:10px; font-weight:bold; cursor:pointer;">📥 DOWNLOAD SEKARANG</button></a>', unsafe_allow_html=True)
    if st.button("🔄 RESET"):
        st.session_state.antrean = []
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br><p style='text-align:center; font-size:12px; opacity:0.5;'>Den Abi Master Project © 2026</p>", unsafe_allow_html=True)
