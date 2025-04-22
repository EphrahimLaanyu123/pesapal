from flask import Flask, request, jsonify
import requests
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS
import uuid
from datetime import datetime
from flask import jsonify, request
import requests


app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])
# Pesapal API configuration
PESAPAL_CONFIG = {
    'sandbox': True,
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

# Helper function to get Pesapal base URL
def get_pesapal_base_url():
    return "https://pay.pesapal.com/v3/api/Auth/RequestToken"  # Live environment URL


# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        # In a real app, you would verify the token here
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/initiate-payment', methods=['POST'])
@token_required
def initiate_payment():
    data = request.json
    product_id = data.get('product_id')
    customer_email = data.get('email')
    phone_number = data.get('phone_number')
    
    # Find product
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Authenticate with Pesapal to get token
    auth_url = f"{get_pesapal_base_url()}/api/Auth/RequestToken"
    auth_data = {
        "consumer_key": PESAPAL_CONFIG['consumer_key'],
        "consumer_secret": PESAPAL_CONFIG['consumer_secret']
    }
    
    try:
        auth_response = requests.post(auth_url, json=auth_data, headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        auth_response.raise_for_status()
        token_data = auth_response.json()
        access_token = token_data['token']
    except Exception as e:
        return jsonify({'error': 'Failed to authenticate with Pesapal', 'details': str(e)}), 500
    
    # Register IPN (in a real app, you'd do this once and store the IPN ID)
    ipn_url = f"{get_pesapal_base_url()}/api/URLSetup/RegisterIPN"
    ipn_data = {
        "url": PESAPAL_CONFIG['ipn_url'],
        "ipn_notification_type": "POST"
    }
    
    try:
        ipn_response = requests.post(ipn_url, json=ipn_data, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        })
        ipn_response.raise_for_status()
        ipn_data = ipn_response.json()
        notification_id = ipn_data['ipn_id']
    except Exception as e:
        return jsonify({'error': 'Failed to register IPN', 'details': str(e)}), 500
    
    # Submit order to Pesapal
    order_id = str(uuid.uuid4())
    submit_order_url = f"{get_pesapal_base_url()}/api/Transactions/SubmitOrderRequest"
    order_data = {
        "id": order_id,
        "currency": "KES",
        "amount": product['price'],
        "description": f"Payment for {product['name']}",
        "callback_url": PESAPAL_CONFIG['callback_url'],
        "notification_id": notification_id,
        "billing_address": {
            "email_address": customer_email,
            "phone_number": phone_number,
            "country_code": "KE",
            "first_name": "Customer",
            "last_name": "Name"
        }
    }
    
    try:
        order_response = requests.post(submit_order_url, json=order_data, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        })
        order_response.raise_for_status()
        order_response_data = order_response.json()
        
        # Store order in our database
        orders[order_id] = {
            "pesapal_tracking_id": order_response_data['order_tracking_id'],
            "product_id": product_id,
            "amount": product['price'],
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "redirect_url": order_response_data['redirect_url'],
            "order_id": order_id
        })
    except Exception as e:
        return jsonify({'error': 'Failed to submit order to Pesapal', 'details': str(e)}), 500

@app.route('/api/payment-status', methods=['GET'])
@token_required
def check_payment_status():
    order_id = request.args.get('order_id')
    if order_id not in orders:
        return jsonify({'error': 'Order not found'}), 404
    
    # Get Pesapal token
    auth_url = f"{get_pesapal_base_url()}/api/Auth/RequestToken"
    auth_data = {
        "consumer_key": PESAPAL_CONFIG['consumer_key'],
        "consumer_secret": PESAPAL_CONFIG['consumer_secret']
    }
    
    try:
        auth_response = requests.post(auth_url, json=auth_data, headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        auth_response.raise_for_status()
        token_data = auth_response.json()
        access_token = token_data['token']
    except Exception as e:
        return jsonify({'error': 'Failed to authenticate with Pesapal', 'details': str(e)}), 500
    
    # Check transaction status
    status_url = f"{get_pesapal_base_url()}/api/Transactions/GetTransactionStatus?orderTrackingId={orders[order_id]['pesapal_tracking_id']}"
    
    try:
        status_response = requests.get(status_url, headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        })
        status_response.raise_for_status()
        status_data = status_response.json()
        
        # Update order status in our database
        orders[order_id]['status'] = status_data['payment_status_description'].lower()
        orders[order_id]['updated_at'] = datetime.now().isoformat()
        
        return jsonify({
            "status": orders[order_id]['status'],
            "payment_details": status_data
        })
    except Exception as e:
        return jsonify({'error': 'Failed to check payment status', 'details': str(e)}), 500

@app.route('/api/ipn', methods=['POST'])
def ipn_handler():
    data = request.json
    order_tracking_id = data.get('OrderTrackingId')
    order_merchant_reference = data.get('OrderMerchantReference')
    
    # In a real app, you would process the IPN and update your database
    print(f"Received IPN for order {order_merchant_reference} with tracking ID {order_tracking_id}")
    
    # Return success response to Pesapal
    return jsonify({
        "orderNotificationType": "IPNCHANGE",
        "orderTrackingId": order_tracking_id,
        "orderMerchantReference": order_merchant_reference,
        "status": 200
    })

if __name__ == '__main__':
    app.run(debug=True)