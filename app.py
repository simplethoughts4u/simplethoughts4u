from flask import Flask, jsonify, request, send_from_directory
import os
from flask_cors import CORS
import requests
import time

app = Flask(__name__, static_folder="static", static_url_path="/")  # ✅ Define the app here before using it!
CORS(app)  # Enable Cross-Origin Resource Sharing


MAIL_TM_API = "https://api.mail.tm"
SESSION = requests.Session()

def get_domain():
    """Fetches the first available domain from Mail.tm"""
    try:
        response = SESSION.get(f"{MAIL_TM_API}/domains").json()
        if "hydra:member" in response and len(response["hydra:member"]) > 0:
            return response["hydra:member"][0]["domain"]
    except Exception as e:
        print("Error fetching domain:", e)
    return None

def create_temp_email():
    """Generates a new temporary email and returns credentials."""
    domain = get_domain()
    if not domain:
        return None  # No available domains

    email = f"user{int(time.time())}@{domain}"
    password = "randompassword"

    payload = {"address": email, "password": password}
    response = SESSION.post(f"{MAIL_TM_API}/accounts", json=payload)

    if response.status_code == 201:
        token_response = SESSION.post(f"{MAIL_TM_API}/token", json=payload)
        if token_response.status_code == 200:
            token = token_response.json().get("token")
            return {"email": email, "password": password, "token": token}

    return None  # Return None if creation or token fetching fails

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

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
    if not token:
        return jsonify({"error": "Token is required"}), 400

    headers = {"Authorization": f"Bearer {token}"}
    try:
        inbox = SESSION.get(f"{MAIL_TM_API}/messages", headers=headers).json()
        return jsonify(inbox)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch inbox: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port, debug=True)
