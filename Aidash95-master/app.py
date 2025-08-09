import streamlit as st
from pathlib import Path
from login import show_login
from sidebar import show_sidebar
from utils.config import load_config, init_session_state

# Configure Streamlit page
st.set_page_config(
    page_title="Business Management Suite",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = Path("assets/style.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page mapping: keys are labels, values are relative paths inside /pages folder
PAGE_MAPPING = {
    "Dashboard": "Aidash95-master/pages/1_Dashboard.py",
    "Calendar": "Aidash95-master/pages/2_Calendar.py",
    "Invoices": "Aidash95-master/pages/3_Invoices.py",
    "Customers": "Aidash95-master/pages/4_Customers.py",
    "Appointments": "Aidash95-master/pages/5_Appointments.py",
    "Pricing": "Aidash95-master/pages/6_Pricing.py",
    "AI Chat": "Aidash95-master/pages/7_Super_Chat.py",
    "Voice Calls": "Aidash95-master/pages/8_AI_Caller.py",
    "Call Center": "pages/Aidash95-master/9_Call_Center.py",
    "Project Management": "pages/Aidash95-master/10_Project_Management.py"
}

def main():
    load_css()
    load_config()
    init_session_state()

    # Debug info
    st.write("🚀 App started")

    # User login check
    if not st.session_state.get("logged_in", False):
        st.write("🔐 Login required")
        show_login()
        return  # Stop execution if not logged in

    st.write("✅ Logged in")
    show_sidebar()

    # Set default page
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    selected_page = st.session_state.get("current_page", "Dashboard")

    st.write(f"📄 Current page: {selected_page}")

    # Ensure page exists before switching
    if selected_page in PAGE_MAPPING:
        page_path = PAGE_MAPPING[selected_page]
        try:
            # st.switch_page must be called before any other Streamlit commands for clean nav
            if Path(page_path).exists():
                st.switch_page(page_path)
            else:
                st.error(f"❌ Page file not found: {page_path}")
        except st.errors.StreamlitAPIException as e:
            st.error(f"⚠ Navigation error: {e}")
    else:
        st.warning("⚠️ Page not found. Showing fallback dashboard.")
        st.title("📊 Dashboard (Fallback)")
        st.info("Use the sidebar to select a valid page.")

if __name__ == "__main__":
    main()

