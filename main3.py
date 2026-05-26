import os
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 0. BOOTSTRAP ENVIRONMENT SECURITY
# Automatically scans for the local .env file and loads variables securely into system memory
load_dotenv()

# Initialize the production core web server application
app = FastAPI(title="Stateful AI UML Engine", version="2.0")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your local frontend tab to read the cloud responses safely
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 1. DATA CONTRACTS (Pydantic Input/Output Schemas) ---

class UMLRequest(BaseModel):
    """Structures the inbound data payload entering our system endpoints."""
    session_id: str = Field(..., example="sebi-compliance-session-444")
    prompt: str = Field(..., example="Build a pipeline where a Web Scraper pulls circular files from SEBI.")
    diagram_types: List[str] = Field(default=["sequence", "flowchart"], example=["sequence", "flowchart"])

class UMLDiagramOutput(BaseModel):
    """Structures an individual compiled graph output entry."""
    diagram_type: str
    mermaid_code: str

class UMLResponse(BaseModel):
    """Structures the explicit schema contract returned over the network to the client."""
    explanation: str
    diagrams: List[UMLDiagramOutput]

class UserFeedbackPayload(BaseModel):
    """Structures the diagnostic training parameters required for the Case 3 Feedback Loop."""
    session_id: str = Field(..., example="sebi-compliance-session-444")
    original_prompt: str = Field(..., example="Build a pipeline where a Web Scraper...")
    generated_mermaid_code: str = Field(..., example="sequenceDiagram...")
    rating: str = Field(..., description="Must be 'thumbs_up' or 'thumbs_down'", example="thumbs_down")
    user_critique: str = Field(default="", example="The system missed the asynchronous queue connection step.")


# --- 2. PERSISTENCE LAYER (Evaluation Pools & Memories) ---

# Global dataset pool serving as our Case 3 raw data lake for offline model tuning
feedback_data_lake: List[Dict] = []    

# In-memory session tracking matrix isolated in system RAM
session_database: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Isolates and routes stateful message ledgers according to tracking tokens."""
    if session_id not in session_database:
        session_database[session_id] = ChatMessageHistory()
    return session_database[session_id]


# --- 3. COGNITIVE PIPELINE CONFIGURATION (LangChain + Gemini 2.5) ---

# Safe operational check to verify the developer added the hidden key credentials file

# UPDATE TO THIS:
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,  # Keeps structural token outputs deterministic
    api_key="AIzaSyB6JVG5ycLr7N1LBTElCR8QddkB5eJ0wpY"  # Paste your real text key token string inside these quotes
)

# Connects the model engine to our Pydantic response contract to enforce structured JSON parameters
structured_llm = llm.with_structured_output(UMLResponse)

# Behavioral prompt setup containing our dynamic context message placeholder slot
prompt_template = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert Principal Systems Architect.\n"
        "Analyze the user's requirements and output clean, syntactically correct Mermaid.js code.\n"
        "Crucial: Look closely at your conversation history. If the user asks for a modification, "
        "update or modify the existing Mermaid code blocks accordingly rather than inventing an entirely new system."
    )),
    MessagesPlaceholder(variable_name="history"),
    ("user", "Target Diagrams to maintain: {diagram_types}\n\nLatest Request: {user_prompt}")
])

core_chain = prompt_template | structured_llm

# Wrap the core generation chain inside LangChain's automatic execution interceptor memory wrapper
stateful_chain = RunnableWithMessageHistory(
    core_chain,
    get_session_history,
    input_messages_key="user_prompt",
    history_messages_key="history"
)


# --- 4. EXPOSING THE INTERACTIVE API ROUTER ENDPOINTS ---

@app.get("/")
async def root_redirect():
    """Forwards root traffic directly to the automated documentation interface."""
    return RedirectResponse(url="/docs")

@app.post("/api/v1/generate", response_model=UMLResponse)
async def generate_uml(payload: UMLRequest):
    """Processes dynamic structural prompts while continuously managing multi-turn session state."""
    try:
        types_str = ", ".join(payload.diagram_types)
        
        result = stateful_chain.invoke(
            {
                "user_prompt": payload.prompt,
                "diagram_types": types_str
            },
            config={"configurable": {"session_id": payload.session_id}}
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stateful Generation Engine Error: {str(e)}")

@app.post("/api/v1/feedback")
async def collect_user_feedback(feedback: UserFeedbackPayload):
    """Captures human preference logs to feed downstream automated model optimization engines."""
    try:
        log_record = {
            "session_id": feedback.session_id,
            "original_prompt": feedback.original_prompt,
            "generated_mermaid_code": feedback.generated_mermaid_code,
            "rating": feedback.rating,
            "user_critique": feedback.user_critique
        }
        feedback_data_lake.append(log_record)
        print(f"📊 [ART LOGGED] Received {feedback.rating} for session {feedback.session_id}. Total records: {len(feedback_data_lake)}")
        return {
            "status": "logged_successfully",
            "message": "Feedback captured for core engine optimization pipelines."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback Engine Logging Failure: {str(e)}")

@app.get("/api/v1/feedback/data-lake")
async def view_feedback_data_lake():
    """Provides a data diagnostic endpoint to review all stored human critique logs."""
    return {"records_stored": len(feedback_data_lake), "data": feedback_data_lake}

@app.get("/health")
async def health_check():
    """Provides an automated operational health ping route confirming backend uptime status."""
    return {"status": "healthy"}


app = app
