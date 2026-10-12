# agentic-comm-automator/src/sms_tasks.py
import re

from .email_tasks import EmailTasks
from .utils import setup_logging

logger = setup_logging(__name__)

SMS_MAX_LENGTH = 160


class SMSTasks:
    """
    Sends SMS via email-to-SMS gateways, reusing EmailTasks for the actual transmission.

    A phone number can be given as:
      * digits + carrier_name  -> "0812345678" + "att"  => 0812345678@txt.att.net
      * a full gateway address -> "0812345678@txt.att.net" (carrier_name ignored)
    Tip: carriers outside the US (e.g. in Thailand) generally have no email gateway – for testing,
    put an email address you can read in TEST_SMS_PHONE_NUMBER and the "SMS" arrives as an email.
    """

    def __init__(self, email_tasks_instance):
        if not isinstance(email_tasks_instance, EmailTasks):
            raise TypeError("SMSTasks requires an instance of EmailTasks.")
        self.email_tasks = email_tasks_instance
        self.carrier_gateways = {
            "att": "@txt.att.net",
            "verizon": "@vtext.com",
            "tmobile": "@tmomail.net",
            "sprint": "@messaging.sprintpcs.com",
            "boost": "@sms.myboostmobile.com",
            "cricket": "@sms.cricketwireless.net",
            "us_cellular": "@email.uscc.net",
            "googlefi": "@msg.fi.google.com",
        }
        logger.info("SMSTasks initialized.")

    def resolve_gateway(self, phone_number, carrier_name=None):
        phone_number = (phone_number or "").strip()
        if "@" in phone_number and "." in phone_number.split("@")[-1]:
            return phone_number
        digits = re.sub(r"\D", "", phone_number)
        carrier = (carrier_name or "").strip().lower()
        if digits and carrier in self.carrier_gateways:
            return f"{digits}{self.carrier_gateways[carrier]}"
        return None

    def send_sms(self, phone_numbers, message, carrier_name=None):
        """
        Sends the message to every number.
        :return: dict {"success": all sent, "sent": [...], "failed": [...]}.
        """
        if len(message) > SMS_MAX_LENGTH:
            logger.warning(f"SMS is {len(message)} chars; truncating to {SMS_MAX_LENGTH}.")
            message = message[:SMS_MAX_LENGTH - 3] + "..."
        sent, failed = [], []
        for number in phone_numbers:
            gateway = self.resolve_gateway(number, carrier_name)
            if not gateway:
                logger.warning(f"Cannot build SMS gateway address for '{number}' "
                               f"(carrier '{carrier_name}' unknown and number is not an email address).")
                failed.append(number)
                continue
            logger.info(f"Sending SMS to {number} via gateway {gateway}")
            result = self.email_tasks.send_email(recipients={"to": [gateway]}, subject="", body=message)
            (sent if result["success"] else failed).append(gateway)
        logger.info(f"SMS: {len(sent)} sent, {len(failed)} failed.")
        return {"success": bool(phone_numbers) and not failed, "sent": sent, "failed": failed,
                "message": message}
