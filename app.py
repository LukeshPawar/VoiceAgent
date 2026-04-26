import os
import asyncio
from typing import TypedDict
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

app = FastAPI()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=512,
)

KNOWLEDGE = """
RIVERWOOD ESTATE — PROJECT INFO:

PROJECT: Riverwood Estate by Riverwood Projects LLP. 25-acre residential plotted township
in Sector 7, Kharkhauda, Haryana. DDJAY scheme (Deen Dayal Jan Awas Yojana).

PLOTS: Sizes 50, 100, 150, 200 sq yards. Starting ~₹15,000/sq yard. Booking ₹1,00,000.
Flexible EMI options available.

CONSTRUCTION: Boundary wall 80% done. Internal roads being laid. Water pipeline started.
Electricity planning phase. Phase 1 completion Q4 2026.

LOCATION: 5 km from NH-44. Near KMP Expressway. 60 km from Delhi, 40 km from Gurugram.
Next to IMT Kharkhauda (Maruti Suzuki hub). Metro connectivity planned.

AMENITIES: Parks, community center, temple, 24/7 CCTV security. Roads: 30ft, 40ft, 60ft.
Underground drainage & water supply.

LEGAL: DDJAY approved (Haryana Govt), RERA registered, clear title, no litigation.

VISITS: ONLY weekends (Sat/Sun), STRICTLY 10 AM - 5 PM. Free pickup from Kharkhauda bus stand.
"""

class CallState(TypedDict):
    messages: list
    current_step: str
    customer_input: str
    agent_response: str
    visit_day: str
    visit_time: str
    visit_handled: bool
    should_end: bool
    turn_count: int



def run_share_update(state: CallState) -> CallState:
    messages = [
        SystemMessage(content=(
            "You are Riya, a warm, friendly, and helpful customer relationship manager at Riverwood Projects LLP. "
            "You are speaking to a customer on a phone call. Keep your response conversational, natural, and limited to 2-3 SHORT sentences MAX.\n\n"
            "Share this construction update naturally:\n"
            "- Boundary wall 80% complete\n"
            "- Internal roads being laid\n"
            "- Water pipeline work started\n"
            "- Phase 1 completion expected Q4 2026\n\n"
            "After the update, ask if they'd like to schedule a weekend site visit.\n"
            "ALWAYS respond in English unless the customer explicitly speaks Hindi. Never say you are AI."
        )),
        *state["messages"],
        HumanMessage(content=state["customer_input"]),
    ]
    resp = llm.invoke(messages)
    state["messages"].extend([
        HumanMessage(content=state["customer_input"]),
        AIMessage(content=resp.content),
    ])
    state["agent_response"] = resp.content
    state["current_step"] = "share_update"
    state["turn_count"] += 1
    return state


def run_offer_visit(state: CallState) -> CallState:
    messages = [
        SystemMessage(content=(
            "You are Riya, a warm and polite manager from Riverwood Projects on a phone call. Keep it to 1-2 conversational sentences MAX.\n\n"
            "Enthusiastically ask if they want to schedule a site visit. Visits are on weekends only "
            "(Saturday & Sunday), 10 AM to 5 PM. Free pickup from Kharkhauda bus stand.\n"
            "If they already expressed interest, ask which day and preferred time.\n"
            "ALWAYS respond in English unless the customer explicitly speaks Hindi. Never say you are AI."
        )),
        *state["messages"],
        HumanMessage(content=state["customer_input"]),
    ]
    resp = llm.invoke(messages)
    state["messages"].extend([
        HumanMessage(content=state["customer_input"]),
        AIMessage(content=resp.content),
    ])
    state["agent_response"] = resp.content
    state["current_step"] = "offer_visit"
    state["turn_count"] += 1
    return state


