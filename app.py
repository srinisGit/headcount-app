import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time
from datetime import datetime, time as datetime_time

# 1. Page Configuration
st.set_page_config(page_title="Live Emergency Headcount", layout="wide")

# 2. Database Connection Configuration
SUPABASE_URL = "https://aqnryhvsltbwhcbnwiyr.supabase.co" # Your verified URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxbnJ5aHZzbHRid2hjYm53aXlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzODM0NDksImV4cCI6MjA5OTk1OTQ0OX0.yBtM42rPhi1NmzJib4IemeJ9pzZpUROI2zLKVpb4C8s"          # Replace with your actual Anon Key

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# 3. Handle Emergency State & Snapshot Cache across UI refreshes
if 'emergency_mode' not in st.session_state:
    st.session_state.emergency_mode = False
if 'snapshot_counts' not in st.session_state:
    st.session_state.snapshot_counts = {}
if 'snapshot_total' not in st.session_state:
    st.session_state.snapshot_total = 0
if 'cleared_categories' not in st.session_state:
    st.session_state.cleared_categories = set()

# 4. Data Extraction Function (Filters data from the current calendar day)
@st.cache_data(ttl=2) # Clears cache every 2 seconds for real-time streaming
def fetch_live_logs():
    today_start = datetime.now().combine(datetime.today(), datetime_time.min).isoformat()
    
    # Queries rows generated since 00:00 today to implement the daily automatic baseline reset
    response = supabase.table("gate_logs").select("category, movement_type, count_value").gte("created_at", today_start).execute()
    
    # Process inputs into active headcounts
    categories = [
        "Staff", "Workers", "Contract Labours", "Housekeeping", 
        "Loadmen", "Drivers+Helpers", "Visitors", "Interview candidates"
    ]
    
    counts = {cat: 0 for cat in categories}
    total = 0
    
    if response.data:
        df = pd.DataFrame(response.data)
        for cat in categories:
            cat_df = df[df['category'] == cat]
            ins = cat_df[cat_df['movement_type'] == 'IN']['count_value'].sum()
            outs = cat_df[cat_df['movement_type'] == 'OUT']['count_value'].sum()
            
            current = max(0, ins - outs) # Prevents negative integer values from field log typos
            counts[cat] = int(current)
            total += int(current)
            
    return counts, total

# 5. Core Dashboard UI Logic
if not st.session_state.emergency_mode:
    # --- NORMAL OPERATIONS VIEW ---
    st.markdown("<h1 style='text-align: center; color: #1e3d59;'>🏢 FACTORY LIVE HEADCOUNT PANEL</h1>", unsafe_allow_html=True)
    st.write(f"<p style='text-align: center; color: #666;'>Last Updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</p>", unsafe_allow_html=True)
    st.write("---")
    
    live_counts, total_occupancy = fetch_live_logs()
    
    # Big Live Occupancy Counter Banner
    st.markdown(f"""
        <div style='background-color: #e8f1f5; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #1e3d59; margin-bottom: 25px;'>
            <h2 style='margin: 0; color: #1e3d59; font-weight: 500;'>TOTAL PERSONS CURRENTLY INSIDE</h2>
            <h1 style='margin: 10px 0 0 0; font-size: 65px; color: #1e3d59;'>{total_occupancy}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Display Breakdown Grid
    st.markdown("### 📊 Headcount by Category")
    col1, col2, col3, col4 = st.columns(4)
    col5, col6, col7, col8 = st.columns(4)
    ui_cols = [col1, col2, col3, col4, col5, col6, col7, col8]
    
    for idx, (category, val) in enumerate(live_counts.items()):
        with ui_cols[idx]:
            st.metric(label=category, value=val)
            
    st.write("---")
    
    # Emergency Action Section
    st.markdown("### ⚠️ Emergency Control Protocol")
    if st.button("🚨 ACTIVATE EMERGENCY MUSTER MODE", use_container_width=True, type="primary"):
        st.session_state.emergency_mode = True
        st.session_state.snapshot_counts = live_counts.copy()
        st.session_state.snapshot_total = total_occupancy
        st.session_state.cleared_categories = set()
       
        st.rerun()

else:
    # --- EMERGENCY MUSTER MODE VIEW ---
    st.markdown("<h1 style='text-align: center; color: #d32f2f; font-size: 45px;'>🚨 EMERGENCY EVACUATION MODE ACTIVE</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #b71c1c;'>Live Gate Logging Suspended • Baseline Count Locked</h3>", unsafe_allow_html=True)
    st.write("---")
    
    # Show frozen target number
    st.markdown(f"""
        <div style='background-color: #ffebee; padding: 20px; border-radius: 12px; text-align: center; border: 3px solid #d32f2f; margin-bottom: 25px;'>
            <h2 style='margin: 0; color: #b71c1c;'>TARGET HEADCOUNT TO ACCOUNT FOR</h2>
            <h1 style='margin: 10px 0 0 0; font-size: 70px; color: #b71c1c;'>{st.session_state.snapshot_total}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Muster Point Assembly Checklist")
    st.write("Mark categories as cleared as groups report safely to assembly zones:")
    
    # Render checklist items dynamically
    for category, target_count in st.session_state.snapshot_counts.items():
        is_cleared = category in st.session_state.cleared_categories
        
        c_left, c_right = st.columns([3, 1])
        with c_left:
            if is_cleared:
                st.markdown(f"✅ ~~**{category}**: {target_count} persons accounted for~~")
            else:
                st.markdown(f"❌ **{category}**: Need to account for **{target_count}** persons")
        with c_right:
            if not is_cleared:
                if st.button(f"Clear {category}", key=f"clr_{category}"):
                    st.session_state.cleared_categories.add(category)
                    st.rerun()
            else:
                if st.button(f"Undo Clear", key=f"undo_{category}"):
                    st.session_state.cleared_categories.remove(category)
                    st.rerun()
                    
    st.write("---")
    
    # All groups accounted for condition
    if len(st.session_state.cleared_categories) == len(st.session_state.snapshot_counts):
        st.success("🎉 All categories checked and accounted for at muster points!")
        
    # Deactivate Emergency Mode
    if st.button("🟢 Deactivate Emergency Mode & Resume Logging", use_container_width=True):
        st.session_state.emergency_mode = False
        st.rerun()

# 6. Automatic UI loop execution (Refreshes the script interface every 3 seconds)
time.sleep(3)
st.rerun()