# email-sms-automator/src/email_sender.py
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .utils import setup_logging

logger = setup_logging(__name__)


class EmailSender:
    """
    Handles sending emails via SMTP.
    """

    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.server = None
        logger.info(f"EmailSender initialized for {sender_email} via {smtp_server}:{self.smtp_port}.")

    def _connect(self):
        """Establishes and logs into the SMTP server."""
        try:
            self.server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            self.server.starttls()  # Secure the connection
            self.server.login(self.sender_email, self.sender_password)
            logger.info("Successfully connected and logged into SMTP server.")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed. Check email and app password. Error: {e}")
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed. Check server address and port. Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during SMTP connect/login: {e}")
        self.server = None
        return False

    def _disconnect(self):
        """Disconnects from the SMTP server."""
        if self.server:
            try:
                self.server.quit()
                logger.info("Disconnected from SMTP server.")
            except Exception as e:
                logger.warning(f"Error during SMTP disconnection: {e}")
            finally:
                self.server = None

    def build_message(self, recipient_email, subject, body, attachment_path=None,
                      is_html=False, cc=None, bcc=None):
        """Builds a MIMEMultipart message (body + optional attachment)."""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc

        # Attach body (utf-8 so Thai text displays correctly)
        msg.attach(MIMEText(body, 'html' if is_html else 'plain', 'utf-8'))

        # Attach file if path is provided
        if attachment_path:
            try:
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)
                logger.info(f"Attached file: {attachment_path}")
            except FileNotFoundError:
                logger.error(f"Attachment file not found: {attachment_path}. Email will be sent without it.")
            except Exception as e:
                logger.error(f"Error attaching file {attachment_path}: {e}. Email will be sent without it.")
        return msg

    def send_email(self, recipient_email, subject, body, attachment_path=None,
                   is_html=False, cc=None, bcc=None):
        """
        Sends an email.
        :param recipient_email: The email address of the recipient.
        :param subject: The subject line of the email.
        :param body: The content of the email.
        :param attachment_path: Optional path to a file to attach.
        :param is_html: Set to True if the body is HTML, False for plain text.
        :return: True if email sent successfully, False otherwise.
        """
        if not self._connect():
            return False

        msg = self.build_message(recipient_email, subject, body, attachment_path, is_html, cc, bcc)

        try:
            self.server.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email} with subject: '{subject}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}. Error: {e}")
            return False
        finally:
            self._disconnect()
