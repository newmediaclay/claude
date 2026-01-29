#!/usr/bin/env python3
"""
Sales Pipeline Tracker - Web Interface
New Media Campaigns

Run with: python web.py
Then open: http://localhost:5000
"""

import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

app = Flask(__name__)

# Middleware to rewrite Host header to localhost (bypass host validation)
class HostRewriter:
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        environ['HTTP_HOST'] = 'localhost:5000'
        environ['SERVER_NAME'] = 'localhost'
        return self.app(environ, start_response)

app.wsgi_app = HostRewriter(app.wsgi_app)

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_FILE = Path(__file__).parent / "data" / "deals.json"

# Your name for email templates
YOUR_NAME = "Clay"

STAGES = [
    ("contact", "Contact", "○"),
    ("proposal_sent", "Proposal Sent", "◕"),
    ("won", "Won", "✓"),
    ("lost", "Lost", "✗"),
]

STAGE_COLORS = {
    "contact": "#0077ff",
    "proposal_sent": "#7eb8da",
    "won": "#059669",
    "lost": "#6b7280",
}

# Email Templates
EMAIL_TEMPLATES = {
    "initial_followup": {
        "name": "Initial Follow-up",
        "subject": "Following up on our conversation",
        "body": """Hi {contact_first_name},

I hope this message finds you well! I wanted to follow up on our recent conversation about how we might be able to help {company}.

I'd love to schedule a quick call to discuss your needs in more detail and answer any questions you might have.

Would you have some time this week for a brief chat?

Best regards,
{your_name}"""
    },
    "proposal_followup": {
        "name": "Proposal Follow-up",
        "subject": "Following up on our proposal",
        "body": """Hi {contact_first_name},

I wanted to check in regarding the proposal we sent over for {company}. I hope you've had a chance to review it.

I'm happy to walk through any details or answer questions you might have. We're excited about the possibility of working together!

Do you have any questions I can help address?

Best regards,
{your_name}"""
    },
    "gentle_reminder": {
        "name": "Gentle Reminder",
        "subject": "Quick check-in",
        "body": """Hi {contact_first_name},

I hope you're doing well! I wanted to send a quick note to see if you had any updates on your timeline for moving forward.

No pressure at all - I just wanted to make sure I'm available whenever you're ready to chat.

Let me know if there's anything I can help with!

Best,
{your_name}"""
    },
    "value_reminder": {
        "name": "Value Reminder",
        "subject": "Thinking about {company}",
        "body": """Hi {contact_first_name},

I was thinking about our conversation and wanted to share a quick thought about how we could help {company} achieve your goals.

Based on what you shared, I believe we could make a real impact, especially given the ${deal_value} investment we discussed.

Would you be open to a brief call to explore this further?

Looking forward to hearing from you,
{your_name}"""
    }
}

# ============================================================================
# DATA MANAGEMENT
# ============================================================================

