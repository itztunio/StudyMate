"""
Google Gemini AI Service for ChatBond AI.
Generates tailored WhatsApp reply suggestions based on input message, context, and tone.
Gracefully handles missing API keys or service unavailability.
"""

import os
import json
import logging
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

logger = logging.getLogger(__name__)

# Valid tone definitions with instructions
TONE_INSTRUCTIONS = {
    'friendly': 'warm, kind, conversational, and genuinely supportive with natural friendly emojis.',
    'funny': 'humorous, witty, playful, and lighthearted with funny expressions or light teasing.',
    'cute': 'sweet, adorable, warm-hearted, cheerful with cute emojis (e.g. 🌸, ✨, 🥺).',
    'polite': 'courteous, respectful, thoughtful, and well-mannered.',
    'professional': 'clear, polite, constructive, articulate, and business-appropriate without slang.',
    'casual': 'relaxed, chill, everyday natural text, like messaging a close buddy.'
}


def is_api_key_configured():
    """Checks whether GEMINI_API_KEY is configured in the environment."""
    key = os.getenv('GEMINI_API_KEY')
    return bool(key and key.strip() and key != 'YOUR_GEMINI_API_KEY_HERE')


def generate_chat_replies(message_text, context='', tone='friendly'):
    """
    Generates 3 distinct reply suggestions using Google Gemini API.
    Returns:
        dict: {'success': bool, 'replies': list[str], 'error': str or None, 'setup_needed': bool}
    """
    if not message_text or not message_text.strip():
        return {
            'success': False,
            'replies': [],
            'error': 'Please provide a message to generate replies for.',
            'setup_needed': False
        }

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key.strip() == '' or api_key == 'YOUR_GEMINI_API_KEY_HERE':
        return {
            'success': False,
            'replies': [],
            'error': 'Google Gemini API key is not configured. Add your GEMINI_API_KEY to the .env file to enable AI replies.',
            'setup_needed': True
        }

    tone_key = tone.lower().strip() if tone else 'friendly'
    tone_desc = TONE_INSTRUCTIONS.get(tone_key, TONE_INSTRUCTIONS['friendly'])

    prompt = f"""You are a helpful WhatsApp messaging assistant.
The user received the following message from a friend or contact:
---
"{message_text.strip()}"
---

Additional context provided:
"{context.strip() if context else 'None provided.'}"

Requested tone: {tone.capitalize()} ({tone_desc})

Generate exactly 3 alternative, realistic WhatsApp reply suggestions that fit this tone.
Keep replies natural, concise, and appropriate for text messaging.
Return ONLY a valid JSON array of strings containing the 3 suggestions, for example:
["Option 1 text", "Option 2 text", "Option 3 text"]
Do not wrap in Markdown code fences if possible, or provide raw JSON only.
"""

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # Primary model gemini-flash-latest with fallback
        response = None
        for model_name in ['gemini-flash-latest', 'gemini-2.5-flash-lite', 'gemini-3-flash-preview']:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    break
            except Exception as model_err:
                logger.warning(f"Model {model_name} attempt failed: {model_err}")
                continue

        if not response or not response.text:
            return {
                'success': False,
                'replies': [],
                'error': 'Gemini models are temporarily unavailable or high demand. Please try again in a moment.',
                'setup_needed': False
            }

        response_text = response.text.strip()
        
        # Clean any markdown code blocks (e.g. ```json ... ```)
        if response_text.startswith('```'):
            lines = response_text.splitlines()
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines).strip()

        # Parse JSON
        replies = json.loads(response_text)
        if isinstance(replies, list) and len(replies) > 0:
            clean_replies = [str(r).strip() for r in replies[:3]]
            return {
                'success': True,
                'replies': clean_replies,
                'error': None,
                'setup_needed': False
            }
        else:
            return {
                'success': False,
                'replies': [],
                'error': 'AI returned an unexpected format. Please try again.',
                'setup_needed': False
            }

    except Exception as e:
        logger.error(f"Gemini API generation error: {str(e)}")
        err_msg = str(e)
        
        if 'API_KEY_INVALID' in err_msg or 'API key not valid' in err_msg or '400' in err_msg and 'API key' in err_msg:
            return {
                'success': False,
                'replies': [],
                'error': 'The provided GEMINI_API_KEY is invalid. Please verify your API key in the .env file.',
                'setup_needed': True
            }
        elif 'RESOURCE_EXHAUSTED' in err_msg or '429' in err_msg:
            return {
                'success': False,
                'replies': [],
                'error': 'Gemini API quota or rate limit reached. Please wait a moment and try again.',
                'setup_needed': False
            }
        elif '503' in err_msg or 'UNAVAILABLE' in err_msg:
            return {
                'success': False,
                'replies': [],
                'error': 'Gemini service is currently experiencing high demand. Please try again shortly.',
                'setup_needed': False
            }
        else:
            return {
                'success': False,
                'replies': [],
                'error': f'Unable to generate replies: {err_msg}',
                'setup_needed': False
            }
