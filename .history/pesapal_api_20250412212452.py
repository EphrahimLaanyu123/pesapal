from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Pesapal API credentials
CONSUMER_KEY = 'xxxxx'  # Replace with your actual consumer_key
CONSUMER_SECRET = ' S3AnVcFQ25XmEFRFLuV/Y/S5KG0='  # Replace with your actual consumer_secret

# URL for getting token (sandbox or production)
TOKEN_URL = 'https://cybqa.pesapal.com/pesapalv3/api/Auth/RequestToken'  # Change to production URL when ready

@app.route('/get_token', methods=['POST'])
def get_token():
    # Prepare request payload
    payload = {
        'consumer_key': CONSUMER_KEY,
        'consumer_secret': CONSUMER_SECRET
    }

    # Send POST request to Pesapal API
    response = requests.post(TOKEN_URL, json=payload)

    # Check if request was successful
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
