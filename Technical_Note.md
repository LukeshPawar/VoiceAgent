# Technical Note: Architecture & Scaling Strategy

## System Architecture Overview
The Riverwood AI Agent is designed as a **State-Machine Driven Voice Webhook** system.

- **Telephony Layer**: Twilio handles the voice connection and stream. It uses `<Gather>` with `speech_timeout="auto"` to perform real-time Speech-to-Text (STT).
- **Logic & Routing**: A FastAPI server maintains a unique session for every `CallSid`. It utilizes a Finite State Machine (FSM) to route users between construction updates, Q&A, and site visit scheduling.
- **Inference Layer**: The system uses Groq (Llama 3.3 70B) to generate contextual responses. Groq's low-latency inference is critical for maintaining a "human" conversational speed.
- **Synthesis Layer**: AWS Polly (Neural engine) converts text back to speech using the `en-IN` voice (Aditi), ensuring the accent feels natural to the target demographic.
- **Contextual Memory**: A local session store preserves the message history and specific user flags (like `visit_handled`), allowing for logical follow-ups.

---

## Technical Thinking: Scaling to 1000 Calls
If Riverwood needs to trigger 1,000 calls every morning, the infrastructure must move from a single-process script to a distributed system.

### 1. Distributed Task Queue
We would implement a worker-consumer model using **Celery with Redis**.
- An "Initiator" script creates 1,000 tasks in the queue.
- Multiple celery workers pick up these tasks and call the Twilio REST API in parallel.

### 2. Scalable Webhook Backend
To handle 1,000 simultaneous webhooks when customers answer:
- **Load Balancing**: Deploy the FastAPI app behind an ALB (Application Load Balancer) or use Kubernetes (K8s) to auto-scale pods based on traffic.
- **Serverless Alternative**: Deploy the `/process` logic as AWS Lambda functions to handle burst traffic without maintaining idle servers.

### 3. Rate Limit Management
- **Twilio CPS**: Standard Twilio accounts are limited to 1 Call Per Second (CPS). We would request a CPS increase (e.g., 50 CPS) to finish the 1,000 calls in ~20 seconds rather than 16 minutes.
- **Session Persistence**: Move the `sessions` dictionary from RAM to a **Redis** cluster. This allows state sharing across multiple server instances.

---

## Estimated Infrastructure Cost (per 1000 calls)
*Based on 2.5 minutes average call duration.*

| Service | Rate | Total Cost |
| :--- | :--- | :--- |
| **Twilio Voice** | $0.013/min × 2.5 min × 1000 | ~$32.50 |
| **Groq (LLM)** | $0.60/1M tokens (Llama 70B) | ~$0.60 |
| **AWS Polly (TTS)** | $16 per 1M characters (Neural) | ~$3.00 |
| **Cloud Hosting** | Lambda execution / Redis | ~$1.50 |
| **Total** | | **~$37.60** |
