from flask import Flask, jsonify, request
import requests
from flask_cors import CORS  

app = Flask(__name__)

# Allow CORS for localhost React dev server
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST", "OPTIONS"])

CONSUMER_KEY = 'Br9toGU3pWfpg21N3adIO2u95u2RTqXd' 
CONSUMER_SECRET = 'S3AnVcFQ25XmEFRFLuV/Y/S5KG0='
TOKEN_URL = 'https://pay.pesapal.com/v3/api/Auth/RequestToken'
REGISTER_IPN_URL = 'https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN'
GET_IPN_LIST_URL = 'https://pay.pesapal.com/v3/api/URLSetup/GetIpnList'
SUBMIT_ORDER_URL = 'https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest'  
GET_IPN_LIST_URL = "https://pay.pesapal.com/v3/api/URLSetup/GetIpnList"  

# @app.route('/get_token', methods=['POST'])
# def get_token():
#     payload = {
#         'consumer_key': CONSUMER_KEY,
#         'consumer_secret': CONSUMER_SECRET
#     }

#     response = requests.post(TOKEN_URL, json=payload)

#     if response.status_code == 200:
#         data = response.json()
#         return jsonify({
#             'token': data.get('token'),
#             'expiryDate': data.get('expiryDate'),
#             'status': data.get('status'),
#             'message': data.get('message')
#         }), 200
#     else:
#         return jsonify({
#             'error': 'Failed to get token',
#             'status_code': response.status_code,
#             'message': response.text
#         }), 400


# @app.route('/register_ipn', methods=['POST'])
# def register_ipn():
#     # Get token from /get_token route first
#     token = request.json.get('token')  # Token should be passed from the client

#     if not token:
#         return jsonify({'error': 'No token provided'}), 400

#     ipn_url = request.json.get('url')  # IPN URL
#     ipn_notification_type = request.json.get('ipn_notification_type')  # 'GET' or 'POST'

#     if not ipn_url or not ipn_notification_type:
#         return jsonify({'error': 'Missing IPN URL or notification type'}), 400

#     headers = {
#         'Accept': 'application/json',
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {token}',  # Bearer token for authentication
#     }

#     # Payload for registering IPN URL
#     payload = {
#         'url': ipn_url,
#         'ipn_notification_type': ipn_notification_type
#     }

#     # Send the POST request to register the IPN URL
#     response = requests.post(REGISTER_IPN_URL, json=payload, headers=headers)

#     if response.status_code == 200:
#         data = response.json()
#         return jsonify({
#             'url': data.get('url'),
#             'created_date': data.get('created_date'),
#             'ipn_id': data.get('ipn_id'),
#             'ipn_status': data.get('ipn_status'),
#             'status': response.status_code,
#             'message': 'IPN URL registered successfully'
#         }), 200
#     else:
#         return jsonify({
#             'error': 'Failed to register IPN URL',
#             'status_code': response.status_code,
#             'message': response.text
#         }), 400


@app.route('/register_ipn_combined', methods=['POST'])
def register_ipn_combined():
    # Step 1: Get IPN data from client
    ipn_url = request.json.get('url')
    ipn_notification_type = request.json.get('ipn_notification_type')  # 'GET' or 'POST'

    if not ipn_url or not ipn_notification_type:
        return jsonify({'error': 'Missing IPN URL or notification type'}), 400

    # Step 2: Get a token from Pesapal
    token_payload = {
        'consumer_key': CONSUMER_KEY,
        'consumer_secret': CONSUMER_SECRET
    }

    token_response = requests.post(TOKEN_URL, json=token_payload)

    if token_response.status_code != 200:
        return jsonify({
            'error': 'Failed to get token',
            'status_code': token_response.status_code,
            'message': token_response.text
        }), 400

    token_data = token_response.json()
    token = token_data.get('token')

    if not token:
        return jsonify({'error': 'Token not found in response'}), 400

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    # Step 3: Register the IPN using the token
    ipn_payload = {
        'url': ipn_url,
        'ipn_notification_type': ipn_notification_type
    }

    register_response = requests.post(REGISTER_IPN_URL, json=ipn_payload, headers=headers)

    if register_response.status_code != 200:
        return jsonify({
            'error': 'Failed to register IPN URL',
            'status_code': register_response.status_code,
            'message': register_response.text
        }), 400

    ipn_registration_data = register_response.json()

    # Step 4: Get all registered IPNs
    ipn_list_response = requests.get(GET_IPN_LIST_URL, headers=headers)

    if ipn_list_response.status_code != 200:
        return jsonify({
            'error': 'Failed to fetch registered IPNs',
            'status_code': ipn_list_response.status_code,
            'message': ipn_list_response.text
        }), 400

    ipn_list = ipn_list_response.json()

    # Final Response
    return jsonify({
        'token_info': {
            'token': token_data.get('token'),
            'expiryDate': token_data.get('expiryDate'),
            'status': token_data.get('status'),
            'message': token_data.get('message')
        },
        'ipn_registration': {
            'url': ipn_registration_data.get('url'),
            'created_date': ipn_registration_data.get('created_date'),
            'ipn_id': ipn_registration_data.get('ipn_id'),
            'ipn_status': ipn_registration_data.get('ipn_status'),
            'status': register_response.status_code,
            'message': 'IPN URL registered successfully'
        },
        'registered_ipns': ipn_list
    }), 200



BEARER_TOKEN = "YOUR_ACCESS_TOKEN"

@app.route('/submit_order', methods=['POST'])
def submit_order():
    # Step 1: Get the notification ID from your own registered endpoint
    try:
        ipn_response = requests.get('http://127.0.0.1:5000/register_ipn_combined')
        ipn_response.raise_for_status()
        notification_id = ipn_response.json().get('notification_id')
    except Exception as e:
        return jsonify({"error": "Failed to fetch notification_id", "details": str(e)}), 500

    if not notification_id:
        return jsonify({"error": "notification_id is missing"}), 400

    # Step 2: Construct the payload for the SubmitOrderRequest
    payload = {
        "id": "TXN-" + request.json.get("merchant_id", "default-id"),  # Ensure this is always unique
        "currency": "KES",
        "amount": request.json.get("amount", 100.00),
        "description": request.json.get("description", "Sample transaction"),
        "callback_url": "https://yourdomain.com/response",
        "redirect_mode": "TOP_WINDOW",
        "notification_id": notification_id,
        "branch": "Main Store",
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
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(
            "https://cybqa.pesapal.com/pesapalv3/api/Transactions/SubmitOrderRequest",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": "Pesapal API call failed", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
