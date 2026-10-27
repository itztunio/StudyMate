"""
WhatsApp Chat Parser and Friendship Metrics Analyzer for ChatBond AI.
Supports both Android and iOS exported formats, 12h and 24h clocks,
multiline messages, system notifications, media placeholders, and emoji extraction.
"""

import re
import math
from collections import Counter
from datetime import datetime

# Common English stop words to filter out from word frequency calculations
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
    "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
    'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
    'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
    'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
    'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll',
    'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't",
    'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn',
    "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't",
    'ok', 'okay', 'yeah', 'yes', 'no', 'ya', 'like', 'get', 'got', 'also', 'u', 'ur'
}

# Regex to detect Unicode emojis (including compounds, skin tones, etc.)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols, Symbols and Pictographs Extended-A
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-B
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE
)

# Common regex patterns for WhatsApp chat export lines
# Android format 1: 15/01/24, 10:30 am - Name: Message OR 15/01/2024, 10:30 - Name: Message
# Android format 2: 1/15/24, 10:30:15 AM - Name: Message
# iOS format 1: [15/01/2024, 10:30:15] Name: Message
# iOS format 2: [15/01/24, 10:30:15 AM] Name: Message
PATTERNS = [
    # Android formats with " - "
    re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?[mM]\.?)?)\s*-\s*(.+?):\s*(.*)$'),
    # iOS formats with square brackets "[date, time] Name: message"
    re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?[mM]\.?)?)\]\s*(.+?):\s*(.*)$'),
    # Android dash with dash date format: 2024-01-15, 10:30 - Name: message
    re.compile(r'^(\d{4}-\d{1,2}-\d{1,2}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?[mM]\.?)?)\s*-\s*(.+?):\s*(.*)$'),
]

# System notification patterns to ignore (security code change, encryption notice, group creation)
SYSTEM_SUBSTRINGS = [
    'Messages and calls are end-to-end encrypted',
    'created group',
    'added you',
    'added',
    'left',
    'changed the subject to',
    'changed this group\'s icon',
    'changed the group description',
    'security code changed',
    'You were added to',
    'joined using this group\'s invite link'
]


def clean_invisible_chars(text):
    """Remove Left-to-Right and Right-to-Left directional marks commonly present in iOS exports."""
    return text.replace('\u200e', '').replace('\u200f', '').replace('\u202a', '').replace('\u202c', '')


def parse_datetime(date_str, time_str):
    """Safely parse various date and time combinations into a datetime object."""
    # Clean time string (e.g. normalize a.m./p.m. or special spaces)
    time_str = time_str.strip().replace('\u202f', ' ').replace('.', '').upper()
    date_str = date_str.strip()

    date_formats = ['%d/%m/%Y', '%d/%m/%y', '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d']
    time_formats = ['%I:%M %p', '%I:%M:%S %p', '%H:%M', '%H:%M:%S', '%I:%M%p', '%I:%M:%S%p']

    for df in date_formats:
        for tf in time_formats:
            fmt = f"{df} {tf}"
            try:
                return datetime.strptime(f"{date_str} {time_str}", fmt)
            except ValueError:
                pass
    
    # Fallback to date only if time fails
    for df in date_formats:
        try:
            return datetime.strptime(date_str, df)
        except ValueError:
            pass

    return None


def parse_chat_text(raw_text):
    """
    Parses WhatsApp exported raw text into structured message records.
    Handles multiline messages, cleans system notices, and flags media attachments.
    """
    cleaned_text = clean_invisible_chars(raw_text)
    lines = cleaned_text.splitlines()

    messages = []
    current_msg = None

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Check for system messages (e.g. "Messages and calls are end-to-end encrypted")
        if any(sub in line_clean for sub in SYSTEM_SUBSTRINGS):
            continue

        matched = False
        for pattern in PATTERNS:
            match = pattern.match(line)
            if match:
                date_str, time_str, sender, content = match.groups()
                
                # Check if sender itself looks like a system event
                if any(sub in content for sub in SYSTEM_SUBSTRINGS) or "changed to" in sender:
                    matched = True
                    break

                dt = parse_datetime(date_str, time_str)
                sender = sender.strip()
                content = content.strip()

                # Save previous message
                if current_msg:
                    messages.append(current_msg)

                # Media omitted detection
                is_media = False
                if '<Media omitted>' in content or 'image omitted' in content or 'audio omitted' in content or 'video omitted' in content or 'sticker omitted' in content:
                    is_media = True

                current_msg = {
                    'datetime': dt,
                    'date': dt.strftime('%Y-%m-%d') if dt else date_str,
                    'time': time_str,
                    'hour': dt.hour if dt else 0,
                    'sender': sender,
                    'message': content,
                    'is_media': is_media,
                    'char_count': len(content) if not is_media else 0,
                    'word_count': len(content.split()) if not is_media else 0
                }
                matched = True
                break

        if not matched:
            # Multiline continuation of previous message
            if current_msg:
                current_msg['message'] += '\n' + line
                if not current_msg['is_media']:
                    current_msg['char_count'] += len(line) + 1
                    current_msg['word_count'] += len(line.split())

    if current_msg:
        messages.append(current_msg)

    return messages


