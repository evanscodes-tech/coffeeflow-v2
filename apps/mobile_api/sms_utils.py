import africastalking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service using Africa's Talking API"""
    
    def __init__(self):
        self.username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
        self.api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
        
        try:
            africastalking.initialize(self.username, self.api_key)
            self.sms = africastalking.SMS
            self.is_initialized = True
            print("✅ Africa's Talking initialized successfully")
        except Exception as e:
            self.is_initialized = False
            print(f"❌ Failed to initialize: {str(e)}")
    
    def send_otp(self, phone_number, otp_code):
        """Send OTP code via SMS"""
        if not self.is_initialized:
            return False, "SMS service not initialized"
        
        # Format phone number to international format (254XXXXXXXXX)
        formatted_number = self.format_phone_number(phone_number)
        
        message = f"Your CoffeeFlow OTP is: {otp_code}. Valid for 10 minutes."
        
        print(f"📞 Sending to: {formatted_number}")
        print(f"📝 Message: {message}")
        
        try:
            # Use the SDK properly
            response = self.sms.send(message, [formatted_number], sender_id="CoffeeFlow")
            print(f"📱 SMS Response: {response}")
            
            if response and response.get('SMSMessageData'):
                recipients = response['SMSMessageData']['Recipients']
                if recipients and len(recipients) > 0:
                    status = recipients[0].get('status')
                    if status == 'Success':
                        print(f"✅ OTP sent to {formatted_number}")
                        return True, "OTP sent successfully"
                    else:
                        print(f"⚠️ Status: {status}")
                        return False, f"SMS failed: {status}"
            
            return False, "No response from SMS service"
            
        except Exception as e:
            print(f"❌ SMS error: {str(e)}")
            return False, str(e)
    
    def format_phone_number(self, phone_number):
        """
        Format phone number for Africa's Talking
        Expected format: 254XXXXXXXXX (no leading + or 0)
        """
        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Remove leading 0 and replace with 254
        if cleaned.startswith('0'):
            cleaned = '254' + cleaned[1:]
        # Remove leading + if present
        elif cleaned.startswith('254254'):
            cleaned = cleaned[3:]
        
        print(f"📞 Formatted phone number: {cleaned}")
        return cleaned
    
    def test_connection(self):
        """Test if SMS service is working"""
        if not self.is_initialized:
            return False, "SMS service not initialized"
        
        try:
            # Try to fetch messages as a connection test
            response = self.sms.fetch_messages()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

# Singleton instance
sms_service = SMSService()