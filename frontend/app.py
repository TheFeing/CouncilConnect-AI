import streamlit    # For frontend UI rendering
import requests     # For making HTTP requests to the backend API gateway
import os           # For accessing environment variables for configuration
import logging      # For logging application events and errors

# Configure local logging infrastructure for the frontend UI layer.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetch the backend service URL location from container environment variables.
# Defaulting to localhost if running outside of the Azure Container App environment.
BACKEND_TARGET = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

streamlit.set_page_config(
    page_title="Council Resident Support AI",
    page_icon="🤖",
    layout="centered"
)

streamlit.title("🤖 Council Resident Support AI")
streamlit.caption("Automated assistance hub for local resident queries, compliance routing, and general council guidance.")

# --- Browser Session State Initialisation ---
# Because web interactions are stateless, Streamlit uses streamlit.session_state to keep chat history alive inside the browser tab memory container.
if "conversation_history" not in streamlit.session_state:
    streamlit.session_state.conversation_history = []

# Display previous conversation dialogue entries stored in browser memory cache.
for conversation_turn in streamlit.session_state.conversation_history:
    with streamlit.chat_message(conversation_turn["role"]):
        streamlit.markdown(conversation_turn["content"])

# --- Main Interaction Input Component ---
if user_input_prompt := streamlit.chat_input("How can the council assist with an enquiry today?"):
    
    # 1. Instantly render the citizen's query locally in the UI window.
    with streamlit.chat_message("user"):
        streamlit.markdown(user_input_prompt)
        
    # Append the user turn to browser memory cache so it survives the next re-run event.
    streamlit.session_state.conversation_history.append({"role": "user", "content": user_input_prompt})

    # 2. Trigger communication lane to the FastAPI backend container.
    with streamlit.chat_message("assistant"):
        response_placeholder = streamlit.empty()
        
        # Package payload packet according to the strict QueryRequest Pydantic template rules.
        request_payload = {"prompt": user_input_prompt}
        target_endpoint = f"{BACKEND_TARGET}/chat"
        
        try:
            logger.info(f"Transmitting operational payload packet to endpoint target: {target_endpoint}")
            
            # Post the data across the private network bridge container boundary.
            network_response = requests.post(
                target_endpoint,
                json=request_payload,
                timeout=30.0  # Safe boundary window for upstream model processing latency.
            )
            
            # Check for gateway perimeter errors or structural validation rejections.
            if network_response.status_code == 200:
                extracted_data = network_response.json()
                final_ai_output = extracted_data.get("response", "Error: Backend payload mapping anomaly encountered.")
                
                # Render the final text string clearly into the presentation interface.
                response_placeholder.markdown(final_ai_output)
                
                # Commit assistant turn to browser memory history cache.
                streamlit.session_state.conversation_history.append({"role": "assistant", "content": final_ai_output})
                
            elif network_response.status_code == 422:
                error_message = "⚠️ UI Input validation mismatch: Payload structure rejected by backend gateway guard."
                response_placeholder.markdown(error_message)
                logger.error("FastAPI perimeter gate rejected frontend data format payload configuration.")
                
            else:
                error_message = f"⚠️ Downstream service exception encountered. System status code: {network_response.status_code}"
                response_placeholder.markdown(error_message)
                logger.error(f"Unexpected endpoint transmission barrier state: {network_response.text}")
                
        except requests.exceptions.RequestException as network_error:
            fallback_message = "❌ Service communication failure: Unable to establish a connection to the backend engine."
            response_placeholder.markdown(fallback_message)
            logger.critical(f"Network bridge connection sequence collapsed entirely: {str(network_error)}")