def extract_emojis(text):
    """Extract all unicode emojis from a string."""
    return EMOJI_PATTERN.findall(text)


def analyze_chat(messages):
    """
    Analyzes message list and computes comprehensive stats, friendship score,
    and chart data.
    """
    if not messages:
        return {'success': False, 'error': 'No chat messages could be parsed from the file.'}

    total_messages = len(messages)
    senders = Counter()
    dates = Counter()
    months = Counter()
    hours = Counter([0] * 24)  # Initialize all 24 hours
    media_count_by_sender = Counter()
    total_words_by_sender = Counter()
    total_chars_by_sender = Counter()
    all_emojis = Counter()
    emojis_by_sender = {}
    words_counter = Counter()

    for msg in messages:
        sender = msg['sender']
        senders[sender] += 1
        dates[msg['date']] += 1

        if msg.get('datetime'):
            month_key = msg['datetime'].strftime('%Y-%m')
            months[month_key] += 1
            hours[msg['hour']] += 1
        else:
            hours[0] += 1

        if msg['is_media']:
            media_count_by_sender[sender] += 1
        else:
            total_words_by_sender[sender] += msg['word_count']
            total_chars_by_sender[sender] += msg['char_count']

            # Extract emojis
            found_emojis = extract_emojis(msg['message'])
            for em in found_emojis:
                # Each character or joined emoji
                for char in em:
                    all_emojis[char] += 1
                    if sender not in emojis_by_sender:
                        emojis_by_sender[sender] = Counter()
                    emojis_by_sender[sender][char] += 1

            # Extract words for frequency (clean punctuation and filter stops)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', msg['message'].lower())
            for w in words:
                if w not in STOP_WORDS and not w.startswith('http'):
                    words_counter[w] += 1

    participants = list(senders.keys())
    participant_count = len(participants)

    if participant_count == 0:
        return {'success': False, 'error': 'No conversation participants found in chat text.'}

    most_active_sender = senders.most_common(1)[0][0]
    most_active_date, max_date_msgs = dates.most_common(1)[0]
    
    # Peak hour formatted
    busiest_hour_val = hours.most_common(1)[0][0]
    peak_period_str = datetime.strptime(str(busiest_hour_val), "%H").strftime("%I %p").lstrip('0')

    # Total characters and average message length
    overall_total_chars = sum(total_chars_by_sender.values())
    non_media_msgs_count = sum(senders[s] - media_count_by_sender[s] for s in participants)
    avg_message_len = round(overall_total_chars / max(non_media_msgs_count, 1), 1)

    # Participant breakdown
    participant_stats = []
    for s in participants:
        s_msgs = senders[s]
        s_media = media_count_by_sender[s]
        s_non_media = max(s_msgs - s_media, 1)
        s_avg_len = round(total_chars_by_sender[s] / s_non_media, 1)
        s_pct = round((s_msgs / total_messages) * 100, 1)
        top_emojis_s = emojis_by_sender.get(s, Counter()).most_common(3)
        participant_stats.append({
            'name': s,
            'messages': s_msgs,
            'percentage': s_pct,
            'media': s_media,
            'avg_length': s_avg_len,
            'top_emojis': ''.join([e[0] for e in top_emojis_s]) if top_emojis_s else '—'
        })

    # Sort participants by message count descending
    participant_stats.sort(key=lambda x: x['messages'], reverse=True)

    # Top emojis & words
    top_emojis = all_emojis.most_common(10)
    top_words = words_counter.most_common(10)

    # Sort dates chronologically for daily timeline
    sorted_dates = sorted(dates.keys())
    daily_timeline = [{'date': d, 'count': dates[d]} for d in sorted_dates]

    # Monthly breakdown
    sorted_months = sorted(months.keys())
    monthly_timeline = [{'month': m, 'count': months[m]} for m in sorted_months]

    # Hourly distribution (0 to 23)
    hourly_distribution = [hours[h] for h in range(24)]

    # Calculate Friendship Score (Playful & transparent 0-100 metric for entertainment)
    score_details = calculate_friendship_score(
        total_messages=total_messages,
        participant_count=participant_count,
        senders=senders,
        dates_count=len(dates),
        all_emojis_count=sum(all_emojis.values())
    )

    # Generate interesting trivia facts based on actual metrics
    fun_facts = generate_fun_facts(
        total_messages=total_messages,
        participants=participant_stats,
        busiest_hour_str=peak_period_str,
        most_active_date=most_active_date,
        max_date_msgs=max_date_msgs,
        top_emoji=top_emojis[0][0] if top_emojis else None,
        top_word=top_words[0][0] if top_words else None,
        score=score_details['total_score']
    )

    return {
        'success': True,
        'summary': {
            'total_messages': total_messages,
            'participant_count': participant_count,
            'most_active_sender': most_active_sender,
            'most_active_date': most_active_date,
            'most_active_date_msgs': max_date_msgs,
            'busiest_hour': peak_period_str,
            'avg_message_length': avg_message_len,
            'total_emojis_used': sum(all_emojis.values()),
            'date_range': f"{sorted_dates[0]} to {sorted_dates[-1]}" if sorted_dates else "N/A",
            'days_active': len(dates)
        },
        'participants': participant_stats,
        'friendship_score': score_details,
        'fun_facts': fun_facts,
        'top_emojis': [{'emoji': e[0], 'count': e[1]} for e in top_emojis],
        'top_words': [{'word': w[0], 'count': w[1]} for w in top_words],
        'charts': {
            'participant_labels': [p['name'] for p in participant_stats],
            'participant_counts': [p['messages'] for p in participant_stats],
            'daily_labels': [d['date'] for d in daily_timeline],
            'daily_counts': [d['count'] for d in daily_timeline],
            'hourly_counts': hourly_distribution,
            'top_emoji_labels': [e[0] for e in top_emojis[:8]],
            'top_emoji_counts': [e[1] for e in top_emojis[:8]],
            'top_word_labels': [w[0] for w in top_words[:8]],
            'top_word_counts': [w[1] for w in top_words[:8]]
        }
    }


