# email-sms-automator/src/email_receiver.py
import email
import imaplib
import os
from email.header import decode_header

from .utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)


class EmailReceiver:
    """
    Handles receiving and parsing emails via IMAP.
    Uses real IMAP UIDs (mail.uid(...)) so IDs stay valid across connections.
    """

    def __init__(self, imap_server, sender_email, sender_password):
        self.imap_server = imap_server
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.mail = None
        logger.info(f"EmailReceiver initialized for {sender_email} via {imap_server}.")

    def _connect(self):
        """Establishes and logs into the IMAP server."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.sender_email, self.sender_password)
            logger.info("Successfully connected and logged into IMAP server.")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed. Check email and app password. Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during IMAP connect/login: {e}")
        self.mail = None
        return False

    def _disconnect(self):
        """Disconnects from the IMAP server."""
        if self.mail:
            try:
                self.mail.logout()
                logger.info("Disconnected from IMAP server.")
            except Exception as e:
                logger.warning(f"Error during IMAP disconnection: {e}")
            finally:
                self.mail = None

    @staticmethod
    def build_search_query(criteria='UNSEEN', from_sender=None, subject_contains=None):
        """Builds IMAP search arguments. Values are quoted so spaces work."""
        query = [criteria]
        if from_sender:
            query += ['FROM', f'"{from_sender}"']
        if subject_contains:
            query += ['SUBJECT', f'"{subject_contains}"']
        return query

    def search_emails(self, mailbox='INBOX', criteria='UNSEEN', from_sender=None,
                      subject_contains=None):
        """
        Searches for emails based on criteria.
        Note: keep subject_contains ASCII-only (plain IMAP SEARCH is ASCII).
        :return: A list of email UIDs (bytes).
        """
        if not self._connect():
            return []
        try:
            self.mail.select(mailbox)
            search_query = self.build_search_query(criteria, from_sender, subject_contains)
            status, email_ids = self.mail.uid('SEARCH', None, *search_query)
            if status != 'OK':
                logger.error(f"IMAP search failed. Status: {status}")
                return []
            uids = email_ids[0].split()
            logger.info(f"Found {len(uids)} emails matching criteria in '{mailbox}'.")
            return uids
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
        finally:
            self._disconnect()

    def fetch_email_content(self, uid, mark_as_read=True, download_attachments_dir=None,
                            mailbox='INBOX'):
        """
        Fetches the content of a specific email by UID.
        Optionally marks as read and downloads attachments.
        :return: dict with uid, sender, subject, body_snippet, attachments_downloaded — or None.
        """
        if not self._connect():
            return None
        try:
            self.mail.select(mailbox)
            # BODY.PEEK[] fetches the full message without auto-marking it as read
            status, msg_data = self.mail.uid('FETCH', uid, '(BODY.PEEK[])')
            if status != 'OK' or not msg_data or msg_data[0] is None:
                logger.error(f"Failed to fetch email UID {uid}. Status: {status}")
                return None

            msg = email.message_from_bytes(msg_data[0][1])
            details = self.parse_message(msg, download_attachments_dir)

            if mark_as_read:
                self.mail.uid('STORE', uid, '+FLAGS', '(\\Seen)')
                logger.info(f"Marked email UID {self._uid_str(uid)} as read.")

            details["uid"] = self._uid_str(uid)
            return details
        except Exception as e:
            logger.error(f"Error fetching/parsing email UID {uid}: {e}")
            return None
        finally:
            self._disconnect()

    def parse_message(self, msg, download_attachments_dir=None):
        """Extracts sender, subject, plain-text body and attachments from an email.message.Message."""
        sender = self._decode_header_part(msg['From'])
        subject = self._decode_header_part(msg['Subject'])
        email_body = ""
        attachments_downloaded = []

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")

            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = os.path.basename(self._decode_header_part(filename))  # avoid path traversal
                if filename and download_attachments_dir:
                    ensure_directory_exists(download_attachments_dir)
                    filepath = os.path.join(download_attachments_dir, filename)
                    try:
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        attachments_downloaded.append(filepath)
                        logger.info(f"Downloaded attachment: {filepath}")
                    except Exception as e:
                        logger.error(f"Error downloading attachment {filename}: {e}")
            elif content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True) or b""
                    email_body += payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                except Exception as e:
                    logger.warning(f"Could not decode plain text part. Error: {e}")
                    email_body += "[ undecodable plain text part ]"
            # text/html parts are skipped for simplicity (plain text preferred)

        email_body = email_body.strip()
        snippet = email_body[:200] + "..." if len(email_body) > 200 else email_body
        return {
            "sender": sender,
            "subject": subject,
            "body_snippet": snippet,
            "attachments_downloaded": attachments_downloaded,
        }

    @staticmethod
    def _uid_str(uid):
        return uid.decode('utf-8') if isinstance(uid, bytes) else str(uid)

    @staticmethod
    def _decode_header_part(header_value):
        """Decodes header parts that might be encoded (e.g., '=?UTF-8?B?U3ViamVjdA==?=')."""
        if header_value is None:
            return ""
        decoded_string = ""
        for part, charset in decode_header(str(header_value)):
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(charset if charset else 'utf-8')
                except (LookupError, UnicodeDecodeError):
                    decoded_string += part.decode('latin-1', errors='replace')
            else:
                decoded_string += part
        return decoded_string.strip()
