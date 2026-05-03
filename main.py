from gmail_service import get_service, read_emails, send_email
from ai_reply import generate_reply

GMAIL_ID = "daniyalnadeem911@gmail.com"  # change this to any Gmail you want

# Emails to NEVER auto-send to (always skip)
BLOCKED_SENDERS = [
    "no-reply", "noreply", "newsletter", "pinterest", "recommendations"
]

def is_blocked(sender):
    sender_lower = sender.lower()
    return any(b in sender_lower for b in BLOCKED_SENDERS)

def main():
    service = get_service()
    print("Reading emails...\n")
    emails = read_emails(service, max_results=5)

    for email in emails:
        print(f"From: {email['sender']}")
        print(f"Subject: {email['subject']}")
        print(f"Body preview: {email['body'][:100]}")
        print("-" * 40)

        if is_blocked(email['sender']):
            print("Skipping — blocked sender.\n")
            continue

        reply = generate_reply(email['sender'], email['subject'], email['body'])
        print(f"Generated reply:\n{reply}\n")

        confirm = input("Send this reply? (yes/no): ").strip().lower()
        if confirm == "yes":
            send_email(service, email['sender'], "Re: " + email['subject'], reply)
            print("Sent.\n")
        else:
            print("Skipped.\n")

if __name__ == "__main__":
    main()