#!/usr/bin/env python3
"""
Email Sender Script
------------------
This script automates sending follow-up emails for job applications.
It reads application data from a JSON file and sends personalized emails
using SMTP over SSL.

Features:
- Rate limiting to avoid spam detection
- SSL encryption for secure email transmission
- Dry run mode for testing
- Detailed logging of all operations
- Error handling and reporting
- Input validation and normalization
"""

# Standard library imports
import json
import os
import ssl
import time
import logging
from typing import List, Dict, Any, Iterable
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
import smtplib
import socket
import traceback

# Third-party imports
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows configuration without changing code
load_dotenv()

# =========================
# SMTP Configuration
# =========================
# Email server settings from environment variables
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT_SSL = int(os.getenv("SMTP_PORT_SSL"))

# Rate limiting: pause between emails to avoid triggering spam filters
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS"))

# Enable SMTP debug output for troubleshooting
SMTP_DEBUG = os.getenv("SMTP_DEBUG")

# When True, simulates sending without actually sending emails
# Useful for testing email content and configuration
DRY_RUN = False

# Sender's display name in email signature
Sender_Name = os.getenv("SENDER_NAME")
# Optional profile links for email signature
Linkedin_Profile_URL = f"\nLinkedIn: {os.getenv('LINKEDIN_PROFILE_URL')}" if os.getenv(
    "LINKEDIN_PROFILE_URL") else ""
Portfolio_URL = f"\nPortfolio: {os.getenv('PORTFOLIO_URL')}" if os.getenv(
    "PORTFOLIO_URL") else ""
Github_Profile_URL = f"\nGitHub: {os.getenv('GITHUB_PROFILE_URL')}" if os.getenv(
    "GITHUB_PROFILE_URL") else ""

# =========================
# Logging Configuration
# =========================
# Set up detailed logging with timestamps and log levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("yahoo-sender")


def load_applications() -> List[Dict[str, Any]]:
    """
    Loads application data from applications.json file.
    
    File Structure Expected:
    {
        "applications": [
            {
                "company": "Company Name",
                "role": "Job Title",
                "emails": ["email1@company.com", "email2@company.com"]
            },
            ...
        ]
    }
    
    Returns:
        List[Dict[str, Any]]: List of application dictionaries
    """
    json_path = os.path.join(os.path.dirname(
        __file__), "metadata", "applications.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    return data["applications"]

def build_subject(role: str) -> str:
    """
    Generates email subject line based on the job role.
    
    Args:
        role (str): The job role/title being followed up on
        
    Returns:
        str: Formatted subject line for the email
    """
    return f"Follow-up on my application for {role}"

def build_body(company: str, role: str) -> str:
    """
    Generates personalized email body with:
    - Greeting
    - Follow-up message
    - Request for feedback
    - Signature
    """
    return (
        f"Hi {company} hiring team,\n\n"
        f"I hope you're doing well. I just wanted to kindly check in again regarding the {role} position. "
        f"I'm still enthusiastic and interested in the role at {company} and would love to know if there are any updates on the next steps.\n"
        f"\n"
        f"If I'm not selected for this role, I would love to get some feedback so that it would help me to better position myself in future applications.\n"
        f"Thank you for your time and consideration, and I look forward to hearing from you.\n"
        f"\n"
        f"Cheers,\n"
        f"{Sender_Name}\n"
        f"\n"
        f"{Linkedin_Profile_URL}"
        f"{Portfolio_URL}"
        f"{Github_Profile_URL}"
    )

def create_message(sender: str, recipient: str, company: str, role: str) -> EmailMessage:
    """
    Creates an EmailMessage object with all necessary headers and content.
    
    Args:
        sender (str): Sender's email address
        recipient (str): Recipient's email address
        company (str): Company name for personalization
        role (str): Job role for subject and body
        
    Returns:
        EmailMessage: Fully formatted email message ready to send
        
    Note:
        - Includes automatic Message-ID generation
        - Uses local timezone for Date header
        - Body text is generated from build_body()
    """
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["Subject"] = build_subject(role)
    msg.set_content(build_body(company, role))
    return msg

# -------- Input Validation Helpers --------
def _is_email_like(s: str) -> bool:
    """Basic validation to check if a string looks like an email address"""
    s = s.strip()
    return "@" in s and "." in s and " " not in s

def _coerce_emails(value: Any) -> List[str]:
    """
    Converts various input formats into a clean list of email addresses.
    Handles:
    - Lists/tuples/sets of strings
    - Comma/semicolon separated strings
    Removes duplicates and invalid emails.
    """
    emails: List[str] = []
    if value is None:
        return emails
    if isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, str) and _is_email_like(item):
                emails.append(item.strip())
    elif isinstance(value, str):
        parts = [p.strip() for p in value.replace(";", ",").split(",")]
        emails.extend([p for p in parts if _is_email_like(p)])
    return sorted(set(emails))

