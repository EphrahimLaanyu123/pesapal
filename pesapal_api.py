from flask import Flask, jsonify, request
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins=["http://localhost:5174"], methods=["GET", "POST", "OPTIONS"])

CONSUMER_KEY = os.getenv('CONSUMER_KEY', 'Br9toGU3pWfpg21N3adIO2u95u2RTqXd')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET', 'S3AnVcFQ25XmEFRFLuV/Y/S5KG0=')
TOKEN_URL = 'https://pay.pesapal.com/v3/api/Auth/RequestToken'
REGISTER_IPN_URL = 'https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN'
GET_IPN_LIST_URL = 'https://pay.pesapal.com/v3/api/URLSetup/GetIpnList'
SUBMIT_ORDER_URL = 'https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest'

def get_pesapal_token():
    """Retrieves a Pesapal API token."""
    token_payload = {
        'consumer_key': CONSUMER_KEY,
        'consumer_secret': CONSUMER_SECRET
    }
    try:
        token_response = requests.post(TOKEN_URL, json=token_payload)
        token_response.raise_for_status()
        return token_response.json().get('token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
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
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Failed to register IPN URL',
            'details': str(e)
        }), 400

    # Get IPN List
    try:
        ipn_list_response = requests.get(GET_IPN_LIST_URL, headers=headers)
        ipn_list_response.raise_for_status()
        ipn_list = ipn_list_response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Failed to fetch registered IPNs',
            'details': str(e)
        }), 400

    return jsonify({
        'ipn_registration': {
            'url': ipn_registration_data.get('url'),
            'created_date': ipn_registration_data.get('created_date'),
            'ipn_id': ipn_registration_data.get('ipn_id'),
            'ipn_status': ipn_registration_data.get('ipn_status'),
            'status_code': register_response.status_code,
            'message': 'IPN URL registered successfully'
        },
        'registered_ipns': ipn_list
    }), 200

BEARER_TOKEN = os.getenv('BEARER_TOKEN') # It's better to fetch a fresh token before each request if it expires

@app.route('/submit_order', methods=['POST'])
def submit_order():
    token = get_pesapal_token()
    if not token:
        return jsonify({'error': 'Failed to retrieve Pesapal token'}), 401

    payload = {
        "id": f"TXN-{request.json.get('merchant_id', 'default-id')}-{int(time.time())}", # Generate a unique ID
        "currency": request.json.get("currency", "KES"),
        "amount": request.json.get("amount", 90.00),
        "description": request.json.get("description", "Sample transaction"),
        "callback_url": request.json.get("callback_url", "https://yourdomain.com/response"),
        "redirect_mode": request.json.get("redirect_mode", "TOP_WINDOW"),
        "notification_id": request.json.get("notification_id"), # Ensure notification_id is provided in the request
        "branch": request.json.get("branch", "Main Store"),
        "billing_address": {
            "email_address": request.json.get("email", "test@example.com"),
            "phone_number": request.json.get("phone", "0700000000"),
            "country_code": request.json.get("country_code", "KE"),
            "first_name": request.json.get("first_name", "John"),
            "middle_name": request.json.get("middle_name", ""),
            "last_name": request.json.get("last_name", "Doe"),
            "line_1": request.json.get("line_1", "123 Main Street"),
            "line_2": request.json.get("line_2", ""),
            "city": request.json.get("city", "Nairobi"),
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
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Pesapal API call failed", "details": str(e)}), 500

if __name__ == '__main__':
    import time  # Import the time module
    app.run(debug=True)