def run_confirm_visit(state: CallState) -> CallState:
    messages = [
        SystemMessage(content=(
            "You are Riya, a friendly manager from Riverwood Projects on a phone call. Keep it to 1-2 sentences MAX.\n\n"
            "Helpfully confirm the site visit details:\n"
            "- Day MUST be Saturday or Sunday only. Reject weekdays.\n"
            "- Time MUST be between 10 AM and 5 PM strictly.\n"
            "- If they say 5 PM, suggest coming earlier (3-4 PM) for enough time.\n"
            "- If day or time is invalid, politely correct and suggest alternatives.\n"
            "- Once both are valid, confirm: 'Your visit is booked for [day] at [time]. "
            "We will arrange a free pickup from Kharkhauda bus stand.'\n"
            "ALWAYS respond in English unless the customer explicitly speaks Hindi. Never say you are AI."
        )),
        *state["messages"],
        HumanMessage(content=state["customer_input"]),
    ]
    resp = llm.invoke(messages)
    state["messages"].extend([
        HumanMessage(content=state["customer_input"]),
        AIMessage(content=resp.content),
    ])
    state["agent_response"] = resp.content
    state["current_step"] = "confirm_visit"
    state["turn_count"] += 1

    # Extract visit details
    lower = state["customer_input"].lower()
    if "saturday" in lower or "शनिवार" in lower:
        state["visit_day"] = "Saturday"
    elif "sunday" in lower or "रविवार" in lower:
        state["visit_day"] = "Sunday"

    return state


def run_conversation(state: CallState) -> CallState:
    prompt_visit = "" if state.get("visit_handled") else " or would like to visit the site"
    messages = [
        SystemMessage(content=(
            "You are Riya, a highly knowledgeable and warm manager from Riverwood Projects on a phone call. "
            "Speak naturally and directly address their needs. 2-3 sentences MAX.\n\n"
            f"Answer the customer's question using this knowledge:\n{KNOWLEDGE}\n\n"
            "If the answer is in the knowledge base, give it concisely.\n"
            "If you don't know, say you'll check and call back.\n"
            f"After answering, ask if they have other questions{prompt_visit}.\n"
            "ALWAYS respond in English unless the customer explicitly speaks Hindi. Never say you are AI."
        )),
        *state["messages"],
        HumanMessage(content=state["customer_input"]),
    ]
    resp = llm.invoke(messages)
    state["messages"].extend([
        HumanMessage(content=state["customer_input"]),
        AIMessage(content=resp.content),
    ])
    state["agent_response"] = resp.content
    state["current_step"] = "conversation"
    state["turn_count"] += 1
    return state


def run_anything_else(state: CallState) -> CallState:
    messages = [
        SystemMessage(content=(
            "You are Riya, a helpful and engaging manager from Riverwood Projects. 1-2 sentences MAX.\n\n"
            "Acknowledge their last response (e.g., 'No problem' if they declined a visit, or 'Great' if confirmed). "
            "Then ask if they would like to know any other details about the project (amenities, location, pricing, etc.).\n"
            "ALWAYS respond in English unless the customer explicitly speaks Hindi. Never say you are AI."
        )),
        *state["messages"],
        HumanMessage(content=state["customer_input"]),
    ]
    resp = llm.invoke(messages)
    state["messages"].extend([
        HumanMessage(content=state["customer_input"]),
        AIMessage(content=resp.content),
    ])
    state["agent_response"] = resp.content
    state["current_step"] = "anything_else"
    state["turn_count"] += 1
    return state


def run_goodbye(state: CallState) -> CallState:
    messages = [
        SystemMessage(content=(
            "You are Riya, a warm and polite manager from Riverwood Projects. The call is ending. "
            "Express genuine appreciation for their time in 1 short, friendly sentence and say goodbye warmly. "
            f"{'Visit confirmed for ' + state['visit_day'] + '.' if state.get('visit_day') else ''}\n"
            "ALWAYS respond in English unless the customer explicitly speaks Hindi. Never say you are AI."
        )),
        *state["messages"],
        HumanMessage(content=state["customer_input"]),
    ]
    resp = llm.invoke(messages)
    state["agent_response"] = resp.content
    state["should_end"] = True
    return state


import re

