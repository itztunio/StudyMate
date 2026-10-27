"""
ChatBond AI - WhatsApp Friendship Analyzer & AI Reply Generator
Flask Application Main Server
"""

import os
import io
import csv
import json
import uuid
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, flash, Response, make_response
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from analyzer import parse_chat_text, analyze_chat
from ai_service import generate_chat_replies, is_api_key_configured

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Secret key for sessions
app.secret_key = os.getenv('SECRET_KEY', 'chatbond-ai-super-secret-key-' + str(uuid.uuid4()))

# Upload security constraints
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16 MB upload limit
ALLOWED_EXTENSIONS = {'txt'}

# In-memory storage for analyzed sessions (keyed by a session UUID token)
# We store structured aggregate stats ONLY, never permanent raw chat text.
# Cleans up automatically.
ANALYSIS_CACHE = {}


def allowed_file(filename):
    """Check if the uploaded file has a .txt extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session_token():
    """Retrieves or initializes a secure session token for temporary storage."""
    if 'token' not in session:
        session['token'] = str(uuid.uuid4())
    return session['token']


@app.route('/')
def index():
    """Home landing page."""
    has_gemini = is_api_key_configured()
    return render_template('index.html', has_gemini=has_gemini)


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Handle WhatsApp .txt file upload, parse chat data,
    compute statistics, and store temporary results.
    """
    if 'chat_file' not in request.files:
        flash('No file was selected. Please choose a WhatsApp export .txt file.', 'danger')
        return redirect(url_for('index'))

    file = request.files['chat_file']
    if file.filename == '':
        flash('Please select a valid WhatsApp chat file to analyze.', 'danger')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Invalid file format. Please upload a standard WhatsApp export .txt file.', 'danger')
        return redirect(url_for('index'))

    try:
        # Read file contents in memory safely
        raw_bytes = file.read()
        if len(raw_bytes) == 0:
            flash('The uploaded file is empty. Please upload an active WhatsApp chat export.', 'warning')
            return redirect(url_for('index'))

        # Try UTF-8 decoding, fallback to utf-8-sig or latin-1
        try:
            raw_text = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                raw_text = raw_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                raw_text = raw_bytes.decode('latin-1')

        # Parse messages
        messages = parse_chat_text(raw_text)
        if not messages:
            flash(
                'Could not detect any messages in this file. Please ensure it is an unmodified WhatsApp exported chat (.txt).',
                'danger'
            )
            return redirect(url_for('index'))

        # Analyze statistics
        results = analyze_chat(messages)
        if not results.get('success'):
            flash(results.get('error', 'Error analyzing chat file.'), 'danger')
            return redirect(url_for('index'))

        # Store results temporarily using session token
        token = get_session_token()
        ANALYSIS_CACHE[token] = {
            'filename': secure_filename(file.filename),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'results': results
        }

        # Success! Redirect to dashboard
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'An unexpected error occurred while processing the file: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/demo')
def demo():
    """Loads bundled sample fictional chat for instant interactive demonstration."""
    sample_path = os.path.join(app.root_path, 'sample_data', 'sample_chat.txt')
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        messages = parse_chat_text(raw_text)
        results = analyze_chat(messages)

        token = get_session_token()
        ANALYSIS_CACHE[token] = {
            'filename': 'Sample_Alex_Sam_Chat.txt (Demo)',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'results': results
        }
        flash('Loaded interactive demo conversation! Enjoy exploring the dashboard and friendship insights.', 'info')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error loading demo data: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """Display comprehensive chat stats and interactive Chart.js visualizations."""
    token = session.get('token')
    if not token or token not in ANALYSIS_CACHE:
        flash('No chat analysis found. Please upload a chat or try the demo first.', 'warning')
        return redirect(url_for('index'))

    data = ANALYSIS_CACHE[token]
    results = data['results']
    filename = data['filename']
    has_gemini = is_api_key_configured()

    return render_template(
        'dashboard.html',
        summary=results['summary'],
        participants=results['participants'],
        friendship_score=results['friendship_score'],
        fun_facts=results['fun_facts'],
        top_emojis=results['top_emojis'],
        top_words=results['top_words'],
        charts_json=json.dumps(results['charts']),
        filename=filename,
        has_gemini=has_gemini
    )


@app.route('/insights')
def insights():
    """Direct route for Friendship Insights section."""
    token = session.get('token')
    if not token or token not in ANALYSIS_CACHE:
        flash('Please upload a chat or run the demo to view Friendship Insights.', 'warning')
        return redirect(url_for('index'))
    return redirect(url_for('dashboard') + '#friendship-insights')


@app.route('/replies', methods=['GET'])
def replies_page():
    """Standalone page for the AI Reply Generator."""
    has_gemini = is_api_key_configured()
    return render_template('replies.html', has_gemini=has_gemini)


