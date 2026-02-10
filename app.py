import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Den Abi Universal Generator Pro", 
    page_icon="🌍", 
    layout="centered"
)

# 2. STYLE CSS CUSTOM (TAMPILAN PREMIUM)
st.markdown("""
    <style>
    /* Mengubah warna background utama */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #ffffff;
    }
    /* Style Card Input */
    .stTextInput>div>div>input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border-radius: 10px !important;
        font-weight: bold;
    }
    /* Style Tombol Utama */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 800;
        height: 3.5em;
        background: linear-gradient(45deg, #5c49f5, #00d2ff);
        color: white;
        border: none;
        transition: 0.3s;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 6px 20px rgba(92, 73, 245, 0.4);
    }
    /* Style Tombol Download */
    .btn-download {
        display: inline-block;
        padding: 15px 30px;
        background: linear-gradient(45deg, #fbc02d, #f57f17);
        color: black !important;
        text-decoration: none;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        width: 100%;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
    }
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 50px;
        font-size: 0.8em;
        color: #aaa;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. HEADER
st.markdown("<h1 style='text-align: center; color: #00d2ff;'>🌍 DEN ABI UNIVERSAL PRO V8</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #ddd;'>Generate konten massal lintas platform dengan teknologi Server-Side Bypass.</p>", unsafe_allow_html=True)

# 4. FORM INPUT
with st.container():
    st.markdown("### 🔗 Konfigurasi Target")
    target_url = st.text_input("Link Beranda / Homepage Situs Target:", placeholder="https://example.com/")
    
    col1, col2 = st.columns(2)
    with col1:
        output_format = st.selectbox("Format Output XML:", ["Blogger (Atom)", "WordPress (WXR)"])
    with col2:
        limit_post = st.number_input("Jumlah Postingan (Min 1, Max 50):", min_value=1, max_value=50, value=10)

# 5. LOGIKA CORE (GRABBER)
if 'antrean' not in st.session_state:
    st.session_state.antrean = []

def get_bulk_links(url):
    links = []
    # Deteksi RSS Feed Otomatis
    feed_url = url.rstrip('/') + '/feeds/posts/default?alt=rss' if 'blogspot' in url else url.rstrip('/') + '/feed/'
    try:
        res = requests.get(feed_url, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        items = soup.find_all('item') or soup.find_all('entry')
        for item in items[:limit_post]:
            link = item.find('link').text if item.find('link') else item.find('link')['href']
            links.append(link)
    except:
        st.error("Gagal mendeteksi feed otomatis. Situs mungkin diproteksi ketat.")
    return list(set(links))

def grab_full_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.find('h1').get_text().strip() if soup.find('h1') else (soup.title.string if soup.title else "No Title")
        
        content = ""
        # Cari Gambar Utama
        img = soup.find("meta", property="og:image")
        if img: content += f'<img src="{img["content"]}" style="width:100%; border-radius:15px;"/><br/>'
        
        # Cari Video
        iframes = soup.find_all('iframe')
        for f in iframes:
            if 'embed' in f.get('src', ''): content += str(f)
            
        # Isi Body
        body = soup.find(class_=re.compile(r'post-body|entry-content|article-post'))
        if body: content += str(body)
            
        return title, content
    except: return None, None

# 6. GENERATOR FORMAT (FIX SYNTAX ERROR)
def generate_blogger_xml(items):
    entries = ""
    for item in items:
        now = datetime.now().isoformat() + "Z"
        # Membersihkan teks untuk XML agar tidak error f-string
        c_text = item['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        entries += f"""
    <entry>
        <category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/>
        <title type='text'>{item['title']}</title>
        <content type='html'>{c_text}</content>
        <published>{now}</published>
        <control xmlns='http://www.w3.org/2007/app'><draft xmlns='http://purl.org/atom/app#'>no</draft></control>
        <author><name>Den Abi</name></author>
    </entry>"""
    return f"<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' xmlns:blogger='http://schemas.google.com/blogger/2008'>{entries}</feed>"

def generate_wordpress_xml(items):
    items_xml = ""
    for item in items:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        items_xml += f"""
        <item>
            <title>{item['title']}</title>
            <pubDate>{now}</pubDate>
            <dc:creator>Den Abi</dc:creator>
            <content:encoded><![CDATA[{item['content']}]]></content:encoded>
            <wp:status>publish</wp:status>
            <wp:post_type>post</wp:post_type>
        </item>"""
    return f"""<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:wp="http://wordpress.org/export/1.2/"><channel><wp:wxr_version>1.2</wp:wxr_version>{items_xml}</channel></rss>"""

# 7. TOMBOL AKSI
st.write("---")
if st.button("🚀 MULAI GENERATE MASSAL"):
    if target_url:
        st.session_state.antrean = [] # Reset antrean
        with st.spinner('Server sedang bekerja keras mengambil data...'):
            links = get_bulk_links(target_url)
            if links:
                progress_bar = st.progress(0)
                for i, link in enumerate(links):
                    t, c = grab_full_data(link)
                    if t and c:
                        st.session_state.antrean.append({'title': t, 'content': c})
                    progress_bar.progress((i + 1) / len(links))
                st.success(f"Berhasil mengumpulkan {len(st.session_state.antrean)} postingan!")
            else:
                st.error("Link tidak valid atau situs memblokir feed RSS.")
    else:
        st.warning("Silakan masukkan URL target.")

# 8. AREA DOWNLOAD
if st.session_state.antrean:
    st.markdown("### 📦 File Siap Diunduh")
    
    if output_format == "Blogger (Atom)":
        final_xml = generate_blogger_xml(st.session_state.antrean)
        f_name = f"Blogger_DenAbi_{datetime.now().strftime('%d%m%y')}.xml"
    else:
        final_xml = generate_wordpress_xml(st.session_state.antrean)
        f_name = f"WordPress_DenAbi_{datetime.now().strftime('%d%m%y')}.xml"
        
    b64 = base64.b64encode(final_xml.encode()).decode()
    
    col_dl, col_rs = st.columns([3, 1])
    with col_dl:
        st.markdown(f'<a href="data:file/xml;base64,{b64}" download="{f_name}" class="btn-download">📥 DOWNLOAD XML {output_format.upper()}</a>', unsafe_allow_html=True)
    with col_rs:
        if st.button("🔄 RESET"):
            st.session_state.antrean = []
            st.rerun()

# 9. FOOTER
st.markdown("""
    <div class="footer">
        Developed by Den Abi Project © 2026<br>
        Optimized for Prostream & Goostream Network
    </div>
    """, unsafe_allow_html=True)
