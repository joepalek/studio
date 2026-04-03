"""
Studio Bridge - REST API for sidebar to Inbox Log + Supervisor Integration
Location: G:/My Drive/Projects/_studio/studio_bridge.py
Execute: VS Code terminal - python studio_bridge.py
"""

from flask import Flask, request, jsonify, make_response, send_file, abort
from datetime import datetime
import json
import os
from pathlib import Path

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path=None):
    return '', 204

STUDIO_DIR = Path(r"G:\My Drive\Projects\_studio")
INBOX_LOG_FILE = STUDIO_DIR / "inbox-log.jsonl"
SUPERVISOR_LOG_FILE = STUDIO_DIR / "supervisor-inbox-log.jsonl"

if not INBOX_LOG_FILE.exists():
    INBOX_LOG_FILE.touch()
if not SUPERVISOR_LOG_FILE.exists():
    SUPERVISOR_LOG_FILE.touch()

# Track supervisor messages for status updates
supervisor_messages = {}

@app.route('/inbox-log', methods=['GET'])
def get_inbox_log():
    if INBOX_LOG_FILE.exists():
        try:
            with open(INBOX_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = [json.loads(line) for line in f if line.strip()]
            return jsonify(lines)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([])

@app.route('/inbox-log', methods=['POST'])
def append_inbox_log():
    """
    POST answer from sidebar.
    Filter: if acknowledge-only, just log.
    Filter: if actionable, log + send to supervisor.
    """
    try:
        entry = request.json
        entry['timestamp'] = entry.get('timestamp', datetime.now().isoformat())
        
        # Write to inbox log
        with open(INBOX_LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Determine if actionable
        is_acknowledge_only = (
            entry.get('answer', '').lower().strip() in ['ok', 'yes', 'noted', 'acknowledged'] and
            entry.get('source') == 'supervisor' and
            entry.get('urgency') == 'INFO'
        )
        
        supervisor_msg = None
        
        if not is_acknowledge_only:
            # This is actionable — send to supervisor
            supervisor_msg = {
                'id': f"sup-{entry.get('id')}-{datetime.now().timestamp()}",
                'inbox_id': entry.get('id'),
                'question': entry.get('question'),
                'answer': entry.get('answer'),
                'project': entry.get('project'),
                'type': entry.get('type'),
                'sent_at': datetime.now().isoformat(),
                'read_at': None,
                'completed_at': None,
                'error': None,
                'status': 'sent'
            }
            
            # Write to supervisor log
            with open(SUPERVISOR_LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
                f.write(json.dumps(supervisor_msg) + '\n')
            
            # Write to supervisor-inbox.json so supervisor sees it as an inbox item
            supervisor_inbox_path = STUDIO_DIR / "supervisor-inbox.json"
            sup_inbox = []
            if supervisor_inbox_path.exists():
                try:
                    with open(supervisor_inbox_path, 'r', encoding='utf-8') as f:
                        sup_inbox = json.load(f)
                except:
                    sup_inbox = []
            
            # Add as inbox item for supervisor
            sup_inbox.append({
                'id': supervisor_msg['id'],
                'title': f"Human Decision: {entry.get('answer', 'No answer')[:60]}",
                'finding': f"From: {entry.get('source', 'mobile')} | Project: {entry.get('project', 'studio')}",
                'urgency': 'WARN',
                'source': 'human',
                'type': 'human_decision',
                'project': entry.get('project'),
                'original_answer': entry.get('answer'),
                'timestamp': datetime.now().isoformat(),
                'status': 'new'
            })
            
            with open(supervisor_inbox_path, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(sup_inbox, f, indent=2)
            
            supervisor_messages[supervisor_msg['id']] = supervisor_msg
        
        return jsonify({
            'ok': True,
            'logged': True,
            'actionable': not is_acknowledge_only,
            'supervisor_msg_id': supervisor_msg['id'] if supervisor_msg else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/answer', methods=['POST'])
def answer_from_sidebar():
    """
    Simplified endpoint from sidebar: {id, answer}
    """
    try:
        data = request.json
        answer_id = data.get('id')
        answer_text = data.get('answer')
        
        if not answer_id or not answer_text:
            return jsonify({'error': 'Missing id or answer'}), 400
        
        # Build full log entry
        full_entry = {
            'id': answer_id,
            'answer': answer_text,
            'timestamp': datetime.now().isoformat(),
            'question': 'Unknown',
            'source': 'mobile',
            'urgency': 'INFO',
            'project': 'studio',
            'type': 'decision'
        }
        
        # Write to inbox log — MUST succeed
        with open(INBOX_LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
            f.write(json.dumps(full_entry) + '\n')
        
        return jsonify({'ok': True, 'logged': True})
    except Exception as e:
        import traceback
        print(f"[BRIDGE ERROR] /answer failed: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
        
        # Try to find the original question in inbox-log
        question_data = {}
        if INBOX_LOG_FILE.exists():
            try:
                with open(INBOX_LOG_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = json.loads(line)
                        if entry.get('id') == answer_id:
                            question_data = entry
                            break
            except:
                pass
        
        # Build full log entry
        full_entry = {
            'id': answer_id,
            'answer': answer_text,
            'timestamp': datetime.now().isoformat(),
            'question': question_data.get('question', 'Unknown'),
            'source': question_data.get('source', 'mobile'),
            'urgency': question_data.get('urgency', 'INFO'),
            'project': question_data.get('project', 'studio'),
            'type': question_data.get('type', 'decision')
        }
        
        print(f"[BRIDGE] Writing to inbox-log: {INBOX_LOG_FILE}")
        # Write to inbox log
        with open(INBOX_LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
            f.write(json.dumps(full_entry) + '\n')
        print(f"[BRIDGE] ✓ Written to inbox-log")
        
        # Determine if actionable
        is_acknowledge_only = (
            full_entry.get('answer', '').lower().strip() in ['ok', 'yes', 'noted', 'acknowledged'] and
            full_entry.get('source') == 'supervisor' and
            full_entry.get('urgency') == 'INFO'
        )
        
        supervisor_msg = None
        
        if not is_acknowledge_only:
            # This is actionable — send to supervisor
            supervisor_msg = {
                'id': f"sup-{answer_id}-{datetime.now().timestamp()}",
                'inbox_id': answer_id,
                'question': full_entry.get('question'),
                'answer': answer_text,
                'project': full_entry.get('project'),
                'type': full_entry.get('type'),
                'sent_at': datetime.now().isoformat(),
                'read_at': None,
                'completed_at': None,
                'error': None,
                'status': 'sent'
            }
            
            # Write to supervisor log
            with open(SUPERVISOR_LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
                f.write(json.dumps(supervisor_msg) + '\n')
            
            # Write to supervisor-inbox.json so supervisor sees it
            supervisor_inbox_path = STUDIO_DIR / "supervisor-inbox.json"
            sup_inbox = []
            if supervisor_inbox_path.exists():
                try:
                    with open(supervisor_inbox_path, 'r', encoding='utf-8') as f:
                        sup_inbox = json.load(f)
                except:
                    sup_inbox = []
            
            sup_inbox.append({
                'id': supervisor_msg['id'],
                'title': f"Human Decision: {answer_text[:60]}",
                'finding': f"From: {full_entry.get('source')} | Project: {full_entry.get('project')}",
                'urgency': 'WARN',
                'source': 'human',
                'type': 'human_decision',
                'project': full_entry.get('project'),
                'original_answer': answer_text,
                'timestamp': datetime.now().isoformat(),
                'status': 'new'
            })
            
            with open(supervisor_inbox_path, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(sup_inbox, f, indent=2)
            
            supervisor_messages[supervisor_msg['id']] = supervisor_msg
        
        return jsonify({
            'ok': True,
            'logged': True,
            'actionable': not is_acknowledge_only,
            'supervisor_msg_id': supervisor_msg['id'] if supervisor_msg else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/supervisor-inbox-log', methods=['GET'])
def get_supervisor_inbox_log():
    """Sidebar polls this to get supervisor message status updates"""
    if SUPERVISOR_LOG_FILE.exists():
        try:
            with open(SUPERVISOR_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = [json.loads(line) for line in f if line.strip()]
            return jsonify(lines)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([])

@app.route('/supervisor-status', methods=['POST'])
def update_supervisor_status():
    """
    Supervisor reports back on message status.
    Body: {supervisor_msg_id, status: 'read' | 'completed' | 'error', error: optional}
    """
    try:
        data = request.json
        msg_id = data.get('supervisor_msg_id')
        status = data.get('status')  # 'read', 'completed', 'error'
        error = data.get('error')
        
        # Read current log, find message, update it
        messages = []
        if SUPERVISOR_LOG_FILE.exists():
            with open(SUPERVISOR_LOG_FILE, 'r', encoding='utf-8') as f:
                messages = [json.loads(line) for line in f if line.strip()]
        
        # Find and update
        for msg in messages:
            if msg['id'] == msg_id:
                if status == 'read':
                    msg['read_at'] = datetime.now().isoformat()
                    msg['status'] = 'read'
                elif status == 'completed':
                    msg['completed_at'] = datetime.now().isoformat()
                    msg['status'] = 'completed'
                elif status == 'error':
                    msg['error'] = error
                    msg['status'] = 'error'
                break
        
        # Rewrite log
        with open(SUPERVISOR_LOG_FILE, 'w', encoding='utf-8', errors='replace') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')
        
        return jsonify({'ok': True, 'updated': msg_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/docs/<path:filename>')
def serve_doc(filename):
    """Serve any HTML/MD file from _studio folder. Called by sidebar launch button."""
    import os
    safe = os.path.basename(filename)          # strip any path traversal
    full = STUDIO_DIR / safe
    if not full.exists():
        abort(404)
    return send_file(str(full))

if __name__ == '__main__':
    print(f"Studio Bridge running on port 11435")
    print(f"Inbox log: {INBOX_LOG_FILE}")
    print(f"Supervisor log: {SUPERVISOR_LOG_FILE}")
    print(f"Listening for POST /answer requests from sidebar...")
    print(f"Listening for POST /inbox-log requests...")
    app.run(host='localhost', port=11435, debug=True)

