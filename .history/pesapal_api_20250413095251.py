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


if __name__ == '__main__':
    app.run(debug=True)
