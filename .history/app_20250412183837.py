from flask import Flask, request, jsonify
import requests
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS



app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])
# Pesapal API configuration
PESAPAL_CONFIG = {
    'sandbox': Fa,
    'consumer_key': 'Br9toGU3pWfpg21N3adIO2u95u2RTqXd',
    'consumer_secret': 'S3AnVcFQ25XmEFRFLuV/Y/S5KG0=',
    'callback_url': 'http://localhost:3000/payment-callback',
    'ipn_url': 'http://your-server-ipn-endpoint',
}

# Mock database for products and orders
products = [
    {"id": 1, "name": "Product 1", "price": 1, "description": "Description for Product 1"},
    {"id": 2, "name": "Product 2", "price": 20.50, "description": "Description for Product 2"},
    {"id": 3, "name": "Product 3", "price": 15.75, "description": "Description for Product 3"},
]

orders = {}

def get_access_token():
    # Use live URL for production environment
    url = 'https://pay.pesapal.com/v3/api/Auth/RequestToken' if not PESAPAL_CONFIG['sandbox'] else 'https://cybqa.pesapal.com/pesapalv3/api/Auth/RequestToken'
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'consumer_key': PESAPAL_CONFIG['consumer_key'],
        'consumer_secret': PESAPAL_CONFIG['consumer_secret']
    }
    
    # Send the POST request to the Pesapal API
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()['token']
    else:
        return None

@app.route('/authenticate', methods=['GET'])
def authenticate():
    token = get_access_token()
    if token:
        return jsonify({'status': 'success', 'token': token})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get access token'}), 400

if __name__ == '__main__':
    app.run(debug=True)