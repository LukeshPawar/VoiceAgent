# Riverwood AI Voice Agent

A highly conversational, low-latency AI voice agent built for Riverwood Estate. This agent automates construction updates and site visit scheduling with a warm, human-like personality.

## Features
- **Natural Greetings**: Multi-lingual support starting with a warm "Namaste" greeting.
- **Voice Interaction**: Powered by Twilio Voice and AWS Polly (Neural Aditi voice).
- **Contextual Intelligence**: Uses Groq (Llama 3.3 70B) for instant, human-like reasoning.
- **Stateful Memory**: Remembers user preferences (e.g., visit declines) and full conversation history.
- **FSM Architecture**: Robust node-based routing ensures the conversation remains logical and goal-oriented.

## Tech Stack
- **FastAPI / Python**: High-performance backend.
- **Twilio**: Telephony and STT.
- **Groq (Llama-3.3-70b)**: Lightning-fast LLM inference.
- **AWS Polly**: Natural Neural Text-to-Speech.

## Setup & Running
1. **Install Dependencies**:
   ```bash
   pip install fastapi uvicorn twilio langchain-groq python-dotenv
   ```
2. **Environment Configuration**: Create a `.env` file with:
   - `GROQ_API_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
3. **Start the Server**:
   ```bash
   uvicorn app:app --reload
   ```
4. **Tunneling**:
   ```bash
   ngrok http 8000
   ```
5. **Update Webhook**: Set the Twilio Voice URL to `your-ngrok-url/voice`.
6. **Initiate Call**: `python3 call.py`
