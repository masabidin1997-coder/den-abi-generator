import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import re

# Konfigurasi Halaman
st.set_page_config(page_title="Den Abi Universal Generator", page_icon="🌍", layout="centered")

st.title("🌍 Den Abi Universal Generator V7")
st.write("Generate konten massal untuk Blogger atau WordPress dalam satu klik!")

# Input URL
target_url = st.text_input("Link Homepage Blog Target:", placeholder="https://example.com/")

# Opsi Output
st.write("---")
col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    output_format = st.radio("Pilih Format Output XML:", ("Blogger (Atom)", "WordPress (WXR)"))
with col_opt2:
    limit_post = st.number_input("Maksimal Postingan:", min_value=1, max_value=50, value=10)

if 'antrean' not in st.session_state:
    st.session_state.antrean = []

# --- FUNGSI CORE ---

def get_bulk_links(url):
    links = []
    # Deteksi Feed
    feed_url = url.rstrip('/') + '/feeds/posts/default?alt=rss' if 'blogspot' in url else url.rstrip('/') + '/feed/'
    try:
        res = requests.get(feed_url, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        items = soup.find_all('item') or soup.find_all('entry')
        for item in items[:limit_post]:
            link = item.find('link').text if item.find('link') else item.find('link')['href']
            links.append(link)
    except:
        st.error("Gagal mendeteksi feed otomatis.")
    return list(set(links))

def grab_full_data(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.find('h1').get_text().strip() if soup.find('h1') else (soup.title.string if soup.title else "No Title")
        
        # Grab Gambar & Video
        content = ""
        img = soup.find("meta", property="og:image")
        if img: content += f'<img src="{img["content"]}" style="width:100%; border-radius:10px;"/><br/>'
        
        iframes = soup.find_all('iframe')
        for f in iframes:
            if 'embed' in f.get('src', ''): content += str(f)
            
        body = soup.find(class_=re.compile(r'post-body|entry-content|article-post'))
        if body: content += str(body)
            
        return title, content
    except: return None, None

# --- GENERATOR FORMAT ---

def generate_blogger_xml(items):
    entries = ""
    for item in items:
        now = datetime.now().isoformat() + "Z"
        entries += f"""
    <entry>
        <category scheme="http://www.blogger.com/atom/ns#" term="AGC-DenAbi"/>
        <title type='text'>{item['title']}</title>
        <content type='html'>{item['content'].replace('&', '&amp;').replace('<', '&lt;').replace(/>/g, '&gt;')}</content>
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
            <description></description>
            <content:encoded><![CDATA[{item['content']}]]></content:encoded>
            <wp:status>publish</wp:status>
            <wp:post_type>post</wp:post_type>
        </item>"""
    
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wfw="http://wellformedweb.org/CommentAPI/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:wp="http://wordpress.org/export/1.2/">
    <channel>
        <wp:wxr_version>1.2</wp:wxr_version>
        {items_xml}
    </channel>
</rss>"""

# --- TOMBOL AKSI ---

if st.button("🚀 MULAI GENERATE MASSAL"):
    if target_url:
        st.session_state.antrean = [] # Reset antrean baru
        with st.spinner('Mencari postingan...'):
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
                st.error("Link tidak valid atau Feed tidak ditemukan.")

# --- DOWNLOAD AREA ---

if st.session_state.antrean:
    st.write("---")
    st.subheader(f"📦 Siap Download: {len(st.session_state.antrean)} Postingan")
    
    if output_format == "Blogger (Atom)":
        final_xml = generate_blogger_xml(st.session_state.antrean)
        file_name = "Blogger_Import_DenAbi.xml"
    else:
        final_xml = generate_wordpress_xml(st.session_state.antrean)
        file_name = "WordPress_Import_DenAbi.xml"
        
    b64 = base64.b64encode(final_xml.encode()).decode()
    st.markdown(f'<a href="data:file/xml;base64,{b64}" download="{file_name}"><button style="width:100%; background:#fbc02d; padding:15px; border-radius:10px; font-weight:bold; border:none; cursor:pointer;">📥 DOWNLOAD XML UNTUK {output_format.upper()}</button></a>', unsafe_allow_html=True)

st.caption("Den Abi Multi-Generator V7")
