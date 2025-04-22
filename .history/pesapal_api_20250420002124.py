from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST", "OPTIONS"])

CONSUMER_KEY = os.getenv('CONSUMER_KEY', 'Br9toGU3pWfpg21N3adIO2u95u2RTqXd')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET', 'S3AnVcFQ25XmEFRFLuV/Y/S5KG0=')
TOKEN_URL = 'https://pay.pesapal.com/v3/api/Auth/RequestToken'
REGISTER_IPN_URL = 'https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN'
GET_IPN_LIST_URL = 'https://pay.pesapal.com/v3/api/URLSetup/GetIpnList'
SUBMIT_ORDER_URL = 'https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest'

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

@app.route('/register_ipn_combined', methods=['POST'])
def register_ipn_combined():
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

    # Register IPN
    ipn_payload = {
        'url': ipn_url,
        'ipn_notification_type': ipn_notification_type
    }
    try:
        register_response = requests.post(REGISTER_IPN_URL, json=ipn_payload, headers=headers)
        register_response.raise_for_status()
        ipn_registration_data = register_response.json()
        print("Pesapal Register IPN Response:", ipn_registration_data)
    except requests.exceptions.RequestException as e:
        print(f"Error registering IPN: {e}")
        if register_response is not None:
            print(f"Register Response Status Code: {register_response.status_code}")
            print(f"Register Response Content: {register_response.text}")
        return jsonify({
            'error': 'Failed to register IPN URL',
            'details': str(e)
        }), 400

    # Get IPN List
    try:
        ipn_list_response = requests.get(GET_IPN_LIST_URL, headers=headers)
        ipn_list_response.raise_for_status()
        ipn_list = ipn_list_response.json()
        print("Pesapal Get IPN List Response:", ipn_list)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IPN list: {e}")
        if ipn_list_response is not None:
            print(f"IPN List Response Status Code: {ipn_list_response.status_code}")
            print(f"IPN List Response Content: {ipn_list_response.text}")
        return jsonify({
            'error': 'Failed to fetch registered IPNs',
            'details': str(e)
        }), 400

    return jsonify({
        'ipn_registration': ipn_registration_data,
        'registered_ipns': ipn_list
    }), 200

@app.route('/submit_order', methods=['POST'])
def submit_order():
    token = get_pesapal_token()
    if not token:
        return jsonify({'error': 'Failed to retrieve Pesapal token'}), 401

    payload = {
        "id": f"TXN-{request.json.get('merchant_id', 'default-id')}-{int(time.time())}",
        "currency": request.json.get("currency", "KES"),
        "amount": request.json.get("amount", 0.00), # Ensure a default value
        "description": request.json.get("description", "E-commerce Order"),
        "callback_url": request.json.get("callback_url", "https://yourdomain.com/payment-callback"), # Replace with your actual callback URL
        "redirect_mode": request.json.get("redirect_mode", "TOP_WINDOW"),
        "notification_id": request.json.get("notification_id"), # Ensure this is being passed correctly from the frontend
        "branch": request.json.get("branch", "Online Store"),
        "billing_address": {
            "email_address": request.json.get("email", ""), # Ensure email is passed
            "phone_number": request.json.get("phone", ""),   # Consider making this required
            "country_code": request.json.get("country_code", "KE"),
            "first_name": request.json.get("first_name", ""), # Consider making this required
            "middle_name": request.json.get("middle_name", ""),
            "last_name": request.json.get("last_name", ""),   # Consider making this required
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
        print("Pesapal Submit Order Response:", response_data) # Log the response
        return jsonify(response_data)
    except requests.exceptions.RequestException as e:
        print(f"Pesapal API Error: {e}")
        if response is not None:
            print(f"Submit Order Response Status Code: {response.status_code}")
            print(f"Submit Order Response Content: {response.text}")
        return jsonify({"error": "Pesapal API call failed", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)