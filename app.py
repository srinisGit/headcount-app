import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Page Configuration
st.set_page_config(
    page_title="Factory Live Headcount & Muster Dashboard", 
    page_icon="🏭", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase
SUPABASE_URL = "https://aqnryhvsltbwhcbnwiyr.supabase.co" # Your verified URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxbnJ5aHZzbHRid2hjYm53aXlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzODM0NDksImV4cCI6MjA5OTk1OTQ0OX0.yBtM42rPhi1NmzJib4IemeJ9pzZpUROI2zLKVpb4C8s"          # Replace with your actual Anon Key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Modern UI Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f9fafb;
        margin-top: 5px;
    }
    .emergency-banner {
        background: #dc2626;
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 0 15px rgba(220, 38, 38, 0.5);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Session State & Login Setup
if "dash_user" not in st.session_state:
    st.session_state.dash_user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# --- AUTHENTICATION GATEWAY ---
if not st.session_state.dash_user:
    st.markdown("<h2 style='text-align: center;'>🔐 Factory Headcount Dashboard Access</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("dash_login"):
            u_input = st.text_input("Username").lower().strip()
            p_input = st.text_input("Password", type="password")
            submit = st.form_submit_button("Authenticate & Open Dashboard", use_container_width=True, type="primary")
            
            if submit:
                res = supabase.table("app_users").select("*").eq("username", u_input).eq("password", p_input).execute()
                if res.data:
                    u_data = res.data[0]
                    if u_data.get("app_type") in ["dashboard", "both"]:
                        st.session_state.dash_user = u_data["username"]
                        st.session_state.user_role = u_data["role"]
                        st.rerun()
                    else:
                        st.error("Unauthorized: User does not have access to Dashboard.")
                else:
                    st.error("Invalid Credentials.")
    st.stop()

# Role permissions mapping
ROLE_PERMISSIONS = {
    "Super Admin": {"emergency": True, "admin_tools": True},
    "Safety Officer": {"emergency": True, "admin_tools": False},
    "Factory Head": {"emergency": True, "admin_tools": False},
    "HR Rep": {"emergency": False, "admin_tools": False},
    "Security Officer": {"emergency": False, "admin_tools": False}
}

user_perms = ROLE_PERMISSIONS.get(st.session_state.user_role, {"emergency": False, "admin_tools": False})

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏭 Control Panel")
    st.markdown(f"👤 **User:** `{st.session_state.dash_user.upper()}`")
    st.markdown(f"🛡️ **Role:** `{st.session_state.user_role}`")
    st.divider()
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state.dash_user = None
        st.session_state.user_role = None
        st.rerun()

# --- FETCH LIVE DATA FROM SUPABASE ---
def fetch_live_headcount():
    categories = [
        "Staff", "Workers", "Contract Labours","Housekeeping","Loadmen", "Drivers+Helpers", "civil Workers", "Visitors", 
        "interview candidates"
    ]
    counts = {cat: 0 for cat in categories}
    
    # Fetch logs selecting exact database columns
    response = supabase.table("gate_logs").select("category, movement_type, count_value").execute()
    if response.data:
        for row in response.data:
            cat = row.get("category")
            if cat in counts:
                cnt = row.get("count_value", 0) or 0
                m_type = row.get("movement_type")
                if m_type == "IN":
                    counts[cat] += cnt
                elif m_type == "OUT":
                    counts[cat] = max(0, counts[cat] - cnt) # Prevent negative numbers
    return counts

live_counts = fetch_live_headcount()
total_occupancy = sum(live_counts.values())

# --- MAIN DASHBOARD INTERFACE ---
st.title("📊 Factory Live Headcount & Evacuation Dashboard")

# --- EMERGENCY MUSTER MODE ---
if "emergency_mode" not in st.session_state:
    st.session_state.emergency_mode = False

if st.session_state.emergency_mode:
    st.markdown(f"""
        <div class='emergency-banner'>
            <h1>🚨 EMERGENCY MUSTER MODE ACTIVE</h1>
            <h3>EVACUATION TARGET HEADCOUNT BASELINE: {st.session_state.snapshot_total}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🟢 DEACTIVATE EMERGENCY / RETURN TO NORMAL MONITORING", type="primary", use_container_width=True):
        st.session_state.emergency_mode = False
        st.rerun()

# --- OCCUPANCY METRICS DISPLAY ---
st.metric("TOTAL FACTORY OCCUPANCY", f"{total_occupancy} Persons")

st.markdown("### 👥 Occupancy Breakdown by Category")
cols = st.columns(4)
for idx, (cat, val) in enumerate(live_counts.items()):
    with cols[idx % 4]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{cat}</div>
            <div class="metric-value">{val}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# --- ACTION CONTROLS (ROLE-BASED) ---

# 1. Emergency Protocol Controls (Super Admin, Safety, Factory Head)
if user_perms["emergency"]:
    st.markdown("### 🚨 Emergency Control Protocol")
    if not st.session_state.emergency_mode:
        if st.button("🚨 ACTIVATE EMERGENCY MUSTER MODE", use_container_width=True, type="primary"):
            st.session_state.emergency_mode = True
            st.session_state.snapshot_total = total_occupancy
            st.rerun()
else:
    st.info("ℹ️ Emergency Control Protocol access is restricted to Safety Officers, Factory Heads, and Super Admins.")

# 2. Super Admin Control Tools
if user_perms["admin_tools"]:
    st.divider()
    with st.expander("🛠️ Super Admin Tools (User Management & Reset)"):
        st.warning("Admin Actions")
        
        tab1, tab2 = st.tabs(["Add User", "Reset Headcount Data"])
        
        with tab1:
            with st.form("add_user_form"):
                new_u = st.text_input("Username").lower().strip()
                new_p = st.text_input("Password")
                new_r = st.selectbox("Role", ["Super Admin", "Safety Officer", "Factory Head", "HR Rep", "Security Officer", "Inspector"])
                new_app = st.selectbox("App Permission", ["dashboard", "gate", "both"])
                submit_u = st.form_submit_button("Create User")
                
                if submit_u and new_u and new_p:
                    supabase.table("app_users").insert({
                        "username": new_u, "password": new_p, "role": new_r, "app_type": new_app
                    }).execute()
                    st.success(f"User {new_u} created successfully!")
        
        with tab2:
            if st.button("⚠️ Clear All Gate Logs / Reset Data", type="secondary"):
                supabase.table("gate_logs").delete().neq("id", 0).execute()
                st.success("All daily gate logs cleared. Occupancy reset to 0.")
                st.rerun()
