from flask import Flask, jsonify, request
import requests
import time

app = Flask(__name__)

MAIL_TM_API = "https://api.mail.tm"
SESSION = requests.Session()

    
def create_temp_email():
    """Generates a new temporary email and returns credentials."""
    domain = SESSION.get(f"{MAIL_TM_API}/domains").json()["hydra:member"][0]["domain"]
    email = f"user{int(time.time())}@{domain}"
    password = "randompassword"

    payload = {"address": email, "password": password}
    response = SESSION.post(f"{MAIL_TM_API}/accounts", json=payload)

    if response.status_code == 201:
        token = SESSION.post(f"{MAIL_TM_API}/token", json=payload).json()["token"]
        return {"email": email, "password": password, "token": token}
    return None

@app.route("/generate-email", methods=["GET"])
def generate_email():
    """Endpoint to generate and return a temporary email."""
    email_data = create_temp_email()
    if email_data:
        return jsonify(email_data)
    return jsonify({"error": "Failed to generate email"}), 500

@app.route("/inbox", methods=["POST"])
def fetch_inbox():
    """Fetches inbox emails for a given email token."""
    token = request.json.get("token")
    headers = {"Authorization": f"Bearer {token}"}
    inbox = SESSION.get(f"{MAIL_TM_API}/messages", headers=headers).json()
    return jsonify(inbox)

if __name__ == "__main__":
    app.run(debug=True)
