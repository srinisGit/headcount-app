import streamlit as st
from supabase import create_client, Client

# 1. Page Configuration
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

# 2. Touch-Optimized CSS
st.markdown("""
<style>
    .gate-card {
        background: #5f2937;
        border: 2px solid #374151;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 15px;
    }
    .card-header {
        color: #f9fafb;
        font-size: 1.1rem;
        font-weight: 700;
        text-align: center;
        text-transform: uppercase;
        border-bottom: 1px solid #374151;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    .badge-grid {
        display: flex;
        justify-content: space-between;
        margin-bottom: 12px;
        gap: 5px;
    }
    .stat-badge {
        flex: 1;
        background: #111827;
        padding: 6px 4px;
        border-radius: 6px;
        text-align: center;
    }
    .badge-label {
        font-size: 0.68rem;
        color: #9ca3af;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-value {
        font-size: 1.1rem;
        font-weight: 800;
    }
    .val-in { color: #10b981; }
    .val-out { color: #f43f5e; }
    .val-net { color: #38bdf8; }
    
    .stButton>button {
        height: 48px;
        font-weight: bold;
        font-size: 1.05rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Session State & Login Setup
if "logged_user" not in st.session_state:
    st.session_state.logged_user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# --- LOGIN GATEWAY ---
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

# --- TOP BAR ---
c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.markdown(f"👤 **Officer:** `{st.session_state.logged_user.upper()}` ({st.session_state.user_role})")
with c_head2:
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state.logged_user = None
        st.session_state.user_role = None
        st.rerun()

st.divider()

# --- EXACT 9 CATEGORIES ---
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

# --- FETCH DETAILED CATEGORY METRICS FROM SUPABASE ---
def fetch_detailed_metrics():
    metrics = {cat: {"in": 0, "out": 0, "net": 0} for cat in CATEGORIES}
    from datetime import datetime, time

# Fetch logs starting from 00:00:00 today
from datetime import datetime, time

# --- FETCH DETAILED CATEGORY METRICS FROM SUPABASE ---
def fetch_detailed_metrics():
    metrics = {cat: {"in": 0, "out": 0, "net": 0} for cat in CATEGORIES}
    
    # Midnight timestamp for today (00:00:00)
    today_start = datetime.combine(datetime.now().date(), time.min).isoformat()
    
    # Line 135: Make sure this has exactly 4 leading spaces (no extra spaces/tabs)
    res = (
        supabase.table("gate_logs")
        .select("category, movement_type, count_value")
        .gte("created_at", today_start)
        .execute()
    )
    
    if res.data:
        for row in res.data:
            cat = row.get("category")
            if cat in metrics:
                cnt = row.get("count_value", 0) or 0
                if row.get("movement_type") == "IN":
                    metrics[cat]["in"] += cnt
                elif row.get("movement_type") == "OUT":
                    metrics[cat]["out"] += cnt
                
                # Calculate net on site
                metrics[cat]["net"] = max(0, metrics[cat]["in"] - metrics[cat]["out"])
    return metrics
metrics_data = fetch_detailed_metrics()

# Function to record movement
def record_movement(category, movement_type, qty):
    payload = {
        "category": category,
        "movement_type": movement_type,
        "count_value": qty,
        "username": st.session_state.logged_user
    }
    supabase.table("gate_logs").insert(payload).execute()
    st.toast(f"{'➕ IN' if movement_type == 'IN' else '➖ OUT'}: {qty} x {category}", icon="✅")

# --- 3-COLUMN CARD GRID UI ---
st.markdown("### 🚪 Factory Gate Terminal")

cols = st.columns(3)

for idx, cat in enumerate(CATEGORIES):
    col = cols[idx % 3]
    cat_stats = metrics_data.get(cat, {"in": 0, "out": 0, "net": 0})
    
    with col:
        # Card Container with Title + IN / OUT / ON-SITE Breakdown
        st.markdown(f"""
        <div class="gate-card">
            <div class="card-header">{cat}</div>
            <div class="badge-grid">
                <div class="stat-badge">
                    <div class="badge-label">Total IN</div>
                    <div class="badge-value val-in">+{cat_stats['in']}</div>
                </div>
                <div class="stat-badge">
                    <div class="badge-label">Total OUT</div>
                    <div class="badge-value val-out">-{cat_stats['out']}</div>
                </div>
                <div class="stat-badge">
                    <div class="badge-label">On Site</div>
                    <div class="badge-value val-net">{cat_stats['net']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Dedicated Input Field per Card (Defaulting to 1)
        qty_input = st.number_input(
            f"Qty ({cat})", 
            min_value=1, 
            value=1, 
            step=1, 
            key=f"qty_{idx}",
            label_visibility="collapsed"
        )
        
        # Action Buttons (IN & OUT) reading from this card's input field
        btn_in, btn_out = st.columns(2)
        with btn_in:
            if st.button(f"➕ IN", key=f"in_btn_{idx}", type="primary", use_container_width=True):
                record_movement(cat, "IN", qty_input)
                st.rerun()
                
        with btn_out:
            if st.button(f"➖ OUT", key=f"out_btn_{idx}", use_container_width=True):
                if cat_stats['net'] >= qty_input:
                    record_movement(cat, "OUT", qty_input)
                    st.rerun()
                else:
                    st.toast(f"Cannot exit {qty_input} {cat}: Only {cat_stats['net']} on site!", icon="⚠️")