@app.route('/generate-replies', methods=['POST'])
def generate_replies_api():
    """
    API endpoint to generate AI reply suggestions via Google Gemini.
    Accepts JSON payload: { message: str, context: str, tone: str }
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            data = request.form

        message = data.get('message', '').strip()
        context = data.get('context', '').strip()
        tone = data.get('tone', 'friendly').strip()

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message content is required.'
            }), 400

        result = generate_chat_replies(message_text=message, context=context, tone=tone)
        if not result['success']:
            status_code = 400 if result.get('setup_needed') else 500
            return jsonify(result), status_code

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error generating replies: {str(e)}'
        }), 500


@app.route('/download/csv')
def download_csv():
    """Download analysis summary and participant breakdown as a CSV file."""
    token = session.get('token')
    if not token or token not in ANALYSIS_CACHE:
        flash('No analysis available to download.', 'warning')
        return redirect(url_for('index'))

    data = ANALYSIS_CACHE[token]['results']
    summary = data['summary']
    participants = data['participants']

    output = io.StringIO()
    writer = csv.writer(output)

    # General Metrics
    writer.writerow(['ChatBond AI - WhatsApp Friendship Analysis Report'])
    writer.writerow([])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Messages', summary.get('total_messages', 0)])
    writer.writerow(['Number of Participants', summary.get('participant_count', 0)])
    writer.writerow(['Most Active Participant', summary.get('most_active_sender', 'N/A')])
    writer.writerow(['Most Active Date', summary.get('most_active_date', 'N/A')])
    writer.writerow(['Peak Messages in Single Day', summary.get('most_active_date_msgs', 0)])
    writer.writerow(['Busiest Hour', summary.get('busiest_hour', 'N/A')])
    writer.writerow(['Average Message Length (characters)', summary.get('avg_message_length', 0)])
    writer.writerow(['Days Active', summary.get('days_active', 0)])
    writer.writerow(['Date Range', summary.get('date_range', 'N/A')])
    writer.writerow([])

    # Participant Breakdown
    writer.writerow(['Participant Breakdown'])
    writer.writerow(['Participant Name', 'Total Messages', 'Message Share (%)', 'Media Sent', 'Avg Message Length (chars)'])
    for p in participants:
        writer.writerow([p['name'], p['messages'], f"{p['percentage']}%", p['media'], p['avg_length']])
    writer.writerow([])

    # Friendship Score
    score_info = data.get('friendship_score', {})
    writer.writerow(['Playful Friendship Score (Entertainment Only)'])
    writer.writerow(['Total Score (out of 100)', score_info.get('total_score', 0)])
    writer.writerow(['Chemistry Tier', score_info.get('tier', 'N/A')])
    writer.writerow([])

    # Top Emojis
    writer.writerow(['Top Emojis Used'])
    writer.writerow(['Emoji', 'Occurrences'])
    for em in data.get('top_emojis', []):
        writer.writerow([em['emoji'], em['count']])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=chatbond_analysis_report.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8'
    return response


@app.route('/download/summary')
def download_summary():
    """Download a friendly, plain-text narrative summary of the chat analysis."""
    token = session.get('token')
    if not token or token not in ANALYSIS_CACHE:
        flash('No analysis available to download.', 'warning')
        return redirect(url_for('index'))

    data = ANALYSIS_CACHE[token]['results']
    summary = data['summary']
    participants = data['participants']
    score = data['friendship_score']
    fun_facts = data.get('fun_facts', [])

    lines = [
        "============================================================",
        "     CHATBOND AI — WHATSAPP CHAT ANALYSIS SUMMARY",
        "============================================================",
        "",
        f"Generated On      : {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        f"Timeline Analyzed : {summary.get('date_range', 'N/A')} ({summary.get('days_active', 0)} active days)",
        f"Total Messages    : {summary.get('total_messages', 0):,}",
        f"Participants      : {summary.get('participant_count', 0)}",
        f"Peak Hour         : {summary.get('busiest_hour', 'N/A')}",
        f"Record Day        : {summary.get('most_active_date', 'N/A')} ({summary.get('most_active_date_msgs', 0)} messages)",
        f"Avg Message Size  : {summary.get('avg_message_length', 0)} characters",
        "",
        "------------------------------------------------------------",
        "PARTICIPANT ACTIVITY",
        "------------------------------------------------------------"
    ]

    for p in participants:
        lines.append(f"• {p['name']}: {p['messages']:,} messages ({p['percentage']}%), {p['media']} media files, avg {p['avg_length']} chars/msg")

    lines.extend([
        "",
        "------------------------------------------------------------",
        "PLAYFUL FRIENDSHIP SCORE (For Entertainment Only)",
        "------------------------------------------------------------",
        f"Score : {score.get('total_score', 0)} / 100 ({score.get('tier', '')})",
        f"Note  : {score.get('tagline', '')}",
        "",
        "------------------------------------------------------------",
        "CONVERSATION HIGHLIGHTS & FUN FACTS",
        "------------------------------------------------------------"
    ])

    for fact in fun_facts:
        lines.append(f"{fact}")

    lines.extend([
        "",
        "============================================================",
        "ChatBond AI - Built with Python Flask & Google Gemini",
        "Disclaimer: This analysis is based solely on chat metadata and",
        "frequency metrics. It is intended for fun and personal curiosity.",
        "============================================================"
    ])

    text_content = "\n".join(lines)
    response = make_response(text_content)
    response.headers['Content-Disposition'] = 'attachment; filename=chatbond_summary.txt'
    response.headers['Content-type'] = 'text/plain; charset=utf-8'
    return response


@app.route('/about')
def about():
    """Information page explaining ChatBond AI, technology, and privacy policy."""
    has_gemini = is_api_key_configured()
    return render_template('about.html', has_gemini=has_gemini)


@app.route('/clear')
def clear_analysis():
    """Clears the session analysis data and returns to home."""
    token = session.get('token')
    if token and token in ANALYSIS_CACHE:
        del ANALYSIS_CACHE[token]
    session.pop('token', None)
    flash('Analysis session cleared successfully.', 'info')
    return redirect(url_for('index'))


@app.errorhandler(413)
def request_entity_too_large(error):
    flash('The uploaded file exceeds the 16MB maximum file size limit.', 'danger')
    return redirect(url_for('index')), 413


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # Local development server
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
