from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST", "OPTIONS"])

CONSUMER_KEY = os.getenv('CONSUMER_KEY', 'Br9toGU3pWfpg21N3adIO2u95u2RTqXd') CONSUMER_SECRET = os.getenv('CONSUMER_SECRET', 'S3AnVcFQ25XmEFRFLuV/Y/S5KG0=')
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

@app.route('/checkout', methods=['POST'])
def checkout():
    """Handles the checkout process."""
    cart_items_data = request.json.get('cartItems')
    user_details = request.json.get('userDetails')
    callback_url = request.json.get('callbackUrl')
    ipn_url = request.json.get('ipnUrl')  # Ensure you have an IPN URL

    if not cart_items_data or not isinstance(cart_items_data, list) or not user_details or not callback_url or not ipn_url:
        return jsonify({'error': 'Invalid checkout data provided'}), 400

    if not cart_items_data:
        return jsonify({'error': 'Your cart is empty'}), 400

    total_amount = sum(item['product']['price'] * item['quantity'] for item in cart_items_data)

    token = get_pesapal_token()
    if not token:
        return jsonify({'error': 'Failed to retrieve Pesapal token'}), 401

    # Generate a unique order ID (you might want to use your database ID)
    order_id = f"ORDER-{user_details.get('id', 'guest')}-{int(time.time())}"

    payload = {
        "id": order_id,
        "currency": "KES",  # Assuming your currency is KES
        "amount": total_amount,
        "description": "Payment for items in cart",
        "callback_url": callback_url,
        "redirect_mode": "TOP_WINDOW",
        "notification_id": ipn_url,  # Use the provided IPN URL here
        "branch": "Online Store",
        "billing_address": {
            "email_address": user_details.get("email") or "guest@example.com",
            "phone_number": user_details.get("phone") or "0700000000",
            "country_code": user_details.get("country_code") or "KE",
            "first_name": user_details.get("firstName") or "Guest",
            "middle_name": user_details.get("middleName") or "",
            "last_name": user_details.get("lastName") or "User",
            "line_1": user_details.get("addressLine1") or "Online Address",
            "line_2": user_details.get("addressLine2") or "",
            "city": user_details.get("city") or "Nairobi",
            "state": user_details.get("state") or "",
            "postal_code": user_details.get("postalCode") or "",
            "zip_code": user_details.get("zipCode") or ""
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
        pesapal_response = response.json()
        # You might want to save the order details in your database here
        return jsonify(pesapal_response)
    except requests.exceptions.RequestException as e:
        print(f"Error submitting order to Pesapal: {e}")
        return jsonify({"error": "Failed to initiate Pesapal payment", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)