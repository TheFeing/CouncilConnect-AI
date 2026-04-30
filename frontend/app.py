import streamlit    # For frontend UI rendering
import requests     # For making HTTP requests to the backend API gateway
import os           # For accessing environment variables for configuration
import platform     # For retrieving the node name for version display

# 1. Configuration fetched from environment variables (S16)
# These are injected via Terraform to allow the UI to find the API
BACKEND_URL = os.getenv("BACKEND_URL", "http://api-gateway:8000")
VERSION = os.getenv("APP_VERSION", "v1.0-stable")
IS_BETA = "beta" in VERSION.lower()

streamlit.set_page_config(
    page_title="Salford City Council - Resident Support Prototype",
    page_icon="🏛️",
    layout="wide"
)

# 2. Custom CSS Injection (Branding & Disclaimer)
# Mimicking the Salford City Council colour palette and typography
streamlit.markdown(f"""
    <style>
    /* Main background and branding */
    .main {{ background-color: #f8f9fa; }}
    .stHeader {{ background-color: #98002E; color: white; padding: 1.5rem; }}
    
    /* Project Disclaimer Banner (Crucial for Assessment) */
    .disclaimer-banner {{
        background-color: #ffcc00;
        color: black;
        padding: 15px;
        text-align: center;
        font-weight: bold;
        border-bottom: 2px solid #000;
        margin-bottom: 25px;
        font-size: 1.1rem;
    }}
    
    /* Versioning and Monitoring Footer (K11/S17) */
    .footer-version {{
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 0.85rem;
        color: #666;
        background: rgba(255,255,255,0.9);
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #ddd;
        z-index: 100;
    }}
    
    /* Salford Red Button Styling */
    div.stButton > button:first-child {{
        background-color: #98002E;
        color: white;
        border-radius: 5px;
    }}
    
    /* Chat message bubble refinement */
    .chat-bubble-container {{
        border-left: 5px solid {"#28a745" if IS_BETA else "#98002E"};
        padding-left: 10px;
    }}
    </style>
    
    <div class="disclaimer-banner">
        PROTOTYPE: This is a DevOps Apprenticeship project. This is NOT an official Salford City Council service. 
        Data entered is for demonstration purposes only.
    </div>
""", unsafe_allow_html=True)

# 3. Navigation Sidebar
with streamlit.sidebar:
    # Use clean URL string to resolve MediaFileStorageError
    streamlit.image("https://www.salford.gov.uk/assets/images/scc.png", width=200)
    streamlit.divider()
    page = streamlit.radio("Site Navigation", ["Resident Home", "Internal Admin Portal"])
    streamlit.divider()
    streamlit.info(f"Environment: {'BETA' if IS_BETA else 'PRODUCTION'}")
    streamlit.write("---")
    streamlit.write("Current Instance Health: ✅")

# 4. Page Logic
if page == "Resident Home":
    streamlit.title("Welcome to Salford City Council")
    streamlit.subheader("Your local services, automated and accessible.")
    
    # Mocking standard council navigation tiles
    col1, col2, col3 = streamlit.columns(3)
    with col1:
        with streamlit.container(border=True):
            streamlit.markdown("### 🗑️ Bin Collections")
            streamlit.write("Find your next collection date or report a missed bin.")
    with col2:
        with streamlit.container(border=True):
            streamlit.markdown("### 🏠 Council Tax")
            streamlit.write("Pay your bill, apply for a discount, or change address.")
    with col3:
        with streamlit.container(border=True):
            streamlit.markdown("### 📑 Planning")
            streamlit.write("Search, view, and comment on planning applications.")

    streamlit.markdown("---")
    
    # 5. AI Assistant Section (The Core RAG Integration)
    streamlit.header("CouncilConnect AI Assistant")
    streamlit.write("Ask our AI about council policies, local services, or general enquiries.")
    
    if "messages" not in streamlit.session_state:
        streamlit.session_state.messages = []

    # Display chat history from session state
    for message in streamlit.session_state.messages:
        with streamlit.chat_message(message["role"]):
            streamlit.markdown(message["content"])

    # User query input handling
    if prompt := streamlit.chat_input("How can I help you today?"):
        streamlit.session_state.messages.append({"role": "user", "content": prompt})
        with streamlit.chat_message("user"):
            streamlit.markdown(prompt)

        with streamlit.chat_message("assistant"):
            try:
                # Synchronous request to the backend API gateway
                response = requests.post(
                    f"{BACKEND_URL}/chat", 
                    json={"prompt": prompt},
                    timeout=30
                )
                if response.status_code == 200:
                    msg = response.json().get("response", "No response found.")
                else:
                    msg = f"Error: The assistant returned status {response.status_code}."
            except Exception as e:
                msg = f"System Error: Unable to reach the AI service. Details: {e}"
            
            streamlit.markdown(msg)
            streamlit.session_state.messages.append({"role": "assistant", "content": msg})

elif page == "Internal Admin Portal":
    streamlit.title("Knowledge Base Management")
    streamlit.markdown("#### Operational Dashboard")
    streamlit.warning("This area is restricted to internal staff. Changes here update the AI Knowledge Base in real-time.")
    
    streamlit.subheader("Update Council Knowledge")
    streamlit.write("Upload official PDF policies to index them into the Vector Database.")
    
    uploaded_file = streamlit.file_uploader("Upload Policy PDF Document", type=["pdf"])
    
    if uploaded_file is not None:
        streamlit.info(f"File detected: {uploaded_file.name}")
        if streamlit.button("Index and Redact Document"):
            # Prepare the file for multipart upload to the backend
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')}
            with streamlit.spinner("Processing document (Redacting PII and generating embeddings)..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/ingest", files=files, timeout=90)
                    if res.status_code == 200:
                        streamlit.success("Ingestion Complete: The AI is now updated with the new policy information.")
                    else:
                        streamlit.error(f"Ingestion failed with status: {res.status_code}")
                except Exception as e:
                    streamlit.error(f"Connection error to ingestion service: {e}")

# 6. Version Indicator (K11/S17 Observability)
# Using platform.node() to fix the AttributeError on Windows environment
streamlit.markdown(
    f'<div class="footer-version">CouncilConnect AI System: <b>{VERSION}</b> | Node: {platform.node()}</div>', 
    unsafe_allow_html=True
)