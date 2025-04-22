from flask import Flask, jsonify, request
import requests
from flask_cors import CORS  

app = Flask(__name__)

# Allow CORS for localhost React dev server
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST", "OPTIONS"])

CONSUMER_KEY = 'Br9toGU3pWfpg21N3adIO2u95u2RTqXd' 
CONSUMER_SECRET = 'S3AnVcFQ25XmEFRFLuV/Y/S5KG0='
TOKEN_URL = 'https://pay.pesapal.com/v3/api/Auth/RequestToken'
REGISTER_IPN_URL = 'https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN'  # Production URL
GET_IPN_LIST_URL = 'https://pay.pesapal.com/v3/api/URLSetup/GetIpnList'  # Production URL
# Use the demo/sandbox URL if testing in the sandbox environment
# GET_IPN_LIST_URL = 'https://cybqa.pesapal.com/pesapalv3/api/URLSetup/GetIpnList'
SUBMIT_ORDER_URL = 'https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest'  
GET_IPN_LIST_URL = "https://cybqa.pesapal.com/pesapalv3/api/URLSetup/GetIpnList"  

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

    # Step 3: Register the IPN using the token
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    ipn_payload = {
        'url': ipn_url,
        'ipn_notification_type': ipn_notification_type
    }

    register_response = requests.post(REGISTER_IPN_URL, json=ipn_payload, headers=headers)

    if register_response.status_code == 200:
        ipn_data = register_response.json()
        return jsonify({
            'token_info': {
                'token': token_data.get('token'),
                'expiryDate': token_data.get('expiryDate'),
                'status': token_data.get('status'),
                'message': token_data.get('message')
            },
            'ipn_registration': {
                'url': ipn_data.get('url'),
                'created_date': ipn_data.get('created_date'),
                'ipn_id': ipn_data.get('ipn_id'),
                'ipn_status': ipn_data.get('ipn_status'),
                'status': register_response.status_code,
                'message': 'IPN URL registered successfully'
            }
        }), 200
    else:
        return jsonify({
            'error': 'Failed to register IPN URL',
            'status_code': register_response.status_code,
            'message': register_response.text
        }), 400


if __name__ == '__main__':
    app.run(debug=True)
