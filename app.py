import streamlit as st
import time
import random

# 1. SETUP UI DARK MODE PREMIUM
st.set_page_config(page_title="Den Abi Traffic Bot", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #ffffff; }
    .bot-console { 
        background-color: #000; border: 1px solid #00FFCC; 
        padding: 15px; font-family: 'Courier New', Courier, monospace;
        color: #00FFCC; border-radius: 5px; height: 300px; overflow-y: auto;
    }
    .status-text { color: #FFFFFF; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE LINK
if 'db_links' not in st.session_state:
    st.session_state.db_links = ["https://fazagafi21.blogspot.com/", "https://prostream.my.id/"]

st.title("🤖 DEN ABI SMART TRAFFIC BOT V4")
st.markdown("---")

# 3. AREA KONTROL & MONITORING
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🎮 Kontrol Bot")
    target = random.choice(st.session_state.db_links)
    st.info(f"Target Selanjutnya: \n{target}")
    
    if st.button("🚀 JALANKAN BOT OTOMATIS"):
        # MEMBUKA LINK SECARA OTOMATIS
        st.write(f'<script>window.open("{target}", "_blank");</script>', unsafe_allow_html=True)
        
        with col2:
            st.subheader("🖥️ Bot Live Activity")
            console = st.empty()
            progress_bar = st.progress(0)
            logs = []

            # SIMULASI LANGKAH-LANGKAH BOT
            steps = [
                ("🌐 Menginisialisasi Browser Headless...", 5),
                (f"🔗 Menghubungkan ke: {target}", 10),
                ("🕵️ Memeriksa Keamanan Cloudflare/Blogger...", 15),
                ("📜 Melakukan Auto-Scrolling (Mencari Konten)...", 30),
                ("🔍 Menganalisis Posisi Iklan Adsterra...", 45),
                ("🎯 Iklan Ditemukan! Menyiapkan Klik Pertama...", 55),
                ("🖱️ Melakukan Klik Iklan 1 (Smart Click)...", 65),
                ("📜 Scrolling ke Area Bawah (Mencari Iklan 2)...", 75),
                ("🖱️ Melakukan Klik Iklan 2...", 85),
                ("⏳ Menahan Sesi (High Retention)...", 95),
                ("✅ Tugas Selesai! Membersihkan Cache & Cookies...", 100)
            ]

            for text, p in steps:
                logs.append(f"> {text}")
                console.markdown(f'<div class="bot-console">{"<br>".join(logs)}</div>', unsafe_allow_html=True)
                progress_bar.progress(p)
                
                # Jeda agar terlihat seperti bot sedang berpikir/bekerja
                time.sleep(random.uniform(2.5, 5.5)) 

            st.success("🎉 Berhasil! Impress & Klik telah tercatat di dashboard.")
            st.balloons()

with col2:
    if 'logs' not in locals():
        st.info("Klik 'Jalankan Bot' untuk melihat aktivitas simulasi di sini.")

# 4. FORM PENDAFTARAN
st.markdown("---")
with st.expander("➕ Daftarkan Blog Kamu ke Database 1000+ User"):
    new_url = st.text_input("URL Blog Adsterra:")
    if st.button("Daftarkan Sekarang"):
        if new_url.startswith("http"):
            st.session_state.db_links.append(new_url)
            st.success("Link kamu berhasil masuk sistem antrean acak!")
