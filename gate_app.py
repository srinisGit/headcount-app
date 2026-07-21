import streamlit as st
from supabase import create_client, Client

# 1. Page Configuration for Mobile Terminals
st.set_page_config(
    page_title="Factory Gate Terminal", 
    page_icon="🪪", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Supabase

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://aqnryhvsltbwhcbnwiyr.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxbnJ5aHZzbHRid2hjYm53aXlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzODM0NDksImV4cCI6MjA5OTk1OTQ0OX0.yBtM42rPhi1NmzJib4IemeJ9pzZpUROI2zLKVpb4C8s" )
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Touch-Optimized CSS for Peak-Hour Speed
st.markdown("""
<style>
    /* Card Container */
    .gate-card {
        background-color: #1f2937;
        border: 2px solid #374151;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .card-title {
        color: #9ca3af;
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .card-count {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 800;
        margin: 4px 0;
    }
    /* Touch target padding for mobile screens */
    .stButton>button {
        height: 50px;
        font-weight: bold;
        font-size: 1.1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Session State & Login Setup
if "logged_user" not in st.session_state:
    st.session_state.logged_user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# --- AUTHENTICATION SCREEN ---
if not st.session_state.logged_user:
    st.markdown("<h2 style='text-align: center;'>🪪 Gate Terminal Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("gate_login"):
            user_input = st.text_input("Username").lower().strip()
            pass_input = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submit:
                res = supabase.table("app_users").select("*").eq("username", user_input).eq("password", pass_input).execute()
                if res.data:
                    u_data = res.data[0]
                    if u_data.get("app_type") in ["gate", "both"]:
                        st.session_state.logged_user = u_data["username"]
                        st.session_state.user_role = u_data["role"]
                        st.rerun()
                    else:
                        st.error("Unauthorized: No Gate Terminal access permission.")
                else:
                    st.error("Invalid Username or Password.")
    st.stop()

# --- TOP HEADER ---
c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.markdown(f"👤 **Officer:** `{st.session_state.logged_user.upper()}` ({st.session_state.user_role})")
with c_head2:
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state.logged_user = None
        st.session_state.user_role = None
        st.rerun()

st.divider()

# --- EXACT 9 CATEGORIES ORDER ---
CATEGORIES = [
    "Staff",
    "Workers",
    "Contract Labours",
    "Housekeeping",
    "Loadmen",
    "Drivers+Helpers",
    "Civil Workers",
    "Visitors",
    "Interview Candidates"
]

# --- FETCH CURRENT LIVE COUNTS ---
def fetch_current_counts():
    counts = {cat: 0 for cat in CATEGORIES}
    res = supabase.table("gate_logs").select("category, movement_type, count_value").execute()
    if res.data:
        for row in res.data:
            cat = row.get("category")
            if cat in counts:
                cnt = row.get("count_value", 0) or 0
                if row.get("movement_type") == "IN":
                    counts[cat] += cnt
                elif row.get("movement_type") == "OUT":
                    counts[cat] = max(0, counts[cat] - cnt)
    return counts

live_counts = fetch_current_counts()

# --- BATCH STEP QUANTITY SELECTOR ---
st.markdown("### 🚪 Quick Gate Entry Terminal")
step_qty = st.radio("Entry Step Size (for group entries):", [1, 5, 10], horizontal=True)

# Helper function to record database entry instantly
def record_entry(category, movement, qty):
    payload = {
        "category": category,
        "movement_type": movement,
        "count_value": qty,
        "username": st.session_state.logged_user
    }
    supabase.table("gate_logs").insert(payload).execute()
    st.toast(f"{'➕ Recorded IN' if movement == 'IN' else '➖ Recorded OUT'}: {qty} x {category}", icon="✅")

# --- 3-COLUMN RESPONSIVE CARD GRID ---
cols = st.columns(3)

for idx, cat in enumerate(CATEGORIES):
    col = cols[idx % 3]
    with col:
        # Display Card UI with Title & Visible Live Count
        current_cnt = live_counts.get(cat, 0)
        st.markdown(f"""
        <div class="gate-card">
            <div class="card-title">{cat}</div>
            <div class="card-count">{current_cnt}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Dedicated IN / OUT Touch Buttons underneath each card
        btn_in, btn_out = st.columns(2)
        with btn_in:
            if st.button(f"➕ IN", key=f"in_{idx}", type="primary", use_container_width=True):
                record_entry(cat, "IN", step_qty)
                st.rerun()
                
        with btn_out:
            if st.button(f"➖ OUT", key=f"out_{idx}", use_container_width=True):
                if current_cnt > 0:
                    record_entry(cat, "OUT", step_qty)
                    st.rerun()
                else:
                    st.toast(f"Cannot exit: {cat} count is already 0", icon="⚠️")
