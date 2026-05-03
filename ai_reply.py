from groq import Groq

client = Groq(api_key="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")

YOUR_NAME = "Daniyal"

RELATIVES = [
    "yousaf", "abdullah", "ibrahim", "father" , "mother" , "nadeem" , "badar"# add any relative names/emails here
]

BLOCKED_SENDERS = [
    "no-reply", "noreply", "newsletter", "pinterest", "recommendations"
]

def is_blocked(sender):
    sender_lower = sender.lower()
    return any(b in sender_lower for b in BLOCKED_SENDERS)


def is_relative(sender):
    sender_lower = sender.lower()
    return any(r in sender_lower for r in RELATIVES)


def generate_reply(sender, subject, body):
    tone = "casual and warm like talking to a family member" if is_relative(sender) else "professional and formal"

    prompt = f"""You are an email assistant writing on behalf of {YOUR_NAME}.
Write a {tone} reply to this email.
Sign off as {YOUR_NAME} — never write [Your Name].

From: {sender}
Subject: {subject}
Email body:
{body}

Write only the reply body."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content