def has_phrase(text: str, phrases: list) -> bool:
    """Helper to do word-boundary matching to prevent 'no' matching 'now'."""
    for p in phrases:
        if p == "?":
            if "?" in text:
                return True
        else:
            if re.search(r'\b' + re.escape(p) + r'\b', text):
                return True
    return False

def route(state: CallState) -> str:
    """Determine which node to run next based on user input + current step."""
    user = state.get("customer_input", "").lower()
    step = state.get("current_step", "greeting")
    turn = state.get("turn_count", 0)

    if turn >= 12:
        return "goodbye"

    bye = ["bye", "goodbye", "no thanks", "not interested", "busy", "later",
           "alvida", "nahi chahiye", "band karo", "bas", "okay bye", "that's all",
           "nothing else", "no no", "nahi nahi", "hang up", "stop", "not as of now"]
    if has_phrase(user, bye) or any(w in user for w in ["nahi chahiye", "band karo", "no thanks", "not as of now"]):
        return "goodbye"

    questions = ["price", "cost", "rate", "kitna", "kya hai", "how much",
                 "where", "kahan", "amenity", "facility", "suvidha",
                 "rera", "legal", "emi", "payment", "plot", "size",
                 "naap", "distance", "dur", "metro", "road", "loan",
                 "when", "kab", "security", "school", "hospital",
                 "market", "registry", "bank", "possession", "?",
                 "what", "which", "kaun", "konsa", "batao", "bataiye",
                 "tell me about", "information"]
    if any(w in user for w in questions):
        return "conversation"

    if step == "greeting":
        no = ["no", "nahi", "nahin", "not now"]
        if has_phrase(user, no):
            return "goodbye"
        return "share_update"

    elif step == "share_update":
        yes = ["yes", "sure", "haan", "ji", "okay", "visit", "dekhna",
               "aana", "come", "saturday", "sunday", "weekend"]
        if has_phrase(user, yes):
            return "confirm_visit"
        no = ["no", "nahi", "nahin", "not now", "later", "baad mein", "not right now"]
        if has_phrase(user, no):
            return "anything_else"
        return "offer_visit"

    elif step == "offer_visit":
        yes = ["yes", "sure", "haan", "ji", "okay", "visit", "dekhna",
               "aana", "come", "saturday", "sunday", "weekend"]
        if has_phrase(user, yes):
            return "confirm_visit"
        no = ["no", "nahi", "nahin", "not now", "later", "baad mein", "not right now"]
        if has_phrase(user, no):
            state["visit_handled"] = True
            return "anything_else"
        return "offer_visit"

    elif step == "confirm_visit":
        state["visit_handled"] = True
        ai_resp = state.get("agent_response", "").lower()
        confirm_words = ["confirmed", "booked", "see you", "milte hain",
                         "तय है", "निर्धारित", "व्यवस्था", "arranged", "arranged from"]
        if any(w in ai_resp for w in confirm_words):
            return "anything_else"
        
        ack = ["ok", "okay", "sure", "thank", "thanks", "great", "perfect",
               "done", "theek", "accha", "shukriya", "dhanyavaad", "dhanyvad",
               "haan", "ji", "good", "fine", "alright"]
        if has_phrase(user, ack):
            return "anything_else"
            
        return "confirm_visit"

    elif step == "anything_else":
        yes = ["yes", "haan", "ji", "tell me", "batao", "what", "kya"]
        if has_phrase(user, yes):
            return "conversation"
        no = ["no", "nahi", "nahin", "bas", "nothing", "that's all", "bye", "goodbye"]
        if has_phrase(user, no):
            return "goodbye"
        return "conversation"

    elif step == "conversation":
        no = ["no", "nahi", "nahin", "not now", "nothing", "that's all", "nope"]
        if has_phrase(user, no):
            return "goodbye"
        if state.get("visit_handled"):
            return "anything_else"
        return "offer_visit"

    return "share_update"


