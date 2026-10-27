# ChatBond AI — WhatsApp Friendship Analyzer & AI Reply Generator

> **"Your chats, your memories, your insights."**

ChatBond AI is a complete, beginner-friendly, full-stack web application designed to analyze exported WhatsApp chat files (`.txt`), uncovering conversational statistics, friendship insights, interactive Chart.js graphs, and AI-powered reply suggestions via the Google Gemini API.

---

## 🌟 Key Features

1. **WhatsApp Chat Upload & Parser**
   - Supports both **Android** and **iOS** WhatsApp exported formats.
   - Handles 12-hour and 24-hour timestamps, multiline messages, system messages (encryption notices, participant events), and media placeholders (`<Media omitted>`).
   - Clean drag-and-drop file upload with format and size validation.

2. **Interactive Analytics Dashboard (Chart.js)**
   - **Total volume:** Message counts, participant totals, active days, date range.
   - **Participant breakdown:** Message counts, percentage shares, media sent, and average character length.
   - **Interactive visual charts:**
     - 📊 Bar Chart: Messages per participant
     - 🍩 Doughnut Chart: Conversation share
     - 📈 Line Chart: Daily activity timeline
     - 💖 Horizontal Bar Chart: Most frequently used emojis
     - 🕒 Bar Chart: 24-hour messaging distribution (busiest hours)
   - **Word frequency cloud:** Top words exchanged, excluding common stop words.

3. **Playful Friendship Score & Insights**
   - A transparent **0–100 score** computed from 4 measurable components:
     - Chat Volume (Max 30)
     - Conversational Symmetry / Balance (Max 30)
     - Active Days Consistency (Max 20)
     - Emoji Expressiveness (Max 20)
   - Categorized tiers: *Dynamic Duo*, *Solid Companions*, *Casual Buddies*, or *Low-Key Acquaintances*.
   - Clearly labeled for **entertainment only**.

4. **AI Reply Studio (Google Gemini API)**
   - Generate 3 distinct contextual replies for any WhatsApp message.
   - Select from 6 tones: **Friendly**, **Funny**, **Cute**, **Polite**, **Professional**, or **Casual**.
   - One-click copy buttons for every suggestion.
   - Graceful fallback: If no API key is provided, a friendly setup guide is displayed while the rest of the application remains fully functional.

5. **Downloadable Reports**
   - 📥 **Export CSV**: Structured spreadsheet report containing key statistics and participant breakdowns.
   - 📄 **Text Summary**: Formatted keepsake text file summarizing your chat highlights.

6. **Privacy & Security by Design**
   - **Zero permanent storage**: Chat files are analyzed in memory and immediately discarded.
   - **No account access required**: Works strictly with exported text files.
   - AI service requests only send explicitly entered text in the Reply Generator, never unsubmitted chat logs.
   - Upload limit (16MB) and input sanitization.

---

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask
- **Frontend:** Semantic HTML5, CSS3 (WhatsApp-inspired Emerald Design System), JavaScript (ES6)
- **Charts:** Chart.js 4.x
- **AI Engine:** Google Gemini API (`google-genai` SDK)
- **Config & Server:** `python-dotenv`, `gunicorn` (Render-ready)

---

## 📁 Project Structure

```text
ChatBondAI/
├── app.py                   # Main Flask application and routes
├── analyzer.py              # WhatsApp text parser & metrics engine
├── ai_service.py            # Google Gemini AI reply generator service
├── requirements.txt         # Production & development dependencies
├── Procfile                 # Deployment process command for Render
├── .env.example             # Template for environment variables
├── .gitignore               # Ignored local files, keys, and environments
├── test_app.py              # Automated test suite
├── README.md                # Project documentation and guide
├── sample_data/
│   └── sample_chat.txt      # Bundled sample conversation for instant demo
├── templates/
│   ├── base.html            # Shared navigation, alert banner, and footer
│   ├── index.html           # Landing page with hero, drag-and-drop upload
│   ├── dashboard.html       # Analytics dashboard with Chart.js
│   ├── replies.html         # AI Reply Studio interface
│   ├── about.html           # Privacy policy and technical details
│   └── 404.html             # Friendly error page
└── static/
    ├── css/
    │   └── style.css        # Responsive Emerald WhatsApp theme
    └── js/
        ├── main.js          # Drag-and-drop, copy buttons, AI fetch
        └── charts.js        # Chart.js initialization logic
```

---

## 🚀 Getting Started Locally

### Prerequisites
- Python 3.9 or newer installed on your computer ([python.org](https://www.python.org/downloads/))
- Git (optional)

### Step 1: Navigate to the Project Directory
Open your terminal (PowerShell, Command Prompt, or Bash) and go to the project folder:
```bash
cd ChatBondAI
```

### Step 2: Create and Activate a Virtual Environment
**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(On macOS / Linux: `python3 -m venv venv && source venv/bin/activate`)*

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure the Google Gemini API Key (Optional for AI Replies)
1. Copy `.env.example` to create `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in any text editor.
3. Get a free API key from [Google AI Studio](https://aistudio.google.com/).
4. Set the key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
*(Note: If you don't configure an API key right now, all chat analytics, demo chats, charts, and report downloads still work completely!)*

### Step 5: Run the Flask Application
```bash
python app.py
```
Open your browser and visit: **`http://localhost:5000`**

---

## 🧪 Running Automated Tests

To run the automated test suite verifying uploads, demo data, format parsing, and report exports:
```bash
python -c "import test_app; test_app.test_homepage(); test_app.test_demo_route(); test_app.test_download_routes_after_demo(); test_app.test_empty_file_upload(); test_app.test_invalid_extension_upload(); test_app.test_multiline_and_ios_format_parsing(); test_app.test_ai_reply_endpoint_without_key(); print('ALL TESTS PASSED!')"
```

---

## 🌐 Deploying to Render

This application is ready for free deployment on [Render](https://render.com/):

1. Push your repository to GitHub (ensure `.env` is NOT committed; `.gitignore` is pre-configured).
2. Log into Render and click **New +** > **Web Service**.
3. Connect your GitHub repository.
4. Set the following settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. In the **Environment Variables** tab, add:
   - `GEMINI_API_KEY` = your Google Gemini API Key
   - `SECRET_KEY` = any random secure string
6. Click **Deploy Web Service**!

---

## 🔒 Privacy & Safety Notice

- **No Permanent Storage:** Chat data is processed in ephemeral memory and discarded after your session.
- **Entertainment Only:** The Friendship Score is an entertaining numerical summary of chat frequency, active days, balance, and emojis. It does not measure true emotions or relationships.
