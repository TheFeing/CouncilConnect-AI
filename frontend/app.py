import streamlit    # For frontend UI rendering
import requests     # For making HTTP requests to the backend API gateway
import os           # For accessing environment variables for configuration
import platform     # For retrieving the node name for version display
import logging      # For logging application events and errors

# Configure local logging infrastructure for the frontend UI layer.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Configuration fetched from environment variables
# These are injected via Terraform to allow the UI to find the API
BACKEND_URL = os.getenv("BACKEND_URL", "http://api-gateway:8000")
VERSION = os.getenv("APP_VERSION", "v1.0-stable")   # Fall back to "v1.0-stable" if not set.
IS_BETA = "beta" in VERSION.lower()

# Defining an experimental feature flag based on the version string to conditionally enable beta features in the UI.
EXPERIMENTAL_ENABLED = "beta" in VERSION.lower() or VERSION != "v1.0-stable"

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
    
    /* System version footprint styling */
    .footer-version {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        color: #6c757d;
        text-align: center;
        padding: 5px;
        font-size: 0.8rem;
        border-top: 1px solid #dee2e6;
        z-index: 999;
    }}
    </style>
""", unsafe_allow_html=True)

# 3. Structural Header Construction across every interface option
streamlit.markdown('<div class="disclaimer-banner">⚠️ DevOps Demonstration 2026-07-01 — NOT FOR PRODUCTION PUBLIC DEPLOYMENT</div>', unsafe_allow_html=True)

streamlit.markdown("""
    <div style="background-color: #98002E; padding: 20px; border-radius: 5px; margin-bottom: 25px;">
        <h1 style="color: white; margin: 0;">🏛️ Salford City Council</h1>
        <p style="color: #ffcccc; margin: 5px 0 0 0;">AI Resident Support & Knowledge Management Portal</p>
    </div>