def calculate_friendship_score(total_messages, participant_count, senders, dates_count, all_emojis_count):
    """
    Computes a playful friendship activity score (0-100) based on 4 measurable components:
    1. Conversation Volume (Max 30 pts)
    2. Communication Balance (Max 30 pts) - Even distribution gives higher balance
    3. Consistency over Days (Max 20 pts)
    4. Expressiveness / Emojis (Max 20 pts)
    
    Clearly labelled for entertainment purposes.
    """
    # 1. Volume Score (Up to 30)
    # 500+ messages = 30 pts
    volume_score = min(30, round(math.log10(max(total_messages, 1)) / math.log10(600) * 30))
    volume_score = max(5, min(30, volume_score))

    # 2. Balance Score (Up to 30)
    if participant_count >= 2:
        top_two = senders.most_common(2)
        count1 = top_two[0][1]
        count2 = top_two[1][1]
        # Ratio of smaller to larger
        ratio = count2 / max(count1, 1)
        balance_score = round(ratio * 30)
    else:
        balance_score = 15

    # 3. Consistency Score (Up to 20)
    # Days with activity
    consistency_score = min(20, round(dates_count * 2))
    consistency_score = max(5, consistency_score)

    # 4. Expressiveness (Up to 20)
    # Emojis per 10 messages
    emojis_per_ten = (all_emojis_count / max(total_messages, 1)) * 10
    expressiveness_score = min(20, round(emojis_per_ten * 5))
    expressiveness_score = max(4, expressiveness_score)

    total_score = min(100, volume_score + balance_score + consistency_score + expressiveness_score)

    if total_score >= 85:
        tier = "Dynamic Duo 🌟"
        tagline = "Inseparable! You chat regularly with high energy and balanced banter."
    elif total_score >= 70:
        tier = "Solid Companions 🤝"
        tagline = "Great chemistry and steady communication keep your bond thriving."
    elif total_score >= 50:
        tier = "Casual Buddies ☕"
        tagline = "Reliable and easygoing. You catch up whenever things happen."
    else:
        tier = "Low-Key Acquaintances 🌱"
        tagline = "Concise and to the point! Fresh conversations with room to grow."

    return {
        'total_score': total_score,
        'tier': tier,
        'tagline': tagline,
        'breakdown': {
            'volume': {'score': volume_score, 'max': 30, 'label': 'Chat Volume'},
            'balance': {'score': balance_score, 'max': 30, 'label': 'Conversation Balance'},
            'consistency': {'score': consistency_score, 'max': 20, 'label': 'Active Days Consistency'},
            'expressiveness': {'score': expressiveness_score, 'max': 20, 'label': 'Emoji Expressiveness'}
        }
    }


def generate_fun_facts(total_messages, participants, busiest_hour_str, most_active_date, max_date_msgs, top_emoji, top_word, score):
    """Generates engaging, lighthearted conversation facts based strictly on chat data."""
    facts = []

    facts.append(f"💬 You both shared a total of {total_messages:,} messages across the analyzed timeline.")

    if len(participants) >= 2:
        p1 = participants[0]
        p2 = participants[1]
        diff = p1['messages'] - p2['messages']
        if diff < 15:
            facts.append(f"⚖️ Incredible symmetry! {p1['name']} ({p1['messages']}) and {p2['name']} ({p2['messages']}) sent almost the exact same number of messages.")
        else:
            facts.append(f"🏆 {p1['name']} leads the conversation count with {p1['messages']:,} messages ({p1['percentage']}%), edging ahead of {p2['name']} by {diff:,} messages.")

    facts.append(f"⏰ Prime Chatting Hour: Most messages were exchanged around {busiest_hour_str}.")
    facts.append(f"📅 Record Breaking Day: {most_active_date} was your busiest day with {max_date_msgs} messages exchanged!")

    if top_emoji:
        facts.append(f"💖 Favorite Emoji: '{top_emoji}' was your go-to expression throughout the conversation.")

    if top_word:
        facts.append(f"🔤 Most repeated signature word: \"{top_word}\" appeared frequently in your talks.")

    return facts
