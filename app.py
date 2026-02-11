import streamlit as st
import time
import random

# 1. STYLE APLIKASI (WARNA MERAH SEPERTI REFERENSI)
st.set_page_config(page_title="View Booster - Den Abi", page_icon="📈")
st.markdown("""
    <style>
    .stApp { background-color: #f4f4f4; color: #333; }
    .header-box { background: #FF0000; padding: 20px; color: white; text-align: center; border-radius: 0 0 20px 20px; }
    .card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; text-align: center; }
    .points-display { font-size: 24px; font-weight: bold; color: #FF0000; }
    .stButton>button { background-color: #FF0000; color: white; border-radius: 5px; width: 100%; border: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE SEDERHANA
if 'points' not in st.session_state: st.session_state.points = 120
if 'campaigns' not in st.session_state: 
    st.session_state.campaigns = [{"url": "https://prostream.my.id/", "reward": 70, "time": 60}]

# --- HEADER ---
st.markdown('<div class="header-box"><h1>Get Free Views</h1><p>FOR YOUR BLOGS EASILY!</p></div>', unsafe_allow_html=True)
st.write("")

# --- TABS SEPERTI APLIKASI ---
tab1, tab2 = st.tabs(["📺 Watch & Earn", "➕ Create Campaign"])

with tab1:
    st.markdown(f'<div class="card"><p>Your Points</p><p class="points-display">🪙 {st.session_state.points}</p></div>', unsafe_allow_html=True)
    
    if st.session_state.campaigns:
        task = random.choice(st.session_state.campaigns)
        st.markdown(f'<div class="card"><h3>Watch This Blog</h3><p>Reward: {task["reward"]} Points</p></div>', unsafe_allow_html=True)
        
        # LINK MURNI AGAR TERBUKA (Seperti instruksi sebelumnya)
        st.markdown(f'<a href="{task["url"]}" target="_blank" style="text-decoration:none;"><div style="background:#FF0000; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">START WATCHING</div></a>', unsafe_allow_html=True)
        
        if st.button("VERIFIKASI POIN"):
            with st.spinner(f"Memverifikasi tayangan {task['time']} detik..."):
                t_placeholder = st.empty()
                for i in range(task['time'], 0, -1):
                    t_placeholder.write(f"⏳ Sisa waktu: {i} detik")
                    time.sleep(1)
                st.session_state.points += task['reward']
                st.success(f"Selamat! +{task['reward']} poin berhasil ditambahkan.")
                st.rerun()
    else:
        st.info("Belum ada campaign aktif. Jadilah yang pertama!")

with tab2:
    st.markdown('<div class="card"><h3>Create Campaign</h3></div>', unsafe_allow_html=True)
    url = st.text_input("URL Blog Adsterra:", placeholder="https://...")
    v_count = st.number_input("Number of views:", 10, 1000, 10)
    p_per_v = st.number_input("Points per view (Min 50):", 50, 500, 70)
    t_required = st.number_input("Time required (seconds):", 30, 120, 60)
    
    total_cost = v_count * p_per_v
    st.write(f"**Total Points Required: {total_cost}**")
    
    if st.button("ADD CAMPAIGN"):
        if st.session_state.points >= total_cost:
            if url.startswith("http"):
                st.session_state.campaigns.append({"url": url, "reward": p_per_v, "time": t_required})
                st.session_state.points -= total_cost
                st.success("Campaign berhasil dibuat! Link kamu akan segera muncul di tab Watch.")
            else:
                st.error("Link tidak valid!")
        else:
            st.error("Poin kamu tidak cukup! Silakan tonton blog orang lain dulu.")

st.markdown("---")
st.caption("Den Abi Traffic Booster © 2026")
