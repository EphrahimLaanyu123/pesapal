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

# Helper function to get the access token
def get_access_token():
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
@app.route('/products')
def get_products():
    # Fetch products from the database or a static list for testing
    products = [
        {"id": 1, "name": "Product 1", "description": "Description 1", "price": 1},
        {"id": 2, "name": "Product 2", "description": "Description 2", "price": 200},
        # Add more products if needed
    ]
    return jsonify(products)


@app.route('/authenticate', methods=['GET'])
def authenticate():
    token = get_access_token()
    if token:
        return jsonify({'status': 'success', 'token': token})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get access token'}), 400

# Register IPN URL function
def register_ipn_url():
    url = "https://pay.pesapal.com/v3/api/URLSetup/RegisterIPN"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"  # Replace with your access token
    }
    data = {
        "url": PESAPAL_CONFIG['ipn_url'],  # Replace with your actual IPN URL
        "ipn_notification_type": "POST"  # or "GET", depending on your setup
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        print("IPN URL registered successfully.")
        print(response.json())  # Print the response, which contains the IPN ID and status
    else:
        print(f"Error: {response.status_code}, {response.text}")

# Get registered IPNs
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

# Submit order
def submit_order(product_id, quantity):
    product = next((item for item in products if item['id'] == product_id), None)
    if not product:
        return jsonify({'status': 'error', 'message': 'Product not found'}), 404
    
    total_amount = product['price'] * quantity
    order_id = str(uuid.uuid4())
    
    order = {
        'order_id': order_id,
        'product_id': product_id,
        'quantity': quantity,
        'total_amount': total_amount,
        'status': 'pending',
        'created_at': datetime.now(),
    }
    
    orders[order_id] = order
    
    url = "https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest"  # Use production URL
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token()}"  # Use live access token
    }

    data = {
        "id": order_id,
        "currency": "KES",
        "amount": total_amount,
        "description": product['description'],
        "callback_url": PESAPAL_CONFIG['callback_url'],
        "notification_id": str(uuid.uuid4()),  # Unique notification ID
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
        return jsonify({
            'status': 'success',
            'order_tracking_id': response_data.get("order_tracking_id"),
            'merchant_reference': response_data.get("merchant_reference"),
            'redirect_url': response_data.get("redirect_url")
        })
    else:
        return jsonify({'status': 'error', 'message': 'Failed to create order'}), 400

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    
    if not product_id or not quantity:
        return jsonify({'status': 'error', 'message': 'Missing product ID or quantity'}), 400
    
    return submit_order(product_id, quantity)

# Callback endpoint (Payment response)
@app.route('/payment-callback', methods=['POST'])
def payment_callback():
    # Handle payment callback logic
    # This is where you can verify payment and update order status in your database
    data = request.json
    order_id = data.get('order_id')
    payment_status = data.get('payment_status')

    if order_id in orders:
        order = orders[order_id]
        order['status'] = 'completed' if payment_status == 'success' else 'failed'
        return jsonify({'status': 'success', 'order_status': order['status']})

    return jsonify({'status': 'error', 'message': 'Order not found'}), 404

# Register IPN URL when starting the application
# @app.before_first_request
# def register_ipn_on_start():
#     register_ipn_url()

if __name__ == '__main__':
    app.run(debug=True)
