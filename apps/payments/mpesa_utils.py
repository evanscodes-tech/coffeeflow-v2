import requests
import base64
from datetime import datetime
from django.conf import settings
import json

class MpesaClient:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.passkey = settings.MPESA_PASSKEY
        self.shortcode = settings.MPESA_SHORTCODE
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')
        
        if self.environment == 'sandbox':
            self.auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            self.b2c_url = "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
        else:
            self.auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            self.b2c_url = "https://api.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
    
    def get_access_token(self):
        """Get OAuth access token from Safaricom"""
        response = requests.get(
            self.auth_url,
            auth=(self.consumer_key, self.consumer_secret)
        )
        if response.status_code == 200:
            return response.json().get('access_token')
        return None
    
    def b2c_payment(self, phone_number, amount, command_id='BusinessPayment', 
                    remarks='CoffeeFlow Payment', occasion='Farmer Payment'):
        """
        Send money to a farmer via B2C
        command_id: 'BusinessPayment' or 'SalaryPayment' or 'PromotionPayment'
        """
        access_token = self.get_access_token()
        if not access_token:
            return {'error': 'Failed to get access token'}
        
        # Format phone number: 254XXXXXXXXX
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+254'):
            phone_number = phone_number[1:]
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        payload = {
            'InitiatorName': 'coffeeflow',
            'SecurityCredential': self.get_security_credential(),
            'CommandID': command_id,
            'Amount': str(amount),
            'PartyA': self.shortcode,
            'PartyB': phone_number,
            'Remarks': remarks,
            'QueueTimeOutURL': 'https://coffeeflow.com/queue-timeout',
            'ResultURL': 'https://coffeeflow.com/result',
            'Occasion': occasion
        }
        
        response = requests.post(self.b2c_url, headers=headers, json=payload)
        return response.json()
    
    def get_security_credential(self):
        """
        For sandbox, we can use a placeholder.
        In production, you need to encrypt the password.
        """
        # For sandbox testing, Safaricom accepts this placeholder
        if self.environment == 'sandbox':
            return 'sandbox_credential'
        # In production, implement proper encryption
        return self.passkey