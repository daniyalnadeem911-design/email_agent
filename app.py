from flask import Flask, render_template_string, request, jsonify
from gmail_service import get_service, read_emails, send_email
from ai_reply import generate_reply, is_blocked

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Email Agent</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 40px auto; padding: 20px; background: #111; color: #eee; }
        .email-card { border: 1px solid #333; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .reply-box { width: 100%; height: 150px; background: #222; color: #eee; padding: 10px; border: 1px solid #444; }
        button { background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 4px; margin: 5px; }
        button.skip { background: #666; }
        h1 { color: #4CAF50; }
    </style>
</head>
<body>
    <h1>Email Agent</h1>
    <button onclick="loadEmails()">Read Emails</button>
    <div id="emails"></div>
    <script>
        async function loadEmails() {
            document.getElementById('emails').innerHTML = '<p>Loading...</p>';
            const res = await fetch('/emails');
            const data = await res.json();
            let html = '';
            data.forEach((email, i) => {
                html += `<div class="email-card">
                    <b>From:</b> ${email.sender}<br>
                    <b>Subject:</b> ${email.subject}<br>
                    <b>Preview:</b> ${email.body.substring(0, 150)}...<br><br>
                    <b>Generated Reply:</b><br>
                    <textarea class="reply-box" id="reply_${i}">${email.reply}</textarea><br>
                    <button onclick="sendEmail(${i}, '${email.sender}', '${email.subject}')">Send</button>
                    <button class="skip" onclick="this.parentElement.remove()">Skip</button>
                </div>`;
            });
            document.getElementById('emails').innerHTML = html || '<p>No emails found.</p>';
            window.emailData = data;
        }

        async function sendEmail(i, sender, subject) {
            const reply = document.getElementById('reply_' + i).value;
            const res = await fetch('/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({sender, subject, reply})
            });
            const data = await res.json();
            alert(data.message);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/emails')
def get_emails():
    service = get_service()
    emails = read_emails(service, max_results=5)
    result = []
    for email in emails:
        if is_blocked(email['sender']):
            continue
        reply = generate_reply(email['sender'], email['subject'], email['body'])
        result.append({
            'sender': email['sender'],
            'subject': email['subject'],
            'body': email['body'],
            'reply': reply
        })
    return jsonify(result)

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    service = get_service()
    send_email(service, data['sender'], "Re: " + data['subject'], data['reply'])
    return jsonify({'message': 'Email sent successfully!'})

if __name__ == '__main__':
    app.run(debug=True)