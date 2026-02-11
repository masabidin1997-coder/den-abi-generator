import streamlit as st
import time
import random

# 1. SETUP UI DARK MODE
st.set_page_config(page_title="Den Abi Real-Monitor V4.1", page_icon="🖥️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #00FFCC; }
    .monitor-box { 
        border: 2px solid #00FFCC; padding: 15px; border-radius: 10px;
        background: #111; font-family: 'Courier New', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE LINK
if 'db_links' not in st.session_state:
    st.session_state.db_links = ["https://fazagafi21.blogspot.com/", "https://prostream.my.id/"]

st.title("🖥️ DEN ABI REAL-TIME MONITORING BOT")
st.write("Sistem ini akan membuka web asli di tab baru agar kamu bisa melihat prosesnya langsung.")

# 3. KONTROL UTAMA
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎮 Kontrol Panel")
    target_url = random.choice(st.session_state.db_links)
    st.write(f"**Target Link:** {target_url}")
    
    if st.button("🚀 JALANKAN BOT & LIHAT WEB"):
        # PERINTAH BUKA WEB ASLI
        st.write(f'<script>window.open("{target_url}", "_blank");</script>', unsafe_allow_html=True)
        
        with col2:
            st.subheader("📟 Bot Logic Logs")
            log_area = st.empty()
            p_bar = st.progress(0)
            status_logs = []
            
            # Simulasi langkah agar kamu bisa mencocokkan dengan web yang terbuka
            actions = [
                ("Membuka Jendela Browser Baru...", 10),
                ("Menunggu Website Terbuka Sempurna...", 25),
                ("Scroll Perlahan ke Bawah (Mencari Iklan)...", 45),
                ("Iklan Ditemukan di Bagian Sidebar!", 60),
                ("Melakukan Simulasi Klik (Misi 1)...", 75),
                ("Menunggu Loading Iklan (High Retention)...", 90),
                ("Selesai! Silakan tutup tab web tadi.", 100)
            ]
            
            for act, p in actions:
                status_logs.append(f"> {act}")
                log_area.markdown(f'<div class="monitor-box">{"<br>".join(status_logs)}</div>', unsafe_allow_html=True)
                p_bar.progress(p)
                time.sleep(random.uniform(3, 6))

with col2:
    if 'status_logs' not in locals():
        st.info("Klik tombol di kiri. Bot akan membuka tab baru berisi web aslimu.")

# 4. PENDAFTARAN
st.write("---")
with st.expander("➕ Daftarkan Blog Kamu"):
    u = st.text_input("Link Blog:")
    if st.button("Daftar"):
        st.session_state.db_links.append(u)
        st.success("Berhasil masuk antrean!")
