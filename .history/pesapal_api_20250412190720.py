from flask import Flask, request, jsonify
import requests
import os
import uuid

app = Flask(__name__)

# Live Pesapal API Base
BASE_URL = "https://pay.pesapal.com/v3"

# Replace with your actual live keys
CONSUMER_KEY = "your_live_consumer_key"
CONSUMER_SECRET = "S3AnVcFQ25XmEFRFLuV/Y/S5KG0=

# Cache token to avoid re-auth on each call
access_token = None


def get_token():
    global access_token
    if access_token:
        return access_token
    url = f"{BASE_URL}/api/Auth/RequestToken"
    payload = {
        "consumer_key": CONSUMER_KEY,
        "consumer_secret": CONSUMER_SECRET
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    res = requests.post(url, json=payload, headers=headers)
    data = res.json()
    access_token = data['token']
    return access_token


@app.route("/register-ipn", methods=["POST"])
def register_ipn():
    token = get_token()
    url = f"{BASE_URL}/api/URLSetup/RegisterIPN"
    payload = {
        "url": request.json.get("url"),
        "ipn_notification_type": "POST"
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    res = requests.post(url, json=payload, headers=headers)
    return jsonify(res.json())


@app.route("/submit-order", methods=["POST"])
def submit_order():
    token = get_token()
    url = f"{BASE_URL}/api/Transactions/SubmitOrderRequest"

    order_id = str(uuid.uuid4())[:20]  # or use your own unique ID
    payload = {
        "id": order_id,
        "currency": request.json.get("currency"),
        "amount": request.json.get("amount"),
        "description": request.json.get("description"),
        "callback_url": request.json.get("callback_url"),
        "notification_id": request.json.get("notification_id"),
        "billing_address": request.json.get("billing_address")
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers)
    return jsonify(res.json())


@app.route("/ipn", methods=["POST", "GET"])
def ipn_listener():
    data = request.json if request.method == "POST" else request.args
    print("IPN received:", data)
    return jsonify({
        "orderNotificationType": data.get("OrderNotificationType"),
        "orderTrackingId": data.get("OrderTrackingId"),
        "orderMerchantReference": data.get("OrderMerchantReference"),
        "status": 200
    })


@app.route("/callback", methods=["GET"])
def callback_handler():
    data = request.args
    return jsonify({
        "OrderTrackingId": data.get("OrderTrackingId"),
        "OrderNotificationType": data.get("OrderNotificationType"),
        "OrderMerchantReference": data.get("OrderMerchantReference")
    })


@app.route("/transaction-status", methods=["GET"])
def transaction_status():
    token = get_token()
    tracking_id = request.args.get("orderTrackingId")
    url = f"{BASE_URL}/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    res = requests.get(url, headers=headers)
    return jsonify(res.json())


if __name__ == "__main__":
    app.run(debug=True)
