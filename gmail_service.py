import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def read_emails(service, max_results=5):
    results = service.users().messages().list(userId='me', maxResults=max_results, labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        full_msg = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = full_msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        # get body
        parts = full_msg['payload'].get('parts', [])
        body = ''
        if parts:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        else:
            data = full_msg['payload']['body'].get('data', '')
            body = base64.urlsafe_b64decode(data).decode('utf-8') if data else ''
        emails.append({'id': msg['id'], 'subject': subject, 'sender': sender, 'body': body})
    return emails

def send_email(service, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f"Email sent to {to}")