NODE_MAP = {
    "share_update": run_share_update,
    "offer_visit": run_offer_visit,
    "confirm_visit": run_confirm_visit,
    "anything_else": run_anything_else,
    "conversation": run_conversation,
    "goodbye": run_goodbye,
}


def run_one_step(state: CallState) -> CallState:
    """Run exactly ONE node based on the router, then return."""
    next_node = route(state)
    print(f"  Router → {next_node}")
    node_fn = NODE_MAP[next_node]
    return node_fn(state)


sessions: dict[str, CallState] = {}


def get_session(call_sid: str) -> CallState:
    if call_sid not in sessions:
        sessions[call_sid] = {
            "messages": [],
            "current_step": "greeting",
            "customer_input": "",
            "agent_response": "",
            "visit_day": "",
            "visit_time": "",
            "visit_handled": False,
            "should_end": False,
            "turn_count": 0,
        }
    return sessions[call_sid]


@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    get_session(call_sid)

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        speech_timeout="auto",
        timeout=10,
        action=f"/process?call_sid={call_sid}",
        method="POST",
        language="en-IN",
    )

    session = get_session(call_sid)
    if session["turn_count"] == 0:
        gather.say(
            "Hello! This is Riya from Riverwood Projects. "
            "I'm calling to give you a quick update on the construction progress "
            "at Riverwood Estate. Would you like to hear it?",
            voice="Polly.Aditi",
            language="en-IN",
        )
    else:
        gather.say("I'm sorry, I didn't catch that. Could you please repeat?", 
                   voice="Polly.Aditi", language="en-IN")

    response.append(gather)
    response.redirect(f"/reprompt?call_sid={call_sid}", method="POST")
    return Response(str(response), media_type="application/xml")


@app.post("/reprompt")
async def reprompt(request: Request):
    form = await request.form()
    call_sid = form.get("call_sid", form.get("CallSid", "unknown"))
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        speech_timeout="auto",
        timeout=10,
        action=f"/process?call_sid={call_sid}",
        method="POST",
        language="en-IN",
    )
    gather.say("Are you still there? Please tell me if you have any other questions.", 
               voice="Polly.Aditi", language="en-IN")
    response.append(gather)
    response.redirect(f"/reprompt?call_sid={call_sid}", method="POST")
    return Response(str(response), media_type="application/xml")


@app.post("/process")
async def process(request: Request):
    form = await request.form()
    call_sid = form.get("call_sid", form.get("CallSid", "unknown"))
    user_input = form.get("SpeechResult", "").strip()

    if not user_input:
        response = VoiceResponse()
        response.say("Sorry, I couldn't hear you. Could you repeat?",
                     voice="Polly.Aditi", language="en-IN")
        response.redirect(f"/reprompt?call_sid={call_sid}", method="POST")
        return Response(str(response), media_type="application/xml")

    session = get_session(call_sid)
    session["customer_input"] = user_input

    print(f"\n{'='*50}")
    print(f"Call: {call_sid} | Turn: {session['turn_count']} | Step: {session['current_step']}")
    print(f"Customer: {user_input}")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: run_one_step(session))
    sessions[call_sid] = result

    ai_response = result["agent_response"]
    should_end = result["should_end"]

    if len(ai_response) > 500:
        ai_response = ai_response[:500].rsplit(".", 1)[0] + "."

    print(f"Riya: {ai_response}")
    print(f"Next step: {result['current_step']} | End: {should_end}")
    print(f"{'='*50}\n")

    response = VoiceResponse()
    if should_end:
        response.say(ai_response, voice="Polly.Aditi", language="en-IN")
        response.hangup()
    else:
        gather = Gather(
            input="speech",
            speech_timeout="auto",
            timeout=10,
            action=f"/process?call_sid={call_sid}",
            method="POST",
            language="en-IN",
        )
        gather.say(ai_response, voice="Polly.Aditi", language="en-IN")
        response.append(gather)
        response.redirect(f"/reprompt?call_sid={call_sid}", method="POST")

    return Response(str(response), media_type="application/xml")