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



if __name__ == '__main__':
    app.run(debug=True)