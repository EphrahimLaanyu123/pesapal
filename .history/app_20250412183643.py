import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Pesapal API credentials
PESAPAL_CONFIG = {
    'sandbox': True,
    'consumer_key': 'your_consumer_key',
    'consumer_secret': 'your_consumer_secret'
}

def get_access_token():
    url = 'https://cybqa.pesapal.com/pesapalv3/api/Auth/RequestToken' if PESAPAL_CONFIG['sandbox'] else 'https://pay.pesapal.com/v3/api/Auth/RequestToken'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = {
        'consumer_key': PESAPAL_CONFIG['consumer_key'],
        'consumer_secret': PESAPAL_CONFIG['consumer_secret']
    }
    
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
