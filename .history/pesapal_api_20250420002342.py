from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST", "OPTIONS"])

CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
TOKEN_URL = 'https://pay.pesapal.com/v3/api/Auth/RequestToken'
REGISTER_IPN_URL = 'https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN'
GET_IPN_LIST_URL = 'https://pay.pesapal.com/v3/api/URLSetup/GetIpnList'
SUBMIT_ORDER_URL = 'https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest'

# In a real application, you would store this in a database
REGISTERED_IPN_ID = None

def get_pesapal_token():
    """Retrieves a Pesapal API token."""
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        print("Error: CONSUMER_KEY or CONSUMER_SECRET not set in environment variables.")
        return None

    token_payload = {
        'consumer_key': CONSUMER_KEY,
        'consumer_secret': CONSUMER_SECRET
    }
    try:
        token_response = requests.post(TOKEN_URL, json=token_payload)
        token_response.raise_for_status()
        token_data = token_response.json()
        print("Pesapal Token Response:", token_data)
        return token_data.get('token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
        if token_response is not None:
            print(f"Token Response Status Code: {token_response.status_code}")
            print(f"Token Response Content: {token_response.text}")
        return None

@app.route('/register_ipn', methods=['POST'])
def register_ipn():
    ipn_url = request.json.get('url')
    ipn_notification_type = request.json.get('ipn_notification_type')

    if not ipn_url or not ipn_notification_type:
        return jsonify({'error': 'Missing IPN URL or notification type'}), 400

    token = get_pesapal_token()
    if not token:
        return jsonify({'error': 'Failed to retrieve Pesapal token'}), 401

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    ipn_payload = {
        'url': ipn_url,
        'ipn_notification_type': ipn_notification_type
    }
    try:
        register_response = requests.post(REGISTER_IPN_URL, json=ipn_payload, headers=headers)
        register_response.raise_for_status()
        ipn_registration_data = register_response.json()
        print("Pesapal Register IPN Response:", ipn_registration_data)
        global REGISTERED_IPN_ID
        REGISTERED_IPN_ID = ipn_registration_data.get('ipn_id')
        return jsonify({'message': 'IPN URL registered successfully', 'ipn_id': REGISTERED_IPN_ID}), 200
    except requests.exceptions.RequestException as e:
        print(f"Error registering IPN: {e}")
        if register_response is not None:
            print(f"Register Response Status Code: {register_response.status_code}")
            print(f"Register Response Content: {register_response.text}")
        return jsonify({'error': 'Failed to register IPN URL', 'details': str(e)}), 400

@app.route('/get_registered_ipn_id', methods=['GET'])
def get_registered_ipn_id():
    """Returns the stored registered IPN ID."""
    if REGISTERED_IPN_ID:
        return jsonify({'ipn_id': REGISTERED_IPN_ID}), 200
    else:
        return jsonify({'error': 'IPN ID not yet registered'}), 404

@app.route('/submit_order', methods=['POST'])
def submit_order():
    token = get_pesapal_token()
    if not token:
        return jsonify({'error': 'Failed to retrieve Pesapal token'}), 401

    ipn_id = REGISTERED_IPN_ID
    if not ipn_id:
        return jsonify({'error': 'IPN ID not available. Ensure it has been registered.'}), 400

    payload = {
        "id": f"TXN-{request.json.get('merchant_id', 'default-id')}-{int(time.time())}",
        "currency": request.json.get("currency", "KES"),
        "amount": request.json.get("amount", 0.00),
        "description": request.json.get("description", "E-commerce Order"),
        "callback_url": request.json.get("callback_url", f"{request.headers.get('Origin', 'http://localhost:5173')}/payment-callback"),
        "redirect_mode": request.json.get("redirect_mode", "TOP_WINDOW"),
        "notification_id": ipn_id,
        "branch": request.json.get("branch", "Online Store"),
        "billing_address": {
            "email_address": request.json.get("email", ""),
            "phone_number": request.json.get("phone", ""),
            "country_code": request.json.get("country_code", "KE"),
            "first_name": request.json.get("first_name", ""),
            "middle_name": request.json.get("middle_name", ""),
            "last_name": request.json.get("last_name", ""),
            "line_1": request.json.get("line_1", ""),
            "line_2": request.json.get("line_2", ""),
            "city": request.json.get("city", ""),
            "state": request.json.get("state", ""),
            "postal_code": request.json.get("postal_code", ""),
            "zip_code": request.json.get("zip_code", "")
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(SUBMIT_ORDER_URL, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        print("Pesapal Submit Order Response:", response_data)
        return jsonify(response_data)
    except requests.exceptions.RequestException as e:
        print(f"Pesapal API Error: {e}")
        if response is not None:
            print(f"Submit Order Response Status Code: {response.status_code}")
            print(f"Submit Order Response Content: {response.text}")
        return jsonify({"error": "Pesapal API call failed", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)