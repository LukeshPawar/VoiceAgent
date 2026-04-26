import os
from twilio.rest import Client

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_phone = os.environ.get("TWILIO_PHONE")
user_phone = os.environ.get("USER_PHONE")

client = Client(account_sid, auth_token)

try:
    call = client.calls.create(
        to=user_phone,
        from_=twilio_phone,
        url="https://melia-endothermic-prandially.ngrok-free.dev/voice"
    )

    print("Call started:", call.sid)

except Exception as e:
    print("Error starting call:", e)