#!/usr/bin/env python3
"""
Sales Pipeline Tracker - Web Interface

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

STAGES = [
    ("lead", "Lead", "○"),
    ("contacted", "Contacted", "◐"),
    ("qualified", "Qualified", "◑"),
    ("proposal", "Proposal", "◕"),
    ("negotiation", "Negotiation", "●"),
    ("won", "Won", "✓"),
    ("lost", "Lost", "✗"),
]

STAGE_COLORS = {
    "lead": "#6b7280",
    "contacted": "#3b82f6",
    "qualified": "#8b5cf6",
    "proposal": "#f59e0b",
    "negotiation": "#ef4444",
    "won": "#10b981",
    "lost": "#9ca3af",
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
    <title>Sales Pipeline</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f3f4f6;
            color: #1f2937;
            line-height: 1.5;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            background: #1f2937;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
        }
        header h1 { font-size: 1.5rem; }
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .stats span { background: rgba(255,255,255,0.1); padding: 5px 12px; border-radius: 4px; }

        /* Pipeline Board */
        .pipeline {
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding-bottom: 20px;
        }
        .stage-column {
            min-width: 280px;
            background: #e5e7eb;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
        }
        .stage-header {
            padding: 12px 15px;
            font-weight: 600;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }
        .stage-header .count {
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
        }
        .stage-deals {
            padding: 10px;
            flex: 1;
            min-height: 200px;
        }

        /* Deal Cards */
        .deal-card {
            background: white;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: box-shadow 0.2s;
        }
        .deal-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .deal-card h3 { font-size: 0.95rem; margin-bottom: 5px; }
        .deal-value { color: #059669; font-weight: 600; font-size: 1.1rem; }
        .deal-contact { color: #6b7280; font-size: 0.85rem; margin-top: 5px; }
        .deal-followup {
            font-size: 0.8rem;
            margin-top: 8px;
            padding: 4px 8px;
            background: #fef3c7;
            color: #92400e;
            border-radius: 4px;
            display: inline-block;
        }
        .deal-followup.overdue { background: #fee2e2; color: #dc2626; }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 100;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
        }
        .modal-header {
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-header h2 { font-size: 1.25rem; }
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #6b7280;
        }
        .modal-body { padding: 20px; }

        /* Forms */
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 1rem;
        }
        .form-group textarea { resize: vertical; min-height: 80px; }
        .form-row { display: flex; gap: 15px; }
        .form-row .form-group { flex: 1; }

        /* Buttons */
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
        }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-primary:hover { background: #2563eb; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-danger:hover { background: #dc2626; }
        .btn-secondary { background: #e5e7eb; color: #374151; }
        .btn-add {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            font-size: 2rem;
            background: #3b82f6;
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
        .btn-add:hover { background: #2563eb; }

        /* Notes */
        .notes-list { margin-top: 15px; }
        .note-item {
            background: #f9fafb;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        .note-date { color: #6b7280; font-size: 0.8rem; }

        .actions { display: flex; gap: 10px; margin-top: 20px; }
        .actions .btn { flex: 1; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Sales Pipeline</h1>
            <div class="stats">
                <span>{{ active_count }} active deals</span>
                <span>${{ "{:,.0f}".format(active_value) }} pipeline value</span>
                <span>{{ won_count }} won (${{ "{:,.0f}".format(won_value) }})</span>
            </div>
        </div>
    </header>

    <div class="container">
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
                        <div class="deal-followup {{ 'overdue' if deal.followup_date < today else '' }}">
                            Follow-up: {{ deal.followup_date }}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            {% endfor %}

            <!-- Won/Lost Column -->
            <div class="stage-column">
                <div class="stage-header" style="background: #10b981">
                    <span>✓ Won</span>
                    <span class="count">{{ deals_by_stage.get('won', [])|length }}</span>
                </div>
                <div class="stage-deals">
                    {% for deal in deals_by_stage.get('won', [])[:5] %}
                    <div class="deal-card" onclick="showDeal({{ deal.id }})">
                        <h3>{{ deal.name }}</h3>
                        <div class="deal-value">${{ "{:,.0f}".format(deal.value) }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <button class="btn-add" onclick="showAddModal()">+</button>

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
                        <label>Company / Deal Name *</label>
                        <input type="text" name="name" id="dealName" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Value ($)</label>
                            <input type="number" name="value" id="dealValue" step="0.01">
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
                        <input type="text" name="contact" id="dealContact">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" name="email" id="dealEmail">
                        </div>
                        <div class="form-group">
                            <label>Phone</label>
                            <input type="tel" name="phone" id="dealPhone">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Follow-up Date</label>
                        <input type="date" name="followup" id="dealFollowup">
                    </div>
                    <div class="form-group" id="noteGroup">
                        <label>Add Note</label>
                        <textarea name="note" id="dealNote" placeholder="Add a note..."></textarea>
                    </div>
                    <div id="existingNotes"></div>
                    <div class="actions">
                        <button type="submit" class="btn btn-primary">Save</button>
                        <button type="button" class="btn btn-danger" id="deleteBtn" onclick="deleteDeal()" style="display:none">Delete</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        const deals = {{ deals_json|safe }};

        function showAddModal() {
            document.getElementById('modalTitle').textContent = 'Add Deal';
            document.getElementById('dealForm').action = '/add';
            document.getElementById('dealForm').reset();
            document.getElementById('dealId').value = '';
            document.getElementById('deleteBtn').style.display = 'none';
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

            // Show existing notes
            let notesHtml = '';
            if (deal.notes && deal.notes.length > 0) {
                notesHtml = '<div class="notes-list"><strong>Notes:</strong>';
                deal.notes.slice().reverse().forEach(note => {
                    notesHtml += `<div class="note-item"><span class="note-date">${note.timestamp.slice(0,10)}</span> ${note.text}</div>`;
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

        // Close modal on outside click
        document.getElementById('dealModal').addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });

        // Keyboard shortcut
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeModal();
            if (e.key === 'n' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
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
    )

@app.route("/add", methods=["POST"])
def add_deal():
    data = load_data()

    deal = {
        "id": data["next_id"],
        "name": request.form["name"],
        "value": float(request.form.get("value") or 0),
        "stage": request.form.get("stage", "lead"),
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

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    print("\n  Sales Pipeline - Web Interface")
    print("  " + "="*40)
    print(f"  Open http://{ip}:5000 in your browser")
    print("  Press Ctrl+C to stop\n")

    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 5000, app, use_reloader=False, use_debugger=False)
