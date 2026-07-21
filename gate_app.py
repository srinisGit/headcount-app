import streamlit as st
from supabase import create_client, Client

# Page setup for mobile optimization
st.set_page_config(page_title="Factory Gate Terminal", page_icon="🪪", layout="centered")

# Initialize Supabase Client
SUPABASE_URL = "https://aqnryhvsltbwhcbnwiyr.supabase.co" # Your verified URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxbnJ5aHZzbHRid2hjYm53aXlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzODM0NDksImV4cCI6MjA5OTk1OTQ0OX0.yBtM42rPhi1NmzJib4IemeJ9pzZpUROI2zLKVpb4C8s"          # Replace with your actual Anon Key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# --- LOGIN SCREEN ---
if not st.session_state.logged_user:
    st.title("🪪 Gate Terminal Login")
    with st.form("gate_login"):
        user_input = st.text_input("Username").lower().strip()
        pass_input = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submit_login:
            # Authenticate against Supabase app_users table
            response = supabase.table("app_users") \
                .select("*") \
                .eq("username", user_input) \
                .eq("password", pass_input) \
                .execute()
            
            if response.data:
                user_data = response.data[0]
                if user_data.get("app_type") in ["gate", "both"]:
                    st.session_state.logged_user = user_data["username"]
                    st.session_state.user_role = user_data["role"]
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Unauthorized: User does not have access to Gate Terminal.")
            else:
                st.error("Invalid Username or Password.")
    st.stop()

# --- MAIN GATE INTERFACE ---
st.markdown(f"👤 **Logged in as:** `{st.session_state.logged_user}` ({st.session_state.user_role})")

if st.button("🔒 Logout", type="secondary"):
    st.session_state.logged_user = None
    st.session_state.user_role = None
    st.rerun()

st.divider()
st.subheader("🚪 Headcount Gate Entry")

# Updated categories list including Civil Workers
categories = [
    "Permanent Staff", 
    "Contract Workers", 
    "Civil Workers", 
    "Visitors", 
    "Drivers/Cleaners", 
    "Transporters", 
    "Subcontractors", 
    "Apprentices"
]

selected_cat = st.selectbox("Select Category", categories)
count_val = st.number_input("Number of Persons", min_value=1, value=1, step=1)

col1, col2 = st.columns(2)

# Record IN Entry
with col1:
    if st.button("➕ ENTRY (IN)", type="primary", use_container_width=True):
        data_payload = {
            "category": selected_cat,
            "movement_type": "IN",          # <--- Matched to your column name
            "count_value": count_val,        # <--- Matched to your column name
            "username": st.session_state.logged_user
        }
        supabase.table("gate_logs").insert(data_payload).execute()
        st.success(f"Recorded +{count_val} {selected_cat} by {st.session_state.logged_user}")

# Record OUT Entry
with col2:
    if st.button("➖ EXIT (OUT)", use_container_width=True):
        data_payload = {
            "category": selected_cat,
            "movement_type": "OUT",         # <--- Matched to your column name
            "count_value": count_val,        # <--- Matched to your column name
            "username": st.session_state.logged_user
        }
        supabase.table("gate_logs").insert(data_payload).execute()
        st.info(f"Recorded -{count_val} {selected_cat} by {st.session_state.logged_user}")