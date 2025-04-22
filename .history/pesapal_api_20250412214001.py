from flask import Flask, jsonify, request
import requests
from flask_cors import CORS  

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST", "OPTIONS"])

CONSUMER_KEY = 'Br9toGU3pWfpg21N3adIO2u95u2RTqXd' 
CONSUMER_SECRET = 'S3AnVcFQ25XmEFRFLuV/Y/S5KG0='
URL = ""

TOKEN_URL = 'https://pay.pesapal.com/v3/api/Auth/RequestToken'  

@app.route('/get_token', methods=['POST'])
def get_token():
    payload = {
        'consumer_key': CONSUMER_KEY,
        'consumer_secret': CONSUMER_SECRET
    }

    response = requests.post(TOKEN_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        return jsonify({
            'token': data.get('token'),
            'expiryDate': data.get('expiryDate'),
            'status': data.get('status'),
            'message': data.get('message')
        }), 200
    else:
        return jsonify({
            'error': 'Failed to get token',
            'status_code': response.status_code,
            'message': response.text
        }), 400

if __name__ == '__main__':
    app.run(debug=True)
