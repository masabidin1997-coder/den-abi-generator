import streamlit as st
import time
import random
import pandas as pd

# 1. SETUP UI PREMIUM
st.set_page_config(page_title="Adsterra Gotong Royong - Den Abi", page_icon="💰")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #ffffff; }
    .status-box { background: #111; border: 2px solid #ee1d52; padding: 20px; border-radius: 10px; text-align: center; }
    .btn-click { background: #2ecc71 !important; color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE LINK (Simulasi Google Sheets)
# Untuk 1000+ user, hubungkan ke gspread atau database permanen.
if 'db_links' not in st.session_state:
    st.session_state.db_links = ["https://fazagafi21.blogspot.com/", "https://prostream.my.id/"]

st.title("💰 ADSTERRA IMPRESS EXCHANGE")
st.write("Sistem Gotong Royong Den Abi - Saling Kunjung & Saling Klik")

# 3. FITUR UTAMA: TUGAS ACAK
st.markdown('<div class="status-box">', unsafe_allow_html=True)
target = random.choice(st.session_state.db_links)
st.subheader("🎯 Target Kunjungan")
st.code(target)

if st.button("🚀 BUKA & MULAI TUGAS"):
    st.write(f'<script>window.open("{target}", "_blank");</script>', unsafe_allow_html=True)
    
    t_box = st.empty()
    mission_box = st.empty()
    
    for t in range(60, 0, -1):
        t_box.markdown(f"### ⏳ Menunggu Impress: {t} Detik")
        
        # FITUR INSTRUKSI KLIK (Max 3x)
        if t == 45: mission_box.warning("👉 MISI 1: Cari iklan Adsterra di atas, lalu KLIK 1x!")
        if t == 30: mission_box.warning("👉 MISI 2: Scroll ke bawah, cari iklan lain dan KLIK 1x!")
        if t == 15: mission_box.warning("👉 MISI 3: Terakhir, KLIK tombol download/iklan di bawah!")
        
        time.sleep(1)
    
    st.success("✅ TUGAS SELESAI! Kamu mendapatkan 30 Poin (Impress + 3 Klik)")
st.markdown('</div>', unsafe_allow_html=True)

# 4. FORM DAFTAR LINK (ANTREAN 1000+ USER)
st.write("---")
with st.expander("➕ Daftarkan Blog Kamu ke Jaringan 1000+ User"):
    new_url = st.text_input("Link Blog Adsterra:")
    if st.button("Daftarkan Sekarang"):
        if new_url:
            st.session_state.db_links.append(new_url)
            st.success("Link kamu sudah masuk antrean acak dunia!")