def load_data() -> dict:
    if not DATA_FILE.exists():
        return {"deals": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def get_deal_by_id(data: dict, deal_id: int):
    for deal in data["deals"]:
        if deal["id"] == deal_id:
            return deal
    return None

# ============================================================================
# HTML TEMPLATE
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Pipeline | New Media Campaigns</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        /* Header - Compact */
        header {
            background: linear-gradient(135deg, #0f172a 0%, #0f172a 100%);
            color: white;
            padding: 0;
            margin-bottom: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .logo {
            width: 32px;
            height: 32px;
            background: #0077ff;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9rem;
        }
        header h1 {
            font-size: 1.1rem;
            font-weight: 600;
            letter-spacing: -0.3px;
        }
        .tagline {
            color: rgba(255,255,255,0.6);
            font-size: 0.75rem;
            margin-left: 10px;
        }
        .stats {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: rgba(255,255,255,0.08);
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.08);
            text-align: center;
        }
        .stat-value {
            font-size: 1rem;
            font-weight: 600;
        }
        .stat-label {
            font-size: 0.65rem;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        /* Welcome Section */
        .welcome {
            background: white;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border-left: 4px solid #0077ff;
        }
        .welcome h2 {
            font-size: 0.95rem;
            color: #0f172a;
            margin-bottom: 4px;
        }
        .welcome p {
            color: #64748b;
            font-size: 0.85rem;
        }

        /* Alert Banner */
        .alert-banner {
            background: linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%);
            border: 1px solid #fecaca;
            border-left: 4px solid #ef4444;
            padding: 16px 20px;
            margin-bottom: 24px;
            border-radius: 8px;
        }
        .alert-banner h3 {
            color: #dc2626;
            font-size: 0.95rem;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .alert-item {
            padding: 10px 0;
            border-bottom: 1px solid #fecaca;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .alert-item:last-child { border-bottom: none; }
        .alert-item .deal-name { font-weight: 500; color: #1e293b; }
        .alert-item .due-date { color: #dc2626; font-size: 0.85rem; }
        .alert-actions { display: flex; gap: 8px; }
        .alert-item .view-btn, .alert-item .email-btn {
            padding: 6px 14px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.85rem;
            cursor: pointer;
            border: none;
            font-weight: 500;
        }
        .alert-item .view-btn {
            background: #dc2626;
            color: white;
        }
        .alert-item .view-btn:hover { background: #b91c1c; }
        .alert-item .email-btn {
            background: #7c3aed;
            color: white;
        }
        .alert-item .email-btn:hover { background: #6d28d9; }

        /* Pipeline Board */
        .pipeline {
            display: flex;
            gap: 16px;
            overflow-x: auto;
            padding-bottom: 20px;
        }
        .stage-column {
            min-width: 300px;
            flex: 1;
            background: #f1f5f9;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
        }
        .stage-header {
            padding: 14px 16px;
            font-weight: 600;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }
        .stage-header .count {
            background: rgba(255,255,255,0.25);
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
        }
        .stage-deals {
            padding: 12px;
            flex: 1;
            min-height: 250px;
        }

        /* Deal Cards */
        .deal-card {
            background: white;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid #e2e8f0;
        }
        .deal-card:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
            transform: translateY(-2px);
        }
        .deal-card h3 {
            font-size: 0.95rem;
            margin-bottom: 6px;
            color: #1e293b;
        }
        .deal-value {
            color: #059669;
            font-weight: 700;
            font-size: 1.15rem;
        }
        .deal-contact {
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 6px;
        }
        .deal-followup {
            font-size: 0.8rem;
            margin-top: 10px;
            padding: 6px 10px;
            background: #fef3c7;
            color: #92400e;
            border-radius: 6px;
            display: inline-block;
        }
        .deal-followup.overdue {
            background: #fee2e2;
            color: #dc2626;
        }
        .deal-email-btn {
            margin-top: 10px;
            padding: 6px 12px;
            background: #7c3aed;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .deal-email-btn:hover { background: #6d28d9; }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(4px);
            justify-content: center;
            align-items: center;
            z-index: 100;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: white;
            border-radius: 16px;
            width: 90%;
            max-width: 550px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
        }
        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8fafc;
            border-radius: 16px 16px 0 0;
        }
        .modal-header h2 {
            font-size: 1.2rem;
            color: #1e3a5f;
        }
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #94a3b8;
            transition: color 0.2s;
        }
        .modal-close:hover { color: #475569; }
        .modal-body { padding: 24px; }

        /* Forms */
        .form-group { margin-bottom: 18px; }
        .form-group label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: #374151;
            font-size: 0.9rem;
        }
        .form-group label .required {
            color: #ef4444;
            font-weight: 700;
            font-size: 1.1em;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #0077ff;
            box-shadow: 0 0 0 3px rgba(0, 119, 255, 0.15);
        }
        .form-group textarea { resize: vertical; min-height: 100px; }
        .form-row { display: flex; gap: 16px; }
        .form-row .form-group { flex: 1; }
        /* Dollar sign input wrapper */
        .input-with-prefix {
            position: relative;
        }
        .input-with-prefix .prefix {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #6b7280;
            font-weight: 500;
        }
        .input-with-prefix input {
            padding-left: 28px;
        }

        /* Buttons */
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #0077ff;
            color: white;
            box-shadow: 0 2px 8px rgba(0, 119, 255, 0.3);
        }
        .btn-primary:hover {
            background: #0066dd;
            box-shadow: 0 4px 12px rgba(0, 119, 255, 0.4);
        }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-danger:hover { background: #dc2626; }
        .btn-secondary {
            background: #e2e8f0;
            color: #475569;
        }
        .btn-secondary:hover { background: #cbd5e1; }
        .btn-purple {
            background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
            color: white;
        }
        .btn-purple:hover {
            background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%);
        }

        .btn-add {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            font-size: 1.8rem;
            background: #0077ff;
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 119, 255, 0.4);
            transition: all 0.2s;
            z-index: 50;
        }
        .btn-add:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(0, 119, 255, 0.5);
        }

        /* Notes */
        .notes-list { margin-top: 16px; }
        .note-item {
            background: #f8fafc;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid #0077ff;
        }
        .note-date {
            display: block;
            color: #94a3b8;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .note-text {
            color: #374151;
            font-size: 0.9rem;
            line-height: 1.5;
        }

        .actions {
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }
        .actions .btn { flex: 1; }

        /* Email Modal Specific */
        .email-preview {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-top: 12px;
        }
        .email-preview-subject {
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        .email-preview-body {
            white-space: pre-wrap;
            font-size: 0.9rem;
            color: #475569;
            line-height: 1.6;
        }
        .template-select {
            margin-bottom: 16px;
        }
        .email-actions {
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }
        .email-actions .btn {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="brand">
                <div class="logo">NM</div>
                <h1>Sales Pipeline</h1>
                <span class="tagline">New Media Campaigns</span>
            </div>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{{ active_count }}</div>
                    <div class="stat-label">Active</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${{ "{:,.0f}".format(active_value) }}</div>
                    <div class="stat-label">Pipeline</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ won_count }}</div>
                    <div class="stat-label">Won</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${{ "{:,.0f}".format(won_value) }}</div>
                    <div class="stat-label">Revenue</div>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        {% if not deals %}
        <div class="welcome">
            <h2>Welcome to Your Sales Pipeline!</h2>
            <p>Get started by clicking the <strong>+</strong> button below to add your first deal. Track prospects from initial contact through proposal and closing. Set follow-up dates to stay on top of your relationships, and use email templates to reach out at just the right time.</p>
        </div>
        {% endif %}

        {% if overdue_deals %}
        <div class="alert-banner">
            <h3>⚠️ Follow-ups Due</h3>
            {% for deal in overdue_deals %}
            <div class="alert-item">
                <span class="deal-name">{{ deal.name }}</span>
                <span class="due-date">{{ deal.followup_date }}{% if deal.followup_date < today %} (OVERDUE){% endif %}</span>
                <div class="alert-actions">
                    {% if deal.email %}
                    <button class="email-btn" onclick="event.stopPropagation(); showEmailModal({{ deal.id }})">✉️ Draft Email</button>
                    {% endif %}
                    <button class="view-btn" onclick="showDeal({{ deal.id }})">View</button>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="pipeline">
            {% for stage_id, stage_name, stage_icon in stages %}
            {% if stage_id not in ['won', 'lost'] %}
            <div class="stage-column">
                <div class="stage-header" style="background: {{ stage_colors[stage_id] }}">
                    <span>{{ stage_icon }} {{ stage_name }}</span>
                    <span class="count">{{ deals_by_stage.get(stage_id, [])|length }}</span>
                </div>
                <div class="stage-deals">
                    {% for deal in deals_by_stage.get(stage_id, []) %}
                    <div class="deal-card" onclick="showDeal({{ deal.id }})">
                        <h3>{{ deal.name }}</h3>
                        <div class="deal-value">${{ "{:,.0f}".format(deal.value) }}</div>
                        {% if deal.contact %}<div class="deal-contact">{{ deal.contact }}</div>{% endif %}
                        {% if deal.followup_date %}
                        <div class="deal-followup {{ 'overdue' if deal.followup_date <= today else '' }}">
                            Follow-up: {{ deal.followup_date }}
                        </div>
                        {% endif %}
                        {% if deal.email and deal.followup_date and deal.followup_date <= today %}
                        <button class="deal-email-btn" onclick="event.stopPropagation(); showEmailModal({{ deal.id }})">✉️ Draft Email</button>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            {% endfor %}

            <!-- Won Column -->
            <div class="stage-column">
                <div class="stage-header" style="background: {{ stage_colors['won'] }}">
                    <span>✓ Won</span>
                    <span class="count">{{ deals_by_stage.get('won', [])|length }}</span>
                </div>
                <div class="stage-deals">
                    {% for deal in deals_by_stage.get('won', []) %}
                    <div class="deal-card" onclick="showDeal({{ deal.id }})">
                        <h3>{{ deal.name }}</h3>
                        <div class="deal-value">${{ "{:,.0f}".format(deal.value) }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Lost Column -->
            <div class="stage-column">
                <div class="stage-header" style="background: {{ stage_colors['lost'] }}">
                    <span>✗ Lost</span>
                    <span class="count">{{ deals_by_stage.get('lost', [])|length }}</span>
                </div>
                <div class="stage-deals">
                    {% for deal in deals_by_stage.get('lost', []) %}
                    <div class="deal-card" onclick="showDeal({{ deal.id }})">
                        <h3>{{ deal.name }}</h3>
                        <div class="deal-value" style="color: #94a3b8;">${{ "{:,.0f}".format(deal.value) }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <button class="btn-add" onclick="showAddModal()" title="Add new deal">+</button>

    <!-- Add/Edit Modal -->
    <div class="modal" id="dealModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Add Deal</h2>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <form id="dealForm" method="POST">
                    <input type="hidden" name="id" id="dealId">
                    <div class="form-group">
                        <label>Company / Deal Name <span class="required">*</span></label>
                        <input type="text" name="name" id="dealName" required placeholder="Acme Corporation">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Value</label>
                            <div class="input-with-prefix">
                                <span class="prefix">$</span>
                                <input type="number" name="value" id="dealValue" step="0.01" placeholder="50000">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Stage</label>
                            <select name="stage" id="dealStage">
                                {% for stage_id, stage_name, _ in stages %}
                                <option value="{{ stage_id }}">{{ stage_name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Contact Name</label>
                        <input type="text" name="contact" id="dealContact" placeholder="John Smith">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" name="email" id="dealEmail" placeholder="john@example.com">
                        </div>
                        <div class="form-group">
                            <label>Phone</label>
                            <input type="tel" name="phone" id="dealPhone" placeholder="555-123-4567">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Follow-up Date</label>
                        <input type="date" name="followup" id="dealFollowup">
                    </div>
                    <div class="form-group">
                        <label>Add Note</label>
                        <textarea name="note" id="dealNote" placeholder="Add a note about this deal..."></textarea>
                    </div>
                    <div id="existingNotes"></div>
                    <div class="actions">
                        <button type="submit" class="btn btn-primary" id="submitBtn">Add Deal</button>
                        <button type="button" class="btn btn-danger" id="deleteBtn" onclick="deleteDeal()" style="display:none">Delete</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Email Draft Modal -->
    <div class="modal" id="emailModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>✉️ Draft Email</h2>
                <button class="modal-close" onclick="closeEmailModal()">&times;</button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="emailDealId">
                <div class="form-group template-select">
                    <label>Template</label>
                    <select id="emailTemplate" onchange="updateEmailPreview()">
                        <option value="initial_followup">Initial Follow-up</option>
                        <option value="proposal_followup">Proposal Follow-up</option>
                        <option value="gentle_reminder">Gentle Reminder</option>
                        <option value="value_reminder">Value Reminder</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>To</label>
                    <input type="email" id="emailTo" readonly style="background: #f1f5f9;">
                </div>
                <div class="form-group">
                    <label>Subject</label>
                    <input type="text" id="emailSubject">
                </div>
                <div class="form-group">
                    <label>Message</label>
                    <textarea id="emailBody" rows="10"></textarea>
                </div>
                <div class="email-actions">
                    <button class="btn btn-purple" onclick="openInEmailClient()">
                        📧 Open in Email Client
                    </button>
                    <button class="btn btn-secondary" onclick="copyToClipboard()">
                        📋 Copy to Clipboard
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const deals = {{ deals_json|safe }};
        const templates = {{ templates_json|safe }};
        const yourName = "{{ your_name }}";
        let currentEmailDeal = null;

        function showAddModal() {
            document.getElementById('modalTitle').textContent = 'Add Deal';
            document.getElementById('dealForm').action = '/add';
            document.getElementById('dealForm').reset();
            document.getElementById('dealId').value = '';
            document.getElementById('deleteBtn').style.display = 'none';
            document.getElementById('submitBtn').textContent = 'Add Deal';
            document.getElementById('existingNotes').innerHTML = '';
            document.getElementById('dealModal').classList.add('active');
        }

        function showDeal(id) {
            const deal = deals.find(d => d.id === id);
            if (!deal) return;

            document.getElementById('modalTitle').textContent = 'Edit Deal';
            document.getElementById('dealForm').action = '/update';
            document.getElementById('dealId').value = deal.id;
            document.getElementById('dealName').value = deal.name;
            document.getElementById('dealValue').value = deal.value || '';
            document.getElementById('dealStage').value = deal.stage;
            document.getElementById('dealContact').value = deal.contact || '';
            document.getElementById('dealEmail').value = deal.email || '';
            document.getElementById('dealPhone').value = deal.phone || '';
            document.getElementById('dealFollowup').value = deal.followup_date || '';
            document.getElementById('dealNote').value = '';
            document.getElementById('deleteBtn').style.display = 'block';
            document.getElementById('submitBtn').textContent = 'Update Deal';

            let notesHtml = '';
            if (deal.notes && deal.notes.length > 0) {
                notesHtml = '<div class="notes-list"><strong>Notes:</strong>';
                deal.notes.slice().reverse().forEach(note => {
                    notesHtml += `<div class="note-item"><span class="note-date">${note.timestamp.slice(0,10)}</span><div class="note-text">${note.text}</div></div>`;
                });
                notesHtml += '</div>';
            }
            document.getElementById('existingNotes').innerHTML = notesHtml;
            document.getElementById('dealModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('dealModal').classList.remove('active');
        }

        function deleteDeal() {
            const id = document.getElementById('dealId').value;
            if (confirm('Delete this deal?')) {
                window.location.href = '/delete/' + id;
            }
        }

        // Email Modal Functions
        function showEmailModal(dealId) {
            currentEmailDeal = deals.find(d => d.id === dealId);
            if (!currentEmailDeal || !currentEmailDeal.email) return;

            document.getElementById('emailDealId').value = dealId;
            document.getElementById('emailTo').value = currentEmailDeal.email;
            document.getElementById('emailTemplate').value = 'initial_followup';
            updateEmailPreview();
            document.getElementById('emailModal').classList.add('active');
        }

        function closeEmailModal() {
            document.getElementById('emailModal').classList.remove('active');
        }

        function updateEmailPreview() {
            if (!currentEmailDeal) return;
            const templateKey = document.getElementById('emailTemplate').value;
            const template = templates[templateKey];

            const firstName = currentEmailDeal.contact ? currentEmailDeal.contact.split(' ')[0] : 'there';
            const subject = fillTemplate(template.subject, currentEmailDeal, firstName);
            const body = fillTemplate(template.body, currentEmailDeal, firstName);

            document.getElementById('emailSubject').value = subject;
            document.getElementById('emailBody').value = body;
        }

        function fillTemplate(text, deal, firstName) {
            return text
                .replace(/{contact_name}/g, deal.contact || 'there')
                .replace(/{contact_first_name}/g, firstName)
                .replace(/{company}/g, deal.name)
                .replace(/{deal_value}/g, deal.value ? deal.value.toLocaleString() : '0')
                .replace(/{your_name}/g, yourName);
        }

        function openInEmailClient() {
            const to = document.getElementById('emailTo').value;
            const subject = encodeURIComponent(document.getElementById('emailSubject').value);
            const body = encodeURIComponent(document.getElementById('emailBody').value);

            // Log the action
            logEmailDraft();

            window.location.href = `mailto:${to}?subject=${subject}&body=${body}`;
        }

        function copyToClipboard() {
            const subject = document.getElementById('emailSubject').value;
            const body = document.getElementById('emailBody').value;
            const fullText = `Subject: ${subject}\\n\\n${body}`;

            navigator.clipboard.writeText(fullText).then(() => {
                alert('Email copied to clipboard!');
                logEmailDraft();
            });
        }

        function logEmailDraft() {
            const dealId = document.getElementById('emailDealId').value;
            const templateName = document.getElementById('emailTemplate').options[document.getElementById('emailTemplate').selectedIndex].text;

            fetch('/log-email', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    deal_id: parseInt(dealId),
                    template: templateName
                })
            }).then(() => {
                closeEmailModal();
                window.location.reload();
            });
        }

        // Modal close handlers
        document.getElementById('dealModal').addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });
        document.getElementById('emailModal').addEventListener('click', function(e) {
            if (e.target === this) closeEmailModal();
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
                closeEmailModal();
            }
            if (e.key === 'n' && !e.ctrlKey && !e.metaKey &&
                document.activeElement.tagName !== 'INPUT' &&
                document.activeElement.tagName !== 'TEXTAREA') {
                showAddModal();
            }
        });
    </script>
</body>
</html>
"""

# ============================================================================
# ROUTES
# ============================================================================

@app.route("/")
def index():
    data = load_data()
    deals = data["deals"]
    today = datetime.now().strftime("%Y-%m-%d")

    # Group deals by stage
    deals_by_stage = {}
    for deal in deals:
        stage = deal["stage"]
        if stage not in deals_by_stage:
            deals_by_stage[stage] = []
        deals_by_stage[stage].append(deal)

    # Sort each stage by value descending
    for stage in deals_by_stage:
        deals_by_stage[stage].sort(key=lambda d: -d["value"])

    # Calculate stats
    active_deals = [d for d in deals if d["stage"] not in ["won", "lost"]]
    won_deals = [d for d in deals if d["stage"] == "won"]

    # Find overdue/due follow-ups
    overdue_deals = [d for d in active_deals
                     if d.get("followup_date") and d["followup_date"] <= today]
    overdue_deals.sort(key=lambda d: d["followup_date"])

    return render_template_string(
        HTML_TEMPLATE,
        deals=deals,
        deals_json=json.dumps(deals),
        deals_by_stage=deals_by_stage,
        stages=STAGES,
        stage_colors=STAGE_COLORS,
        today=today,
        active_count=len(active_deals),
        active_value=sum(d["value"] for d in active_deals),
        won_count=len(won_deals),
        won_value=sum(d["value"] for d in won_deals),
        overdue_deals=overdue_deals,
        templates_json=json.dumps(EMAIL_TEMPLATES),
        your_name=YOUR_NAME,
    )

@app.route("/add", methods=["POST"])
def add_deal():
    data = load_data()

    deal = {
        "id": data["next_id"],
        "name": request.form["name"],
        "value": float(request.form.get("value") or 0),
        "stage": request.form.get("stage", "contact"),
        "contact": request.form.get("contact", ""),
        "email": request.form.get("email", ""),
        "phone": request.form.get("phone", ""),
        "followup_date": request.form.get("followup", ""),
        "notes": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    note_text = request.form.get("note", "").strip()
    if note_text:
        deal["notes"].append({
            "text": note_text,
            "timestamp": datetime.now().isoformat(),
        })

    data["deals"].append(deal)
    data["next_id"] += 1
    save_data(data)

    return redirect(url_for("index"))

@app.route("/update", methods=["POST"])
def update_deal():
    data = load_data()
    deal_id = int(request.form["id"])
    deal = get_deal_by_id(data, deal_id)

    if deal:
        deal["name"] = request.form["name"]
        deal["value"] = float(request.form.get("value") or 0)
        deal["stage"] = request.form.get("stage", deal["stage"])
        deal["contact"] = request.form.get("contact", "")
        deal["email"] = request.form.get("email", "")
        deal["phone"] = request.form.get("phone", "")
        deal["followup_date"] = request.form.get("followup", "")
        deal["updated_at"] = datetime.now().isoformat()

        note_text = request.form.get("note", "").strip()
        if note_text:
            deal["notes"].append({
                "text": note_text,
                "timestamp": datetime.now().isoformat(),
            })

        save_data(data)

    return redirect(url_for("index"))

@app.route("/delete/<int:deal_id>")
def delete_deal(deal_id):
    data = load_data()
    data["deals"] = [d for d in data["deals"] if d["id"] != deal_id]
    save_data(data)
    return redirect(url_for("index"))

@app.route("/log-email", methods=["POST"])
def log_email():
    """Log when an email draft is created"""
    data = load_data()
    req_data = request.get_json()
    deal_id = req_data.get("deal_id")
    template_name = req_data.get("template")

    deal = get_deal_by_id(data, deal_id)
    if deal:
        deal["notes"].append({
            "text": f"📧 Drafted email using '{template_name}' template",
            "timestamp": datetime.now().isoformat(),
        })
        deal["updated_at"] = datetime.now().isoformat()
        save_data(data)

    return jsonify({"success": True})

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    print("\n  Sales Pipeline - New Media Campaigns")
    print("  " + "="*40)
    print(f"  Open http://{ip}:5000 in your browser")
    print("  Press Ctrl+C to stop\n")

    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 5000, app, use_reloader=False, use_debugger=False)
