import streamlit as strl
import streamlit.components.v1 as components
import requests
import uuid

# --- 1. WEB PAGE INITIALIZATION ---
strl.set_page_config(
    page_title="AI UML Architect Dashboard", 
    layout="wide",  # This forces a modern, wide split-screen canvas
    initial_sidebar_state="expanded"
)

strl.title("🧬 Stateful AI UML Systems Architect")
strl.caption("An enterprise-grade platform for real-time compliance tracking and system design.")

# --- 2. MANAGING RUNTIME PERSISTENCE (SESSION STATE) ---
# We use Streamlit's session state memory to give this browser tab a persistent passport ID
if "session_token" not in strl.session_state:
    strl.session_state.session_token = str(uuid.uuid4())  # Generates a clean random tracking ID

if "chat_history_log" not in strl.session_state:
    strl.session_state.chat_history_log = []  # Keeps track of the text lines in the UI chat window

if "latest_compiled_diagrams" not in strl.session_state:
    strl.session_state.latest_compiled_diagrams = None  # Holds the current active charts

# Define the local network address where your FastAPI backend is idling
BACKEND_API_URL = "https://ai-uml-weld.vercel.app/api/v1"


# --- 3. SIDEBAR CONFIGURATION AND META CONTROLS ---
with strl.sidebar:
    strl.header("⚙️ Architecture Controls")
    strl.info(f"**Active Session ID:**\n`{strl.session_state.session_token}`")
    
    # Dropdown multi-select parameter mapping straight to Case 1 requirement lists
    selected_diagrams = strl.multiselect(
        "Target Diagram Blueprints:",
        options=["sequence", "flowchart", "class", "er"],
        default=["sequence", "flowchart"]
    )
    
    strl.markdown("---")
    strl.markdown("### 📊 System Diagnostics")
    
    # Query our backend health check route on the fly
    try:
        health_check = requests.get(f"{BACKEND_API_URL[:-6]}/health").json()
        if health_check.get("status") == "healthy":
            strl.success("Backend Conn: ONLINE")
    except:
        strl.error("Backend Conn: OFFLINE (Run uvicorn!)")


# --- 4. THE SPLIT-SCREEN DASHBOARD LAYOUT ---
left_chat_column, right_canvas_column = strl.columns([1, 1], gap="medium")


# --- LEFT PANEL: THE CONVERSATION LOG GATEWAY ---
with left_chat_column:
    strl.subheader("💬 Interactive Context Canvas")
    
    # Create a scrollable preview area showing past user-assistant conversational cards
    chat_container = strl.container(height=500)
    with chat_container:
        if not strl.session_state.chat_history_log:
            strl.write("_System idling. Input architectural requirements below to generate layout structures._")
        for message in strl.session_state.chat_history_log:
            with strl.chat_message(message["role"]):
                strl.write(message["content"])

    # Captures dynamic entry inputs from the user
    user_prompt_input = strl.chat_input("Ask for a new setup or say 'Modify the diagram to add...'")

    if user_prompt_input:
        # 1. Update the local UI conversation log instantly
        strl.session_state.chat_history_log.append({"role": "user", "content": user_prompt_input})
        with chat_container:
            with strl.chat_message("user"):
                strl.write(user_prompt_input)
                
        # 2. Package parameters into the Pydantic-compliant JSON layout
        network_payload = {
            "session_id": strl.session_state.session_token,
            "prompt": user_prompt_input,
            "diagram_types": selected_diagrams
        }
        
        # 3. Fire the web request across our internal network loop
        with strl.spinner("🧠 Orchestrating system topologies via Gemini..."):
            try:
                backend_response = requests.post(
                    f"{BACKEND_API_URL}/generate", 
                    json=network_payload
                )
                
                if backend_response.status_code == 200:
                    api_data = backend_response.json()
                    
                    # Store the results globally inside the browser context session state
                    strl.session_state.latest_compiled_diagrams = api_data
                    strl.session_state.chat_history_log.append({
                        "role": "assistant", 
                        "content": api_data["explanation"]
                    })
                    
                    # Force a UI refresh to display changes immediately
                    strl.rerun()
                else:
                    strl.error(f"Execution Fault: {backend_response.json().get('detail')}")
            except Exception as e:
                strl.error(f"Network Connection Failed: {str(e)}")


# --- RIGHT PANEL: THE LIVE WORKSPACE CANVAS ---
with right_canvas_column:
    strl.subheader("🎨 Structural Visualization Workspace")
    
    if strl.session_state.latest_compiled_diagrams is None:
        strl.info("💡 Complete structural components appear here once compiled by the core AI engine.")
    else:
        active_data = strl.session_state.latest_compiled_diagrams
        
        # 1. Output the structural explanation paragraph generated by the model
        strl.markdown("### 📝 Architectural Overview")
        strl.write(active_data["explanation"])
        
        strl.markdown("---")
        
        # 2. Iterate dynamically over our structured diagrams array list
        strl.markdown("### 📊 Compiled Charts")
        for diagram in active_data["diagrams"]:
            with strl.expander(f"📐 {diagram['diagram_type'].upper()} DIAGRAM BLUEPRINT", expanded=True):
                
                # Clean up any extra whitespace or formatting artifacts from the backend string
                clean_mermaid_code = diagram['mermaid_code'].strip()

                # Embed the open-source Mermaid CDN script into a sandboxed micro-frame to render the graphic beautifully
                mermaid_html = f"""
                <div class="mermaid" style="display: flex; justify-content: center; align-items: center; background: transparent;">
                    {clean_mermaid_code}
                </div>
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ 
                        startOnLoad: true, 
                        theme: 'dark',
                        securityLevel: 'loose'
                    }});
                </script>
                """

                # Render the graphical vector frame onto your workspace canvas
                components.html(mermaid_html, height=600, scrolling=True)
                
                # Expandable developer tray to grab raw scripts easily
                with strl.popover("📄 View Source Code"):
                    strl.code(diagram["mermaid_code"], language="mermaid")
