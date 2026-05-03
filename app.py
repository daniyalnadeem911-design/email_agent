from flask import Flask, render_template_string, request, jsonify
from gmail_service import get_service, read_emails, send_email
from ai_reply import generate_reply, is_blocked
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MailMind — AI Email Agent</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg: #080b12;
            --surface: #0d1117;
            --card: #111722;
            --border: rgba(255,255,255,0.06);
            --accent: #00e5c4;
            --accent2: #7b5ea7;
            --accent3: #e85d4a;
            --text: #e8eaf0;
            --muted: #5a6278;
            --glow: rgba(0,229,196,0.15);
        }

        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'DM Sans', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Animated background */
        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: 
                radial-gradient(ellipse 600px 400px at 20% 20%, rgba(0,229,196,0.04) 0%, transparent 70%),
                radial-gradient(ellipse 500px 500px at 80% 80%, rgba(123,94,167,0.05) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }

        /* Grid texture */
        body::after {
            content: '';
            position: fixed;
            inset: 0;
            background-image: 
                linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
        }

        .app { position: relative; z-index: 1; }

        /* NAV */
        nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 40px;
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(20px);
            background: rgba(8,11,18,0.8);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo {
            font-family: 'Syne', sans-serif;
            font-weight: 800;
            font-size: 22px;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-dot {
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            box-shadow: 0 0 12px var(--accent);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }

        .nav-badge {
            background: rgba(0,229,196,0.1);
            border: 1px solid rgba(0,229,196,0.2);
            color: var(--accent);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }

        /* HERO */
        .hero {
            text-align: center;
            padding: 80px 40px 60px;
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(0,229,196,0.08);
            border: 1px solid rgba(0,229,196,0.15);
            color: var(--accent);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 28px;
        }

        .hero h1 {
            font-family: 'Syne', sans-serif;
            font-size: clamp(42px, 6vw, 72px);
            font-weight: 800;
            line-height: 1.05;
            letter-spacing: -2px;
            margin-bottom: 20px;
        }

        .hero h1 span {
            background: linear-gradient(135deg, var(--accent), #00b8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero p {
            color: var(--muted);
            font-size: 17px;
            font-weight: 300;
            max-width: 480px;
            margin: 0 auto;
            line-height: 1.7;
        }

        /* SECTIONS */
        .section { display: none; }
        .section.active { display: block; animation: fadeUp 0.4s ease; }

        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* MENU CARDS */
        .menu-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            max-width: 700px;
            margin: 50px auto 0;
            padding: 0 40px;
        }

        .menu-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px 36px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            text-align: left;
        }

        .menu-card::before {
            content: '';
            position: absolute;
            inset: 0;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .menu-card.compose::before {
            background: radial-gradient(circle at top left, rgba(0,229,196,0.08), transparent 60%);
        }

        .menu-card.inbox::before {
            background: radial-gradient(circle at top left, rgba(123,94,167,0.1), transparent 60%);
        }

        .menu-card:hover::before { opacity: 1; }
        .menu-card:hover {
            border-color: rgba(255,255,255,0.12);
            transform: translateY(-4px);
        }

        .menu-card:hover .card-icon {
            transform: scale(1.1);
        }

        .card-icon {
            font-size: 36px;
            margin-bottom: 20px;
            display: block;
            transition: transform 0.3s;
        }

        .card-title {
            font-family: 'Syne', sans-serif;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .card-desc {
            color: var(--muted);
            font-size: 14px;
            line-height: 1.6;
        }

        .card-arrow {
            position: absolute;
            bottom: 24px;
            right: 24px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            font-size: 16px;
            transition: all 0.3s;
        }

        .menu-card:hover .card-arrow {
            border-color: var(--accent);
            color: var(--accent);
            background: rgba(0,229,196,0.1);
        }

        /* MAIN CONTENT AREA */
        .content-area {
            max-width: 860px;
            margin: 0 auto;
            padding: 40px;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 40px;
        }

        .back-btn {
            background: var(--card);
            border: 1px solid var(--border);
            color: var(--muted);
            width: 40px;
            height: 40px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }

        .back-btn:hover {
            border-color: rgba(255,255,255,0.15);
            color: var(--text);
        }

        .section-title {
            font-family: 'Syne', sans-serif;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        /* FORM */
        .form-group { margin-bottom: 16px; }

        .form-label {
            display: block;
            font-size: 12px;
            font-weight: 500;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .form-input {
            width: 100%;
            background: var(--card);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 14px 18px;
            border-radius: 12px;
            font-family: 'DM Sans', sans-serif;
            font-size: 15px;
            transition: all 0.2s;
            outline: none;
        }

        .form-input:focus {
            border-color: rgba(0,229,196,0.4);
            box-shadow: 0 0 0 3px rgba(0,229,196,0.06);
        }

        textarea.form-input { height: 140px; resize: none; }

        /* BUTTONS */
        .btn-primary {
            background: var(--accent);
            color: #000;
            border: none;
            padding: 14px 28px;
            border-radius: 12px;
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,229,196,0.3);
        }

        .btn-send {
            background: linear-gradient(135deg, var(--accent), #00b8ff);
            color: #000;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-send:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(0,229,196,0.3);
        }

        .btn-skip {
            background: transparent;
            color: var(--muted);
            border: 1px solid var(--border);
            padding: 10px 20px;
            border-radius: 8px;
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-skip:hover {
            border-color: rgba(232,93,74,0.4);
            color: var(--accent3);
        }

        /* DRAFT CARDS */
        .drafts-grid {
            display: grid;
            gap: 16px;
            margin-top: 32px;
        }

        .draft-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            transition: border-color 0.2s;
            animation: fadeUp 0.4s ease backwards;
        }

        .draft-card:nth-child(2) { animation-delay: 0.1s; }
        .draft-card:nth-child(3) { animation-delay: 0.2s; }

        .draft-card:hover { border-color: rgba(0,229,196,0.2); }

        .draft-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            background: rgba(255,255,255,0.02);
        }

        .draft-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: 'Syne', sans-serif;
            font-size: 13px;
            font-weight: 700;
        }

        .tone-pill {
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }

        .tone-Professional { background: rgba(0,229,196,0.12); color: var(--accent); border: 1px solid rgba(0,229,196,0.2); }
        .tone-Friendly { background: rgba(123,94,167,0.15); color: #b48ce8; border: 1px solid rgba(123,94,167,0.25); }
        .tone-Direct { background: rgba(232,93,74,0.1); color: #e85d4a; border: 1px solid rgba(232,93,74,0.2); }

        .draft-textarea {
            width: 100%;
            background: transparent;
            border: none;
            color: var(--text);
            padding: 20px;
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            line-height: 1.7;
            resize: none;
            height: 160px;
            outline: none;
        }

        .draft-footer {
            padding: 12px 20px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: flex-end;
        }

        /* EMAIL CARDS */
        .email-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 20px;
            animation: fadeUp 0.4s ease;
            transition: border-color 0.2s;
        }

        .email-card:hover { border-color: rgba(123,94,167,0.25); }

        .email-meta {
            padding: 20px 24px 16px;
            border-bottom: 1px solid var(--border);
        }

        .email-from {
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent2), var(--accent));
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            color: white;
            flex-shrink: 0;
        }

        .email-subject {
            font-family: 'Syne', sans-serif;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .email-preview {
            font-size: 13px;
            color: var(--muted);
            line-height: 1.6;
        }

        .reply-section {
            padding: 20px 24px;
        }

        .reply-label {
            font-size: 11px;
            font-weight: 500;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .reply-label::before {
            content: '';
            width: 16px;
            height: 1px;
            background: var(--accent);
        }

        .reply-textarea {
            width: 100%;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 16px;
            border-radius: 10px;
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            line-height: 1.7;
            resize: none;
            height: 140px;
            outline: none;
            transition: border-color 0.2s;
        }

        .reply-textarea:focus {
            border-color: rgba(123,94,167,0.4);
        }

        .email-actions {
            display: flex;
            gap: 10px;
            margin-top: 12px;
        }

        /* LOADING */
        .loading-state {
            text-align: center;
            padding: 80px 40px;
            color: var(--muted);
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 2px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .loading-state p {
            font-size: 14px;
            letter-spacing: 0.5px;
        }

        /* EMPTY STATE */
        .empty-state {
            text-align: center;
            padding: 80px 40px;
            color: var(--muted);
        }

        .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
        .empty-state p { font-size: 15px; }

        /* TOAST */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--card);
            border: 1px solid rgba(0,229,196,0.3);
            color: var(--text);
            padding: 14px 22px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            z-index: 999;
            display: none;
            animation: slideIn 0.3s ease;
        }

        .toast.show { display: flex; align-items: center; gap: 10px; }
        .toast::before { content: '✓'; color: var(--accent); font-weight: 700; }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        /* RESPONSIVE */
        @media (max-width: 600px) {
            .menu-grid { grid-template-columns: 1fr; padding: 0 20px; }
            .content-area { padding: 20px; }
            nav { padding: 16px 20px; }
        }
    </style>
</head>
<body>
<div class="app">

    <!-- NAV -->
    <nav>
        <div class="logo">
            <div class="logo-dot"></div>
            MailMind
        </div>
        <div class="nav-badge">AI Powered</div>
    </nav>

    <!-- MENU SECTION -->
    <div class="section active" id="menu">
        <div class="hero">
            <div class="hero-eyebrow">✦ Intelligent Email Agent</div>
            <h1>Your emails,<br><span>handled by AI</span></h1>
            <p>Compose polished emails in seconds or let AI draft replies to your inbox — all in one place.</p>
        </div>
        <div class="menu-grid">
            <div class="menu-card compose" onclick="showSection('compose')">
                <span class="card-icon">✍️</span>
                <div class="card-title">Write New Email</div>
                <div class="card-desc">Tell us what you want to say. Get 3 AI-polished drafts instantly.</div>
                <div class="card-arrow">→</div>
            </div>
            <div class="menu-card inbox" onclick="loadEmails()">
                <span class="card-icon">📬</span>
                <div class="card-title">Reply to Inbox</div>
                <div class="card-desc">AI reads your pending emails and generates smart, contextual replies.</div>
                <div class="card-arrow">→</div>
            </div>
        </div>
    </div>

    <!-- COMPOSE SECTION -->
    <div class="section" id="compose">
        <div class="content-area">
            <div class="section-header">
                <button class="back-btn" onclick="showSection('menu')">←</button>
                <div class="section-title">Write New Email</div>
            </div>

            <div class="form-group">
                <label class="form-label">To</label>
                <input class="form-input" id="to_email" placeholder="recipient@gmail.com" />
            </div>
            <div class="form-group">
                <label class="form-label">Subject</label>
                <input class="form-input" id="email_subject" placeholder="What's this about?" />
            </div>
            <div class="form-group">
                <label class="form-label">Your Message</label>
                <textarea class="form-input" id="email_message" placeholder="Write your raw message here — AI will polish it into 3 professional drafts..."></textarea>
            </div>
            <button class="btn-primary" onclick="generateDrafts()">
                ✦ Generate 3 Drafts
            </button>

            <div id="drafts"></div>
        </div>
    </div>

    <!-- REPLIES SECTION -->
    <div class="section" id="replies">
        <div class="content-area">
            <div class="section-header">
                <button class="back-btn" onclick="showSection('menu')">←</button>
                <div class="section-title">Pending Emails</div>
            </div>
            <div id="emails"></div>
        </div>
    </div>

    <!-- TOAST -->
    <div class="toast" id="toast">Email sent successfully!</div>

</div>

<script>
    function showSection(id) {
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showToast(msg) {
        const t = document.getElementById('toast');
        t.textContent = msg;
        t.classList.add('show');
        setTimeout(() => t.classList.remove('show'), 3500);
    }

    function getInitials(email) {
        const name = email.split('<')[0].trim();
        return name.split(' ').map(w => w[0]).join('').substring(0,2).toUpperCase() || '?';
    }

    async function generateDrafts() {
        const to = document.getElementById('to_email').value;
        const subject = document.getElementById('email_subject').value;
        const message = document.getElementById('email_message').value;
        if (!to || !message) { showToast('Please fill in To and Message fields.'); return; }

        document.getElementById('drafts').innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Generating 3 drafts for you...</p>
            </div>`;

        const res = await fetch('/generate_drafts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({to, subject, message})
        });
        const data = await res.json();

        let html = '<div class="drafts-grid">';
        data.drafts.forEach((draft, i) => {
            html += `<div class="draft-card">
                <div class="draft-header">
                    <div class="draft-badge">
                        Draft ${i+1}
                        <span class="tone-pill tone-${draft.tone}">${draft.tone}</span>
                    </div>
                </div>
                <textarea class="draft-textarea" id="draft_${i}">${draft.content}</textarea>
                <div class="draft-footer">
                    <button class="btn-send" onclick="sendDraft(${i}, '${to}', '${subject}')">Send this draft →</button>
                </div>
            </div>`;
        });
        html += '</div>';
        document.getElementById('drafts').innerHTML = html;
    }

    async function sendDraft(i, to, subject) {
        const content = document.getElementById('draft_' + i).value;
        const res = await fetch('/send', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({sender: to, subject: subject, reply: content})
        });
        const data = await res.json();
        showToast(data.message);
    }

    async function loadEmails() {
        showSection('replies');
        document.getElementById('emails').innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Reading your inbox...</p>
            </div>`;

        const res = await fetch('/emails');
        const data = await res.json();

        if (!data.length) {
            document.getElementById('emails').innerHTML = `
                <div class="empty-state">
                    <div class="icon">📭</div>
                    <p>No pending emails found.</p>
                </div>`;
            return;
        }

        let html = '';
        data.forEach((email, i) => {
            const initials = getInitials(email.sender);
            html += `<div class="email-card" id="card_${i}">
                <div class="email-meta">
                    <div class="email-from">
                        <span class="avatar">${initials}</span>
                        ${email.sender}
                    </div>
                    <div class="email-subject">${email.subject}</div>
                    <div class="email-preview">${email.body.substring(0, 180)}...</div>
                </div>
                <div class="reply-section">
                    <div class="reply-label">AI Generated Reply</div>
                    <textarea class="reply-textarea" id="reply_${i}">${email.reply}</textarea>
                    <div class="email-actions">
                        <button class="btn-send" onclick="sendEmail(${i}, '${email.sender}', '${email.subject}')">Send Reply →</button>
                        <button class="btn-skip" onclick="document.getElementById('card_${i}').remove()">Skip</button>
                    </div>
                </div>
            </div>`;
        });
        document.getElementById('emails').innerHTML = html;
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
        showToast(data.message);
        document.getElementById('card_' + i).style.opacity = '0.4';
        document.getElementById('card_' + i).style.pointerEvents = 'none';
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/generate_drafts', methods=['POST'])
def generate_drafts():
    data = request.json
    to = data['to']
    subject = data.get('subject', 'No Subject')
    message = data['message']

    tones = [
        ("Professional", "professional and formal"),
        ("Friendly", "friendly and warm"),
        ("Direct", "very direct and concise")
    ]

    drafts = []
    for tone_name, tone_desc in tones:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Write a {tone_desc} email based on this message:

'{message}'

Subject: {subject}
Write only the email body. Sign off as Daniyal."""
            }]
        )
        drafts.append({
            "tone": tone_name,
            "content": response.choices[0].message.content
        })

    return jsonify({"drafts": drafts})

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
    send_email(service, data['sender'], data['subject'], data['reply'])
    return jsonify({'message': 'Email sent successfully!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)