def normalize_applications(apps: Iterable[Any]) -> List[Dict[str, Any]]:
    """
    Cleans and validates application data:
    - Flattens nested structures
    - Validates required fields
    - Normalizes email addresses
    - Removes invalid entries
    """
    flat: List[Any] = []
    for item in apps:
        if isinstance(item, (list, tuple)):
            flat.extend(item)
        else:
            flat.append(item)

    cleaned: List[Dict[str, Any]] = []
    for idx, item in enumerate(flat):
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict application at index {idx}: {item!r}")
            continue

        company = str(item.get("company", "")).strip()
        role = str(item.get("role", "")).strip()
        emails = _coerce_emails(item.get("emails"))

        if not company or not role or not emails:
            logger.warning(
                f"Skipping row due to missing fields -> company='{company}', role='{role}', emails={emails}"
            )
            continue

        cleaned.append({"company": company, "role": role, "emails": emails})
    return cleaned

def send_all(applications_in: Iterable[Any], sender: str, password: str) -> None:
    """
    Main function to send emails to all recipients.
    
    Process:
    1. Normalizes and validates input data
    2. Establishes secure SMTP connection
    3. Sends emails with rate limiting
    4. Tracks successes and failures
    5. Provides detailed summary
    
    Args:
        applications_in (Iterable[Any]): Raw application data
        sender (str): Sender's email address
        password (str): SMTP authentication password
        
    Error Handling:
    - SMTP connection failures
    - Authentication errors
    - Per-recipient delivery failures
    - Network timeouts
    """
    apps = normalize_applications(applications_in)

    total_targets = sum(len(app["emails"]) for app in apps)
    success = 0
    failures: List[Dict[str, Any]] = []

    if DRY_RUN:
        logger.warning("DRY_RUN is ON — no emails will actually be sent.")

    context = ssl.create_default_context()
    server = None
    try:
        if not DRY_RUN:
            logger.info(f"Connecting to {SMTP_HOST}:{SMTP_PORT_SSL} over SSL …")
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL, context=context, timeout=30)
            if SMTP_DEBUG:
                server.set_debuglevel(1)  # Raw SMTP conversation to stdout
            logger.info("Connected. Logging in …")
            server.login(sender, password)
            logger.info("Login OK.")

        for app in apps:
            company = app["company"]
            role = app["role"]
            recipients = app["emails"]

            logger.info(f"=== Processing {company} | Role: {role} | {len(recipients)} recipient(s) ===")

            for to_addr in recipients:
                try:
                    msg = create_message(sender, to_addr, company, role)

                    logger.info(f"Prepared message -> To: {to_addr} | Subject: {msg['Subject']}")
                    logger.info(f"Message-ID: {msg['Message-ID']} | Date: {msg['Date']}")
                    logger.info(f"Body preview:\n{msg.get_content()!r}")

                    if DRY_RUN:
                        logger.info(f"[DRY_RUN] Skipping actual send to {to_addr}")
                    else:
                        response = server.send_message(msg)
                        # send_message returns a dict of failures; empty dict means success.
                        if not response:
                            logger.info(f"SENT ✅ -> {to_addr}")
                            success += 1
                        else:
                            logger.error(f"FAILED (per-recipient error dict) -> {to_addr} | {response}")
                            failures.append({"recipient": to_addr, "error": str(response)})

                    time.sleep(RATE_LIMIT_SECONDS)

                except (smtplib.SMTPException, socket.timeout) as e:
                    logger.error(f"SMTP error sending to {to_addr}: {e}")
                    logger.debug("Traceback:\n" + traceback.format_exc())
                    failures.append({"recipient": to_addr, "error": repr(e)})

                except Exception as e:
                    logger.error(f"Unexpected error sending to {to_addr}: {e}")
                    logger.debug("Traceback:\n" + traceback.format_exc())
                    failures.append({"recipient": to_addr, "error": repr(e)})

        # Summary
        logger.info("=== SEND SUMMARY ===")
        logger.info(f"Total intended recipients: {total_targets}")
        logger.info(f"Successful sends:         {success}")
        logger.info(f"Failures:                 {len(failures)}")
        if failures:
            for f in failures:
                logger.info(f" - {f['recipient']}: {f['error']}")

    finally:
        if server is not None:
            try:
                logger.info("Closing SMTP connection …")
                server.quit()
                logger.info("SMTP connection closed.")
            except Exception:
                logger.warning("Error while closing SMTP connection (ignored).")

if __name__ == "__main__":
    """
    Script entry point:
    1. Verifies environment variables
    2. Loads application data
    3. Initiates email sending process
    
    Required Environment Variables:
    - EMAIL: Sender's email address
    - APP_PASSWORD: Application-specific password for SMTP auth
    - SMTP_HOST: Email server hostname
    - SMTP_PORT_SSL: SSL port number
    - RATE_LIMIT_SECONDS: Delay between sends
    - SENDER_NAME: Name to use in signature
    """
    # Load credentials from environment variables
    sender_email = os.getenv("EMAIL")
    app_password = os.getenv("APP_PASSWORD")

    # Verify credentials are available
    if not sender_email or not app_password:
        logger.error("Missing EMAIL or APP_PASSWORD environment variables.")
        logger.error(
            "Example:\n  export EMAIL='you@yahoo.com'\n  export APP_PASSWORD='xxxx-xxxx-xxxx-xxxx'")
        raise SystemExit(1)

    # Load applications data from JSON file
    applications = load_applications()

    # Start sending process
    send_all(applications, sender_email, app_password)