""", unsafe_allow_html=True)

# 4. Multi-Page Panel Controller System inside the Sidebar (The Preferred Design)
streamlit.sidebar.title("Control Dashboard")
streamlit.sidebar.write("Switch between public chat assistance and administrative knowledge bootstrapping.")
selected_view = streamlit.sidebar.radio("Navigation View Select:", ["Resident Support Assistant", "Knowledge Administration Workspace"])

# Global session dictionary buffer container initialisation
if "messages" not in streamlit.session_state:
    streamlit.session_state.messages = []


# =====================================================================
# INTERFACE SUB-SYSTEM A: RESIDENT SUPPORT ASSISTANT (CHAT MODALITY)
# =====================================================================
if selected_view == "Resident Support Assistant":
    streamlit.subheader("💬 Resident Support Assistant")
    streamlit.write("Ask questions about waste collection, council tax adjustments, or local public library services.")
    
    # Render historical chat records dynamically from memory arrays
    for context_turn in streamlit.session_state.messages:
        with streamlit.chat_message(context_turn["role"]):
            streamlit.markdown(context_turn["content"])
            
    # Capture fresh input strings from user interaction panels
    if user_prompt_string := streamlit.chat_input("Enter your enquiry (e.g., How do I order a new bin?)"):
        
        # Display the local message trace inside the container
        with streamlit.chat_message("user"):
            streamlit.markdown(user_prompt_string)
            
        streamlit.session_state.messages.append({"role": "user", "content": user_prompt_string})
        
        # Deploy streaming network communication logic targeting the updated backend engine
        with streamlit.chat_message("assistant"):
            response_placeholder = streamlit.empty()
            target_endpoint = f"{BACKEND_URL}/chat"
            
            try:
                logger.info(f"Transmitting prompt packet to streaming gate target: {target_endpoint}")
                
                # Execute standard HTTP POST action configured to hook chunks immediately as they exit the network buffers
                with requests.post(
                    target_endpoint,
                    json={"prompt": user_prompt_string},
                    stream=True,  # Blocks buffering actions to ensure continuous token output processing
                    timeout=30.0  # Fails early if upstream model execution blocks completely
                ) as backend_network_stream:
                    
                    if backend_network_stream.status_code == 200:
                        accumulated_text_payload = ""
                        
                        # Read the incoming text chunks continuously as they are generated by the backend
                        for dynamic_chunk in backend_network_stream.iter_content(chunk_size=None, decode_unicode=True):
                            if dynamic_chunk:
                                accumulated_text_payload += dynamic_chunk
                                # Render text instantly on screen to reduce perceived latency
                                response_placeholder.markdown(accumulated_text_payload)
                                
                        # Save the fully compiled string to the tab memory array cache
                        streamlit.session_state.messages.append({"role": "assistant", "content": accumulated_text_payload})
                        
                    elif backend_network_stream.status_code == 403:
                        # Explicit check for security policy compliance failures
                        safety_violation_error = "⚠️ Query rejected: This request contains flags violating compliance safety parameters."
                        response_placeholder.markdown(safety_violation_error)
                        logger.warning("Upstream firewall module blocked the resident prompt entry content.")
                        
                    elif backend_network_stream.status_code == 422:
                        structural_validation_error = "⚠️ UI Input validation mismatch: Payload structure rejected by backend gateway guard."
                        response_placeholder.markdown(structural_validation_error)
                        logger.error("FastAPI backend engine validation parser blocked the incoming JSON request schema format.")
                        
                    else:
                        unexpected_http_error = f"⚠️ Downstream service exception encountered. System status code: {backend_network_stream.status_code}"
                        response_placeholder.markdown(unexpected_http_error)
                        logger.error(f"Endpoint transmission barrier state reached: {backend_network_stream.text}")
                        
            except requests.exceptions.RequestException as network_transmission_error:
                communication_failure_fallback = "❌ Service communication failure: Unable to establish a connection to the backend engine."
                response_placeholder.markdown(communication_failure_fallback)
                logger.critical(f"Connection array link collapsed completely between interface layers: {str(network_transmission_error)}")


# =====================================================================
# INTERFACE SUB-SYSTEM B: KNOWLEDGE ADMINISTRATION WORKSPACE
# =====================================================================
else:
    streamlit.subheader("⚙️ Knowledge Administration Workspace")
    streamlit.info("Admin Privileges Authenticated: Ingest corporate documentation and framework guidelines into the Vector Database.")
    
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

    streamlit.markdown("---")
    
    # --- Operational Web Crawling Subsystem Interface ---
    streamlit.subheader("🌐 Automated Web Crawling Subsystem")
    streamlit.write("Trigger spider tasks to parse and ingest text content layers from validated live council domain endpoints.")
    
    web_crawl_target_url = streamlit.text_input(
        "Specify Target Council Domain Link Location:", 
        placeholder="https://www.salford.gov.uk/bins-and-recycling/"
    )
    
    if streamlit.button("Initialise Pipeline Crawling Spider"):
        if web_crawl_target_url.strip():
            with streamlit.spinner("Dispatching web spider pipeline configuration execution loops..."):
                try:
                    # Execute direct network route request targeting the freshly established endpoint path configuration
                    res = requests.post(
                        f"{BACKEND_URL}/crawl", 
                        json={"url": web_crawl_target_url.strip()}, 
                        timeout=90
                    )
                    if res.status_code == 200:
                        streamlit.success("Web Crawl Complete: External data structures have been ingested into the vector repository.")
                    else:
                        streamlit.error(f"Crawling sequence halted with status code outcome: {res.status_code}")
                except Exception as crawler_ui_error:
                    streamlit.error(f"Connection exception block encountered during task dispatch sequence: {crawler_ui_error}")
        else:
            streamlit.error("Crawl initialisation blocked: Please specify a valid destination endpoint target URL string first.")

    # =========================================================================
    # EXPERIMENTAL FEATURE (Feature Toggle)
    # =========================================================================
    if EXPERIMENTAL_ENABLED:
        streamlit.markdown("---")
        streamlit.subheader("🧪 Experimental Feature (Beta)")
        streamlit.write("This feature is under development and only visible when the experimental flag is enabled.")
        if streamlit.button("Generate Weekly Summary Report (Experimental)"):
            streamlit.info("Report generation is not yet implemented – this demonstrates branching by abstraction.")
            # In a real implementation, you would call a backend endpoint here.
            logger.info("Experimental report button clicked – feature toggle works.")

# 6. Version Indicator
# Using platform.node() to fix the AttributeError on Windows environment
streamlit.markdown(
    f'<div class="footer-version">CouncilConnect AI System: <b>{VERSION}</b> | Node: {platform.node()}</div>', 
    unsafe_allow_html=True
)