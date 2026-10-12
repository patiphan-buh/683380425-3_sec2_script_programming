# email-sms-automator/src/sms_gateway.py
from .email_sender import EmailSender
from .utils import setup_logging

logger = setup_logging(__name__)


class SMSGateway:
    """
    Provides a simplified interface to send SMS via email-to-SMS gateways.
    Relies on EmailSender for the actual email transmission.
    """

    # Common US carrier email-to-SMS gateways (add more as needed)
    CARRIER_GATEWAYS = {
        "att": "@txt.att.net",
        "verizon": "@vtext.com",
        "tmobile": "@tmomail.net",
        "sprint": "@messaging.sprintpcs.com",
        "boost": "@sms.boostmobile.com",
        "cricket": "@mms.cricketwireless.net",
        "us_cellular": "@email.uscc.net",
    }

    def __init__(self, email_sender_instance):
        if not isinstance(email_sender_instance, EmailSender):
            raise TypeError("SMSGateway requires an instance of EmailSender.")
        self.email_sender = email_sender_instance
        self.carrier_gateways = dict(self.CARRIER_GATEWAYS)
        logger.info("SMSGateway initialized.")

    def build_gateway_address(self, phone_number, carrier_name=None):
        """Returns the gateway email address, or None if it cannot be determined."""
        phone_number = str(phone_number).strip()
        if '@' in phone_number and '.' in phone_number:
            return phone_number  # Already a full gateway address
        if carrier_name and carrier_name.lower() in self.carrier_gateways:
            digits = "".join(ch for ch in phone_number if ch.isdigit())
            return f"{digits}{self.carrier_gateways[carrier_name.lower()]}"
        return None

    def send_sms(self, phone_number, message, carrier_name=None):
        """
        Sends an SMS message via email-to-SMS gateway.
        :return: True if message sent (email-wise), False otherwise.
        """
        sms_gateway_address = self.build_gateway_address(phone_number, carrier_name)
        if not sms_gateway_address:
            logger.warning("No supported carrier provided and phone number is not a gateway address. "
                           "Cannot send SMS.")
            return False
        if len(message) > 160:
            logger.warning("SMS message longer than 160 chars; carrier may truncate or split it.")
        logger.info(f"Attempting to send SMS to {phone_number} via gateway: {sms_gateway_address}")
        return self.email_sender.send_email(sms_gateway_address, "", message)
