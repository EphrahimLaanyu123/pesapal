from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Base URLs
SANDBOX_URL = "https://cybqa.pesapal.com/pesapalv3/api"
LIVE_URL = "https://pay.pesapal.com/v3/api"
BASE_URL = LIVE_URL  # Switch to SANDBOX_URL for testing

# Utility function to make requests with authentication
def make_pesapal_request(endpoint, data=None, method="POST", headers=None):
    """
    Makes a request to the Pesapal API, handling authentication.
    """
    # Get token
    token_response = requests.post(f"{BASE_URL}/Auth/RequestToken", json={
        "consumer_key": "<YOUR_CONSUMER_KEY>",  # Replace with your actual consumer key
        "consumer_secret": "<YOUR_CONSUMER_SECRET>" # Replace with your actual consumer secret
    })
    token_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    token = token_response.json()["token"]

    headers = headers or {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Accept"] = "application/json"
    headers["Content-Type"] = "application/json"

    if method == "POST":
        response = requests.post(f"{BASE_URL}/{endpoint}", json=data, headers=headers)
    elif method == "GET":
        response = requests.get(f"{BASE_URL}/{endpoint}", params=data, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    response.raise_for_status()
    return response.json()

# 1. Authentication Endpoint [cite: 218, 219, 220, 221, 222]
@app.route('/auth/token', methods=['POST'])
def get_auth_token():
    """
    Fetches an authentication token from Pesapal.
    """
    data = request.get_json()
    try:
        token_response = requests.post(f"{BASE_URL}/Auth/RequestToken", json=data)
        token_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return jsonify(token_response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 2. IPN URL Registration Endpoint [cite: 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243]
@app.route('/ipn/register', methods=['POST'])
def register_ipn():
    """
    Registers an IPN URL with Pesapal.
    """
    data = request.get_json()
    try:
        ipn_response = make_pesapal_request("URLSetup/RegisterIPN", data)
        return jsonify(ipn_response)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 3. Get Registered IPNs Endpoint [cite: 256, 257]
@app.route('/ipn/list', methods=['GET'])
def get_ipn_list():
    """
    Fetches all registered IPN URLs for a merchant account.
    """
    try:
        ipn_list_response = make_pesapal_request("URLSetup/GetlpnList", method="GET")
        return jsonify(ipn_list_response)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 4. Submit Order Request Endpoint [cite: 261, 262, 263, 264, 265, 266]
@app.route('/order/submit', methods=['POST'])
def submit_order():
    """
    Submits an order request to Pesapal.
    """
    data = request.get_json()
    try:
        order_response = make_pesapal_request("Transactions/SubmitOrderRequest", data)
        return jsonify(order_response)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 5. Get Transaction Status Endpoint [cite: 304, 305]
@app.route('/order/status', methods=['GET'])
def get_order_status():
    """
    Fetches the status of a transaction.
    """
    order_tracking_id = request.args.get('orderTrackingId')
    if not order_tracking_id:
        return jsonify({"error": "orderTrackingId is required"}), 400
    
    try:
        status_response = make_pesapal_request(
            f"Transactions/GetTransactionStatus?orderTrackingId={order_tracking_id}", 
            method="GET"
        )
        return jsonify(status_response)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 6. Refund Request Endpoint [cite: 387, 388, 389, 390, 391, 392, 393, 394, 395]
@app.route('/order/refund', methods=['POST'])
def refund_order():
    """
    Requests a refund for a transaction.
    """
    data = request.get_json()
    try:
        refund_response = make_pesapal_request("Transactions/RefundRequest", data)
        return jsonify(refund_response)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 7. Order Cancellation API [cite: 409, 410, 411, 412, 413]
@app.route('/order/cancel', methods=['POST'])
def cancel_order():
    """
    Cancels a pending order.
    """
    data = request.get_json()
    try:
        cancel_response = make_pesapal_request("Transactions/CancelOrder", data)
        return jsonify(cancel_response)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)