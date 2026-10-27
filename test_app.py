import io
from app import app
from analyzer import parse_chat_text, analyze_chat

def test_homepage():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b"ChatBond AI" in response.data

def test_demo_route():
    client = app.test_client()
    response = client.get('/demo', follow_redirects=True)
    assert response.status_code == 200
    assert b"Chat Analysis Dashboard" in response.data
    assert b"Alex" in response.data
    assert b"Sam" in response.data
    assert b"Friendship Activity Score" in response.data

def test_download_routes_after_demo():
    client = app.test_client()
    # Trigger demo first to populate session
    client.get('/demo')
    
    # Download CSV
    res_csv = client.get('/download/csv')
    assert res_csv.status_code == 200
    assert res_csv.headers['Content-Type'].startswith('text/csv')
    assert b"ChatBond AI - WhatsApp Friendship Analysis Report" in res_csv.data
    assert b"Total Messages" in res_csv.data

    # Download Plaintext Summary
    res_summary = client.get('/download/summary')
    assert res_summary.status_code == 200
    assert res_summary.headers['Content-Type'].startswith('text/plain')
    assert b"CHATBOND AI" in res_summary.data

def test_empty_file_upload():
    client = app.test_client()
    data = {
        'chat_file': (io.BytesIO(b""), 'empty.txt')
    }
    response = client.post('/analyze', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"uploaded file is empty" in response.data

def test_invalid_extension_upload():
    client = app.test_client()
    data = {
        'chat_file': (io.BytesIO(b"hello world"), 'document.pdf')
    }
    response = client.post('/analyze', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid file format" in response.data

def test_multiline_and_ios_format_parsing():
    sample_text = """[12/03/2024, 10:15:00] Alice: Hey Bob!
How are you doing today?
Are you coming?
[12/03/2024, 10:16:00] Bob: Yes!
Heading over now 🎉"""
    messages = parse_chat_text(sample_text)
    assert len(messages) == 2
    assert messages[0]['sender'] == 'Alice'
    assert "How are you doing today?" in messages[0]['message']
    assert messages[1]['sender'] == 'Bob'

def test_ai_reply_endpoint_without_key():
    client = app.test_client()
    # Test POST request to generate-replies
    res = client.post('/generate-replies', json={
        'message': 'Are we meeting at 5?',
        'tone': 'friendly'
    })
    # If GEMINI_API_KEY is not set or set to placeholder, it should return a clear, structured JSON error
    assert res.status_code in [200, 400, 500]
    data = res.get_json()
    assert 'success' in data

print("All test functions defined.")
