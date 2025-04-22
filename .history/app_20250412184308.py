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
    'sandbox': False,
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
    

def register_ipn_url():
    url = "https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"
    }
    data = {
        "url": "http://yourserver.com/ipn",  # Replace with your actual IPN URL
        "ipn_notification_type": "POST"  # or "GET", depending on your setup
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        print("IPN URL registered successfully.")
        print(response.json())  # Print the response, which contains the IPN ID and status
    else:
        print(f"Error: {response.status_code}, {response.text}")

# Call the function to register IPN URL
register_ipn_url()

def get_registered_ipns():
    url = "https://pay.pesapal.com/v3/api/URLSetup/GetIpnList"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"  # Replace with your access token
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Registered IPNs fetched successfully.")
        print(response.json())  # This will print the list of registered IPNs
    else:
        print(f"Error: {response.status_code}, {response.text}")

# Call the function to fetch registered IPNs
get_registered_ipns()


def submit_order():
    url = "https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest"  # Use production URL
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"  # Replace with your actual token
    }

    data = {
        "id": "AA1122-3344ZZ",
        "currency": "KES",
        "amount": 100.00,
        "description": "Payment description goes here",
        "callback_url": "https://www.myapplication.com/response-page",
        "redirect_mode": "",
        "notification_id": "fe078e53-78da-4a83-aa89-e7ded5c456e6",
        "branch": "Store Name - HQ",
        "billing_address": {
            "email_address": "john.doe@example.com",
            "phone_number": "0723xxxxxx",
            "country_code": "KE",
            "first_name": "John",
            "middle_name": "",
            "last_name": "Doe",
            "line_1": "Pesapal Limited",
            "line_2": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "zip_code": ""
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        print("Order successfully created.")
        print("Order Tracking ID:", response_data.get("order_tracking_id"))
        print("Merchant Reference:", response_data.get("merchant_reference"))
        print("Redirect URL:", response_data.get("redirect_url"))
    else:
        print("Failed to create order:", response.status_code, response.text)

# Call the function to submit the order
submit_order()

if __name__ == '__main__':
    app.run(debug=True)