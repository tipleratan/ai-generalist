import os
import base64
import pickle
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying scopes, delete the token.pickle file first
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """Authenticate with Gmail API using OAuth2 and return service object."""
    creds = None
    # Load saved credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid creds → authenticate again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # refresh token automatically
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save the credentials for future runs
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def create_message(sender, to, subject, message_text):
    """Create email message in base64 encoded format."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw_message.decode()}

def send_email(sender, to, subject, body):
    """Send email using Gmail API."""
    service = get_gmail_service()
    message = create_message(sender, to, subject, body)
    sent = service.users().messages().send(userId="me", body=message).execute()
    print(f"✅ Email sent! Message Id: {sent['id']}")

def build_hr_template(profile_data: dict) -> str:
    """
    Build HR-style email body with plain-text table structure from parsed_profile.json.
    No HTML tags, only formatted text.
    """
    name = profile_data[0].get("name", "N/A")
    contact = profile_data[0].get("contact_number", "N/A")
    email = profile_data[0].get("email_id", "N/A")
    exp = profile_data[0].get("year_of_experience", "N/A")
    company = profile_data[0].get("current_company_name", "N/A")
    skills = ", ".join(profile_data[0].get("primary_skills", []))

    # Define table content (list of rows)
    rows = [
        ("Name", name),
        ("Contact Number", contact),
        ("Email Id", email),
        ("Year of Exp", exp),
        ("Current Company Name", company),
        ("Primary Skills", skills),
    ]

    # Calculate column width for nice alignment
    col_width = max(len(row[0]) for row in rows) + 2

    # Build table string
    table_lines = []
    table_lines.append("=" * (col_width + 40))  # table border
    for heading, value in rows:
        table_lines.append(f"{heading:<{col_width}} | {value}")
    table_lines.append("=" * (col_width + 40))

    # Final email body
    text_body = (
        "Dear HR Team,\n\n"
        "Please find below candidate profile details for your review:\n\n"
        + "\n".join(table_lines) +
        "\n\nKindly proceed with the next steps in the recruitment process.\n\n"
        "Regards,\nRecruitment Bot"
    )

    return text_body


if __name__ == "__main__":
    # Load candidate profile (real-world example: parsed from resume)
    with open("parsed_profiles.json", "r", encoding="utf-8") as f:
        profile = json.load(f)

    # Build HR template
    body = build_hr_template(profile)

    # Send email
    send_email(
        sender="test@gmail.com",
        to="test@gmail.com",
        subject=f"Candidate Profile: {profile[0].get('name', 'Unknown')}",
        body=body
    )
