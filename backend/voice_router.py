import os
import json
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from retell import Retell

voice_router = APIRouter(prefix="/api/voice")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

RETELL_API_KEY = os.environ.get("RETELL_API_KEY")
retell_client = Retell(api_key=RETELL_API_KEY) if RETELL_API_KEY else None

@voice_router.post("/call")
async def initiate_call(request: Request):
    """
    Trigger an outbound Twilio call to the user.
    """
    payload = await request.json()
    user_phone = payload.get("phone")
    if not user_phone:
        return {"error": "Phone number required"}

    if not TWILIO_ACCOUNT_SID:
        return {"error": "Twilio not configured"}

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        url=os.environ.get("BACKEND_URL", "https://api.careeros.local") + "/api/voice/twilio-webhook",
        to=user_phone,
        from_=TWILIO_PHONE_NUMBER
    )
    return {"call_sid": call.sid}

@voice_router.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    """
    Handle the TwiML response when the user answers.
    Connect them to Retell AI.
    """
    response = VoiceResponse()
    
    # We would normally create a Retell Phone Call here and get the websocket URL
    # response.connect().stream(url=retell_websocket_url)
    
    response.say("Welcome to Career OS Mock Interview. An AI agent will join shortly.")
    return str(response)

@voice_router.websocket("/llm-websocket/{application_id}")
async def llm_websocket(websocket: WebSocket, application_id: str):
    """
    Custom LLM WebSocket for Retell AI.
    Receives transcripts, sends back LLM responses.
    """
    await websocket.accept()
    
    # Mock sending an initial greeting
    greeting = {
        "response_id": 1,
        "content": "Hi there! I have your resume and the job description in front of me. Are you ready to start the interview?",
        "content_complete": True,
        "end_call": False
    }
    await websocket.send_text(json.dumps(greeting))
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            if event["type"] == "transcript":
                user_text = event["transcript"]
                
                # Here we would normally pass `user_text` to LangChain or our LLM agent
                # For now, we echo back a generic response
                response = {
                    "response_id": event.get("response_id", 2),
                    "content": "That is a great answer. Can you tell me more about a time you faced a challenge?",
                    "content_complete": True,
                    "end_call": False
                }
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        print(f"Retell AI disconnected for app {application_id}")
