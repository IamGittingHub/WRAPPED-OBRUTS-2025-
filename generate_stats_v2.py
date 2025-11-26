#!/usr/bin/env python3
"""
THE OBRUTS 2025 - Chat Stats Generator V2
Premium Edition with Enhanced Design
"""

import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import html

def parse_chat(filepath):
    """Parse WhatsApp chat export file"""
    messages = []
    message_pattern = re.compile(
        r'^\u200e?\[(\d{1,2}/\d{1,2}/\d{2}),\s*(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.*)$',
        re.IGNORECASE
    )

    current_message = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n\r')
            if not line:
                continue

            clean_line = line.lstrip('\u200e\u200f\u202a\u202b\u202c\u202d\u202e')

            match = message_pattern.match(clean_line) or message_pattern.match(line)
            if match:
                if current_message:
                    messages.append(current_message)

                date_str, time_str, sender, content = match.groups()

                month, day, year = map(int, date_str.split('/'))
                full_year = 2000 + year if year < 50 else 1900 + year

                time_match = re.match(r'(\d{1,2}):(\d{2}):(\d{2})\s*(AM|PM)?', time_str, re.IGNORECASE)
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                seconds = int(time_match.group(3))
                ampm = time_match.group(4)

                if ampm:
                    if ampm.upper() == 'PM' and hours != 12:
                        hours += 12
                    elif ampm.upper() == 'AM' and hours == 12:
                        hours = 0

                try:
                    dt = datetime(full_year, month, day, hours, minutes, seconds)
                except ValueError:
                    continue

                content = content.strip().lstrip('\u200e\u200f\u202a\u202b\u202c\u202d\u202e')
                content_lower = content.lower()
                is_media = 'omitted' in content_lower

                current_message = {
                    'date': dt,
                    'sender': sender.strip(),
                    'content': content,
                    'is_media': is_media,
                    'is_deleted': 'deleted' in content_lower or 'this message was deleted' in content_lower,
                    'is_system': 'frat party' in sender.lower() or sender.strip().startswith('2K25')
                }
            elif current_message and line.strip():
                current_message['content'] += ' ' + line.strip()

    if current_message:
        messages.append(current_message)

    return messages

def filter_last_365_days(messages):
    """Filter messages from the last 365 days"""
    cutoff = datetime(2024, 11, 25)
    end_date = datetime(2025, 11, 25, 23, 59, 59)
    return [m for m in messages if cutoff <= m['date'] <= end_date]

def normalize_name(name):
    """Normalize sender names"""
    name_map = {
        'Abanob Nashat': 'Abanob',
        'Fady Barsoum': 'Fady B',
        'Fady Henen': 'Fady H',
        'David Hana': 'David',
        'Meena Ibrahim': 'Meena',
        'Andro A.': 'Andro',
        'Kirolous Kamel': 'Kiro',
        "Thomas hanna David's Brother": 'Thomas',
        'Aziz El Romancy': 'Aziz',
        'Aziz El Romancy😍': 'Aziz',
    }
    return name_map.get(name, name)

def calculate_stats(messages):
    """Calculate comprehensive stats from messages"""
    stats = {
        'total_messages': 0,
        'total_media': 0,
        'total_chars': 0,
        'by_person': defaultdict(lambda: {
            'messages': 0,
            'media': 0,
            'total_chars': 0,
            'response_times': [],
            'active_days': set(),
            'by_hour': [0] * 24,
            'by_day': [0] * 7,
            'emojis': 0,
            'questions': 0,
            'laughs': 0,
            'exclamations': 0,
            'caps_messages': 0,
            'links': 0,
            'mentions': 0,
            'long_messages': 0,  # Messages > 200 chars
            'short_messages': 0,  # Messages < 10 chars
            'first_message': None,
            'last_message': None,
            'conversations_started': 0,
            'replied_to_count': 0,
            'weekend_messages': 0,
            'late_night_messages': 0,  # 11pm - 4am
            'morning_messages': 0,  # 5am - 9am
            'message_lengths': [],
        }),
        'by_month': defaultdict(int),
        'by_hour': [0] * 24,
        'by_day_of_week': [0] * 7,
        'daily_counts': defaultdict(int),
        'longest_message': {'sender': '', 'length': 0, 'preview': ''},
        'active_days': set(),
        'conversations': [],
        'word_counts': Counter(),
    }

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+", flags=re.UNICODE
    )

    laugh_pattern = re.compile(r'😂|😆|🤣|lol|lmao|haha|hehe|rofl', re.IGNORECASE)
    link_pattern = re.compile(r'https?://\S+', re.IGNORECASE)
    mention_pattern = re.compile(r'@\S+')

    prev_message = None
    conversation_gap = timedelta(hours=2)

    for msg in messages:
        if msg['is_system']:
            continue

        sender = normalize_name(msg['sender'])
        date_key = msg['date'].strftime('%Y-%m-%d')
        month_key = msg['date'].strftime('%Y-%m')
        hour = msg['date'].hour
        day_of_week = (msg['date'].weekday() + 1) % 7  # Sunday = 0

        person = stats['by_person'][sender]

        # Basic counts
        person['messages'] += 1
        stats['total_messages'] += 1
        person['active_days'].add(date_key)
        stats['active_days'].add(date_key)
        person['by_hour'][hour] += 1
        person['by_day'][day_of_week] += 1
        stats['by_hour'][hour] += 1
        stats['by_day_of_week'][day_of_week] += 1
        stats['by_month'][month_key] += 1
        stats['daily_counts'][date_key] += 1

        # Weekend messages (Sat & Sun)
        if day_of_week == 0 or day_of_week == 6:
            person['weekend_messages'] += 1

        # Late night (11pm - 4am)
        if hour >= 23 or hour < 4:
            person['late_night_messages'] += 1

        # Morning (5am - 9am)
        if 5 <= hour < 9:
            person['morning_messages'] += 1

        if person['first_message'] is None:
            person['first_message'] = msg['date']
        person['last_message'] = msg['date']

        if msg['is_media']:
            person['media'] += 1
            stats['total_media'] += 1
        else:
            content = msg['content']
            person['total_chars'] += len(content)
            stats['total_chars'] += len(content)
            person['message_lengths'].append(len(content))

            # Long/short messages
            if len(content) > 200:
                person['long_messages'] += 1
            elif len(content) < 10:
                person['short_messages'] += 1

            # Count emojis
            emojis = emoji_pattern.findall(content)
            person['emojis'] += len(emojis)

            # Count questions
            if '?' in content:
                person['questions'] += 1

            # Count exclamations
            if '!' in content:
                person['exclamations'] += 1

            # CAPS messages (enthusiasm)
            if len(content) > 5 and content.isupper():
                person['caps_messages'] += 1

            # Count laughs
            laughs = laugh_pattern.findall(content)
            person['laughs'] += len(laughs)

            # Count links
            links = link_pattern.findall(content)
            person['links'] += len(links)

            # Count mentions
            mentions = mention_pattern.findall(content)
            person['mentions'] += len(mentions)

            # Longest message
            if len(content) > stats['longest_message']['length']:
                stats['longest_message'] = {
                    'sender': sender,
                    'length': len(content),
                    'preview': content[:150] + ('...' if len(content) > 150 else '')
                }

            # Word counting (for common words)
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            stats['word_counts'].update(words)

        # Response time and conversation tracking
        if prev_message:
            time_diff = (msg['date'] - prev_message['date']).total_seconds() / 60

            # New conversation started (gap > 2 hours)
            if time_diff > 120:
                person['conversations_started'] += 1

            # Response time (if different sender and within 1 hour)
            if prev_message['sender'] != msg['sender'] and 0 < time_diff < 60:
                person['response_times'].append(time_diff)

            # Track who got replied to
            if prev_message['sender'] != msg['sender'] and time_diff < 30:
                prev_sender = normalize_name(prev_message['sender'])
                if prev_sender in stats['by_person']:
                    stats['by_person'][prev_sender]['replied_to_count'] += 1

        prev_message = msg

    # Calculate derived stats
    for sender, person in stats['by_person'].items():
        person['active_days_count'] = len(person['active_days'])
        person['active_days'] = list(person['active_days'])

        text_messages = person['messages'] - person['media']
        person['avg_chars'] = round(person['total_chars'] / text_messages) if text_messages > 0 else 0

        if person['response_times']:
            person['avg_response'] = round(sum(person['response_times']) / len(person['response_times']), 1)
            person['fastest_response'] = round(min(person['response_times']), 1)
        else:
            person['avg_response'] = None
            person['fastest_response'] = None

        person['peak_hour'] = person['by_hour'].index(max(person['by_hour']))
        person['peak_day'] = person['by_day'].index(max(person['by_day']))

        # Engagement rate (how often they get replied to)
        person['engagement_rate'] = round(person['replied_to_count'] / person['messages'] * 100, 1) if person['messages'] > 0 else 0

        # Media ratio
        person['media_ratio'] = round(person['media'] / person['messages'] * 100, 1) if person['messages'] > 0 else 0

        if person['first_message']:
            person['first_message'] = person['first_message'].isoformat()
        if person['last_message']:
            person['last_message'] = person['last_message'].isoformat()

        del person['response_times']
        del person['message_lengths']

    # Find most active day
    most_active_day = max(stats['daily_counts'].items(), key=lambda x: x[1])
    stats['most_active_day'] = {'date': most_active_day[0], 'count': most_active_day[1]}

    # Top words (excluding common words)
    common_words = {'that', 'this', 'with', 'have', 'will', 'your', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'would', 'there', 'could', 'other', 'into', 'more', 'some', 'them', 'then', 'like', 'just', 'know', 'what', 'about', 'when', 'make', 'time', 'very', 'after', 'come', 'made', 'find', 'here', 'want', 'going', 'back', 'really', 'yeah', 'okay', 'good', 'gonna', 'dont', 'didnt', 'cant', 'wont', 'isnt'}
    stats['top_words'] = [(word, count) for word, count in stats['word_counts'].most_common(50) if word not in common_words][:20]

    # Convert sets and defaultdicts
    stats['active_days'] = list(stats['active_days'])
    stats['total_days'] = len(stats['active_days'])
    stats['by_person'] = dict(stats['by_person'])
    stats['by_month'] = dict(stats['by_month'])
    stats['daily_counts'] = dict(stats['daily_counts'])
    del stats['word_counts']
    del stats['conversations']

    return stats

def generate_html(stats):
    """Generate the premium HTML dashboard with embedded stats"""

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OBRUTS WRAPPED 2025 - The Stats Edition</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #8b5cf6;
            --primary-light: #a78bfa;
            --secondary: #f472b6;
            --accent: #34d399;
            --accent-blue: #60a5fa;
            --gold: #fbbf24;
            --silver: #9ca3af;
            --bronze: #f59e0b;
            --bg-dark: #0a0a0f;
            --bg-card: rgba(26, 26, 46, 0.8);
            --bg-card-solid: #1a1a2e;
            --bg-gradient: linear-gradient(135deg, #0a0a0f 0%, #16162a 50%, #0a0a0f 100%);
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #f472b6 50%, #f97316 100%);
            --gradient-gold: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            --gradient-cool: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
            --gradient-warm: linear-gradient(135deg, #f97316 0%, #f472b6 100%);
            --gradient-nature: linear-gradient(135deg, #34d399 0%, #06b6d4 100%);
            --glass: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --glow-purple: 0 0 60px rgba(139, 92, 246, 0.4);
            --glow-pink: 0 0 60px rgba(244, 114, 182, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            line-height: 1.6;
        }

        /* Animated mesh gradient background */
        .mesh-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            background: var(--bg-dark);
        }

        .mesh-bg::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background:
                radial-gradient(ellipse 80% 50% at 20% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 80% 30%, rgba(244, 114, 182, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse 50% 50% at 50% 80%, rgba(52, 211, 153, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse 40% 60% at 90% 70%, rgba(251, 191, 36, 0.06) 0%, transparent 50%);
            animation: meshMove 20s ease-in-out infinite;
        }

        @keyframes meshMove {
            0%, 100% { transform: translate(0, 0) scale(1); }
            25% { transform: translate(-2%, 2%) scale(1.02); }
            50% { transform: translate(2%, -2%) scale(0.98); }
            75% { transform: translate(-1%, -1%) scale(1.01); }
        }

        /* Noise texture overlay */
        .noise {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.03;
            pointer-events: none;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        }

        /* Hero Header */
        .hero {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 40px 20px;
            position: relative;
        }

        .hero-content {
            max-width: 900px;
            z-index: 1;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            padding: 10px 20px;
            border-radius: 100px;
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }

        .hero-badge span {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 600;
        }

        .hero-title {
            font-family: 'Syne', sans-serif;
            font-size: clamp(4rem, 15vw, 10rem);
            font-weight: 800;
            line-height: 0.9;
            letter-spacing: -0.03em;
            margin-bottom: 20px;
        }

        .hero-title .line1 {
            display: block;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmer 3s ease-in-out infinite;
        }

        .hero-title .line2 {
            display: block;
            font-size: 0.4em;
            color: var(--text-secondary);
            font-weight: 500;
            letter-spacing: 0.3em;
            margin-top: 10px;
        }

        @keyframes shimmer {
            0%, 100% { filter: brightness(1) drop-shadow(0 0 30px rgba(139, 92, 246, 0.5)); }
            50% { filter: brightness(1.1) drop-shadow(0 0 50px rgba(244, 114, 182, 0.6)); }
        }

        .hero-subtitle {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(1rem, 3vw, 1.5rem);
            color: var(--text-secondary);
            margin-bottom: 50px;
            font-weight: 400;
        }

        .hero-stats {
            display: flex;
            justify-content: center;
            gap: 60px;
            flex-wrap: wrap;
            margin-bottom: 60px;
        }

        .hero-stat {
            text-align: center;
        }

        .hero-stat-number {
            font-family: 'Syne', sans-serif;
            font-size: clamp(2.5rem, 6vw, 4rem);
            font-weight: 700;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }

        .hero-stat-label {
            font-size: 0.9rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 8px;
        }

        .scroll-indicator {
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            color: var(--text-muted);
            font-size: 0.8rem;
            animation: bounce 2s infinite;
        }

        .scroll-indicator svg {
            width: 24px;
            height: 24px;
        }

        @keyframes bounce {
            0%, 100% { transform: translateX(-50%) translateY(0); }
            50% { transform: translateX(-50%) translateY(10px); }
        }

        /* Navigation */
        .nav {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(10, 10, 15, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--glass-border);
            padding: 0 20px;
        }

        .nav-inner {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: center;
            gap: 8px;
            padding: 15px 0;
            overflow-x: auto;
            scrollbar-width: none;
        }

        .nav-inner::-webkit-scrollbar {
            display: none;
        }

        .nav-btn {
            font-family: 'Space Grotesk', sans-serif;
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-secondary);
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            white-space: nowrap;
        }

        .nav-btn:hover {
            color: var(--text-primary);
            background: var(--glass);
        }

        .nav-btn.active {
            background: var(--gradient-primary);
            color: white;
            border-color: transparent;
        }

        /* Sections */
        .section {
            display: none;
            padding: 80px 20px;
            max-width: 1400px;
            margin: 0 auto;
            min-height: 80vh;
        }

        .section.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .section-header {
            text-align: center;
            margin-bottom: 60px;
        }

        .section-icon {
            font-size: 4rem;
            margin-bottom: 20px;
            display: block;
        }

        .section-title {
            font-family: 'Syne', sans-serif;
            font-size: clamp(2rem, 5vw, 3.5rem);
            font-weight: 700;
            margin-bottom: 15px;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .section-subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto;
        }

        /* Awards Grid */
        .awards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
        }

        .award-card {
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 32px;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            backdrop-filter: blur(10px);
        }

        .award-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--card-accent, var(--gradient-primary));
            opacity: 0.8;
        }

        .award-card::after {
            content: '';
            position: absolute;
            inset: 0;
            background: var(--card-accent, var(--gradient-primary));
            opacity: 0;
            transition: opacity 0.3s;
        }

        .award-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(139, 92, 246, 0.3);
            box-shadow: var(--glow-purple);
        }

        .award-card:hover::after {
            opacity: 0.05;
        }

        .award-content {
            position: relative;
            z-index: 1;
        }

        .award-emoji {
            font-size: 3.5rem;
            margin-bottom: 16px;
            display: block;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }

        .award-title {
            font-family: 'Syne', sans-serif;
            font-size: 1.1rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .award-winner {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 12px;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .award-stat {
            font-size: 0.95rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .award-stat-highlight {
            color: var(--accent);
            font-weight: 600;
        }

        /* Tooltip for awards */
        .award-tooltip {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(10px);
            background: var(--bg-card-solid);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px;
            width: 280px;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 100;
            pointer-events: none;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }

        .award-card:hover .award-tooltip {
            opacity: 1;
            visibility: visible;
            transform: translateX(-50%) translateY(-10px);
        }

        .tooltip-title {
            font-family: 'Syne', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 10px;
            color: var(--text-primary);
        }

        .tooltip-content {
            font-size: 0.85rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        .tooltip-stat {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
        }

        .tooltip-stat-label {
            color: var(--text-muted);
        }

        .tooltip-stat-value {
            color: var(--accent);
            font-weight: 600;
        }

        /* Leaderboard */
        .leaderboard-container {
            max-width: 900px;
            margin: 0 auto;
        }

        .leaderboard-item {
            display: flex;
            align-items: center;
            gap: 20px;
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 24px 32px;
            margin-bottom: 16px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .leaderboard-item:hover {
            transform: translateX(8px);
            border-color: rgba(139, 92, 246, 0.3);
            box-shadow: var(--glow-purple);
        }

        .leaderboard-item.rank-1 {
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, var(--bg-card) 100%);
            border-color: rgba(251, 191, 36, 0.3);
        }

        .leaderboard-item.rank-2 {
            background: linear-gradient(135deg, rgba(156, 163, 175, 0.1) 0%, var(--bg-card) 100%);
            border-color: rgba(156, 163, 175, 0.3);
        }

        .leaderboard-item.rank-3 {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, var(--bg-card) 100%);
            border-color: rgba(245, 158, 11, 0.3);
        }

        .rank-badge {
            font-family: 'Syne', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            width: 60px;
            text-align: center;
        }

        .rank-badge.gold { color: var(--gold); }
        .rank-badge.silver { color: var(--silver); }
        .rank-badge.bronze { color: var(--bronze); }

        .player-avatar {
            width: 56px;
            height: 56px;
            border-radius: 16px;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 1.4rem;
            flex-shrink: 0;
        }

        .player-info {
            flex: 1;
        }

        .player-name {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 1.2rem;
            margin-bottom: 4px;
        }

        .player-meta {
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        .player-score {
            font-family: 'Syne', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--accent);
        }

        /* Activity Charts */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }

        .chart-card {
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 32px;
            backdrop-filter: blur(10px);
        }

        .chart-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 30px;
        }

        .chart-icon {
            font-size: 1.8rem;
        }

        .chart-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
        }

        .bar-chart {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            height: 180px;
            gap: 4px;
            padding: 0 4px;
        }

        .bar-group {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100%;
            position: relative;
        }

        .bar {
            width: 100%;
            max-width: 40px;
            border-radius: 8px 8px 4px 4px;
            transition: all 0.3s ease;
            position: relative;
            min-height: 4px;
        }

        .bar:hover {
            filter: brightness(1.3);
            transform: scaleY(1.05);
        }

        .bar-tooltip {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-card-solid);
            border: 1px solid var(--glass-border);
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent);
            opacity: 0;
            transition: opacity 0.2s;
            white-space: nowrap;
            z-index: 10;
        }

        .bar:hover .bar-tooltip {
            opacity: 1;
        }

        .bar-label {
            color: var(--text-muted);
            font-size: 0.7rem;
            margin-top: 10px;
            text-align: center;
        }

        /* Heatmap */
        .heatmap-container {
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 32px;
            backdrop-filter: blur(10px);
        }

        .heatmap {
            display: grid;
            grid-template-columns: auto repeat(24, 1fr);
            gap: 3px;
            margin-top: 20px;
        }

        .heatmap-row {
            display: contents;
        }

        .heatmap-day-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            padding-right: 10px;
        }

        .heatmap-cell {
            aspect-ratio: 1;
            border-radius: 4px;
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
        }

        .heatmap-cell:hover {
            transform: scale(1.4);
            z-index: 10;
            box-shadow: 0 0 20px currentColor;
        }

        .heatmap-hour-labels {
            display: grid;
            grid-template-columns: auto repeat(24, 1fr);
            gap: 3px;
            margin-top: 8px;
        }

        .heatmap-hour-label {
            font-size: 0.65rem;
            color: var(--text-muted);
            text-align: center;
        }

        /* Fun Facts */
        .facts-container {
            max-width: 900px;
            margin: 0 auto;
        }

        .fact-card {
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 32px;
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
            gap: 24px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .fact-card:hover {
            transform: translateX(8px);
            border-color: rgba(139, 92, 246, 0.3);
        }

        .fact-icon {
            font-size: 3rem;
            flex-shrink: 0;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--glass);
            border-radius: 20px;
        }

        .fact-content {
            flex: 1;
        }

        .fact-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .fact-text {
            color: var(--text-secondary);
            font-size: 1rem;
            line-height: 1.7;
        }

        .fact-highlight {
            color: var(--accent);
            font-weight: 600;
        }

        /* Everyone Stats */
        .everyone-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 24px;
        }

        .person-card {
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 28px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .person-card:hover {
            transform: translateY(-5px);
            border-color: rgba(139, 92, 246, 0.3);
            box-shadow: var(--glow-purple);
        }

        .person-header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
        }

        .person-avatar-lg {
            width: 64px;
            height: 64px;
            border-radius: 18px;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Syne', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
        }

        .person-name-section h3 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .person-name-section p {
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        .person-stats-mini {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }

        .mini-stat {
            text-align: center;
            padding: 16px 8px;
            background: var(--glass);
            border-radius: 14px;
        }

        .mini-stat-value {
            font-family: 'Syne', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 4px;
        }

        .mini-stat-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 80px 20px;
            border-top: 1px solid var(--glass-border);
            margin-top: 80px;
        }

        .footer-logo {
            font-family: 'Syne', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 16px;
        }

        .footer-text {
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .hero-stats {
                gap: 30px;
            }

            .charts-grid {
                grid-template-columns: 1fr;
            }

            .awards-grid {
                grid-template-columns: 1fr;
            }

            .everyone-grid {
                grid-template-columns: 1fr;
            }

            .person-stats-mini {
                grid-template-columns: repeat(2, 1fr);
            }

            .heatmap {
                display: none;
            }

            .leaderboard-item {
                padding: 16px 20px;
                gap: 12px;
            }

            .fact-card {
                flex-direction: column;
                text-align: center;
            }

            .fact-icon {
                margin: 0 auto;
            }
        }

        /* Animations */
        .fade-up {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .fade-up.visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* Stagger children animations */
        .stagger-children > * {
            opacity: 0;
            transform: translateY(20px);
            animation: staggerFade 0.5s ease forwards;
        }

        @keyframes staggerFade {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .stagger-children > *:nth-child(1) { animation-delay: 0.1s; }
        .stagger-children > *:nth-child(2) { animation-delay: 0.15s; }
        .stagger-children > *:nth-child(3) { animation-delay: 0.2s; }
        .stagger-children > *:nth-child(4) { animation-delay: 0.25s; }
        .stagger-children > *:nth-child(5) { animation-delay: 0.3s; }
        .stagger-children > *:nth-child(6) { animation-delay: 0.35s; }
        .stagger-children > *:nth-child(7) { animation-delay: 0.4s; }
        .stagger-children > *:nth-child(8) { animation-delay: 0.45s; }
        .stagger-children > *:nth-child(9) { animation-delay: 0.5s; }
        .stagger-children > *:nth-child(10) { animation-delay: 0.55s; }
        .stagger-children > *:nth-child(11) { animation-delay: 0.6s; }
        .stagger-children > *:nth-child(12) { animation-delay: 0.65s; }
        .stagger-children > *:nth-child(13) { animation-delay: 0.7s; }
        .stagger-children > *:nth-child(14) { animation-delay: 0.75s; }
        .stagger-children > *:nth-child(15) { animation-delay: 0.8s; }
        .stagger-children > *:nth-child(16) { animation-delay: 0.85s; }
        .stagger-children > *:nth-child(17) { animation-delay: 0.9s; }

        /* Color variants for awards */
        .award-card[data-color="purple"] { --card-accent: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%); }
        .award-card[data-color="pink"] { --card-accent: linear-gradient(135deg, #ec4899 0%, #f472b6 100%); }
        .award-card[data-color="blue"] { --card-accent: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); }
        .award-card[data-color="cyan"] { --card-accent: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%); }
        .award-card[data-color="green"] { --card-accent: linear-gradient(135deg, #10b981 0%, #34d399 100%); }
        .award-card[data-color="yellow"] { --card-accent: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%); }
        .award-card[data-color="orange"] { --card-accent: linear-gradient(135deg, #f97316 0%, #fb923c 100%); }
        .award-card[data-color="red"] { --card-accent: linear-gradient(135deg, #ef4444 0%, #f87171 100%); }
    </style>
</head>
<body>
    <div class="mesh-bg"></div>
    <div class="noise"></div>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <div class="hero-badge">
                <span>PART OF THE OBRUTS AWARDS</span>
            </div>
            <h1 class="hero-title">
                <span class="line1">WRAPPED</span>
                <span class="line2">THE STATS EDITION</span>
            </h1>
            <p class="hero-subtitle">A deep dive into our group chat chaos from the past year</p>

            <div class="hero-stats" id="heroStats"></div>
        </div>

        <div class="scroll-indicator">
            <span>Scroll to explore</span>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
        </div>
    </section>

    <!-- Navigation -->
    <nav class="nav">
        <div class="nav-inner">
            <button class="nav-btn active" data-section="awards">The Awards</button>
            <button class="nav-btn" data-section="leaderboards">Leaderboards</button>
            <button class="nav-btn" data-section="activity">Activity</button>
            <button class="nav-btn" data-section="facts">Fun Facts</button>
            <button class="nav-btn" data-section="everyone">Everyone</button>
        </div>
    </nav>

    <!-- Awards Section -->
    <section class="section active" id="awards">
        <div class="section-header">
            <span class="section-icon">🏆</span>
            <h2 class="section-title">The Awards</h2>
            <p class="section-subtitle">Everyone gets their moment to shine. Hover over each award to see the full story.</p>
        </div>
        <div class="awards-grid stagger-children" id="awardsGrid"></div>
    </section>

    <!-- Leaderboards Section -->
    <section class="section" id="leaderboards">
        <div class="section-header">
            <span class="section-icon">📊</span>
            <h2 class="section-title">Leaderboards</h2>
            <p class="section-subtitle">Who dominated the chat this year?</p>
        </div>

        <h3 style="font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; margin-bottom: 24px; text-align: center; color: var(--text-secondary);">💬 Most Messages</h3>
        <div class="leaderboard-container stagger-children" id="messageLeaderboard"></div>

        <h3 style="font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; margin: 60px 0 24px; text-align: center; color: var(--text-secondary);">⚡ Fastest Responders</h3>
        <div class="leaderboard-container stagger-children" id="responseLeaderboard"></div>

        <h3 style="font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; margin: 60px 0 24px; text-align: center; color: var(--text-secondary);">📸 Media Sharers</h3>
        <div class="leaderboard-container stagger-children" id="mediaLeaderboard"></div>
    </section>

    <!-- Activity Section -->
    <section class="section" id="activity">
        <div class="section-header">
            <span class="section-icon">📈</span>
            <h2 class="section-title">Activity Patterns</h2>
            <p class="section-subtitle">When and how we communicate</p>
        </div>

        <div class="charts-grid">
            <div class="chart-card fade-up">
                <div class="chart-header">
                    <span class="chart-icon">📅</span>
                    <span class="chart-title">Messages by Month</span>
                </div>
                <div class="bar-chart" id="monthlyChart"></div>
            </div>

            <div class="chart-card fade-up">
                <div class="chart-header">
                    <span class="chart-icon">📆</span>
                    <span class="chart-title">Day of Week</span>
                </div>
                <div class="bar-chart" id="dayChart"></div>
            </div>
        </div>

        <div class="heatmap-container fade-up" style="margin-top: 30px;">
            <div class="chart-header">
                <span class="chart-icon">🔥</span>
                <span class="chart-title">Activity Heatmap - When We're Most Active</span>
            </div>
            <div class="heatmap" id="heatmap"></div>
            <div class="heatmap-hour-labels" id="heatmapLabels"></div>
        </div>

        <div class="chart-card fade-up" style="margin-top: 30px;">
            <div class="chart-header">
                <span class="chart-icon">⏰</span>
                <span class="chart-title">Hourly Activity</span>
            </div>
            <div class="bar-chart" id="hourlyChart"></div>
        </div>
    </section>

    <!-- Fun Facts Section -->
    <section class="section" id="facts">
        <div class="section-header">
            <span class="section-icon">✨</span>
            <h2 class="section-title">Fun Facts</h2>
            <p class="section-subtitle">The numbers that tell our story</p>
        </div>
        <div class="facts-container stagger-children" id="factsContainer"></div>
    </section>

    <!-- Everyone Section -->
    <section class="section" id="everyone">
        <div class="section-header">
            <span class="section-icon">👥</span>
            <h2 class="section-title">Everyone's Stats</h2>
            <p class="section-subtitle">Individual breakdowns for each member</p>
        </div>
        <div class="everyone-grid stagger-children" id="everyoneGrid"></div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-logo">THE OBRUTS</div>
        <p class="footer-text">Stats Edition - November 2024 to November 2025</p>
        <p class="footer-text" style="margin-top: 8px; opacity: 0.6;">Made with love for the squad</p>
    </footer>

    <script>
        const stats = STATS_PLACEHOLDER;

        // Utility functions
        const formatNumber = (num) => num.toLocaleString();
        const getInitial = (name) => name.charAt(0).toUpperCase();

        // Color palette for awards
        const colors = ['purple', 'pink', 'blue', 'cyan', 'green', 'yellow', 'orange', 'red'];

        // Render hero stats
        function renderHeroStats() {
            const container = document.getElementById('heroStats');
            const avgPerDay = Math.round(stats.total_messages / stats.total_days);

            container.innerHTML = `
                <div class="hero-stat">
                    <div class="hero-stat-number">${formatNumber(stats.total_messages)}</div>
                    <div class="hero-stat-label">Messages</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-number">${formatNumber(stats.total_media)}</div>
                    <div class="hero-stat-label">Media Shared</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-number">${stats.total_days}</div>
                    <div class="hero-stat-label">Days Active</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-number">${avgPerDay}</div>
                    <div class="hero-stat-label">Avg Per Day</div>
                </div>
            `;
        }

        // Render awards - one unique award per person
        function renderAwards() {
            const container = document.getElementById('awardsGrid');
            const people = Object.entries(stats.by_person);

            // Calculate all possible awards with explanations
            const awardCandidates = [];

            // Sort people by different metrics to assign unique awards
            const byMessages = [...people].sort((a, b) => b[1].messages - a[1].messages);
            const byMedia = [...people].sort((a, b) => b[1].media - a[1].media);
            const byEmojis = [...people].sort((a, b) => b[1].emojis - a[1].emojis);
            const byLaughs = [...people].sort((a, b) => b[1].laughs - a[1].laughs);
            const byQuestions = [...people].sort((a, b) => b[1].questions - a[1].questions);
            const byAvgChars = [...people].sort((a, b) => b[1].avg_chars - a[1].avg_chars);
            const byResponse = [...people].filter(([,d]) => d.avg_response).sort((a, b) => a[1].avg_response - b[1].avg_response);
            const bySlowResponse = [...people].filter(([,d]) => d.avg_response).sort((a, b) => b[1].avg_response - a[1].avg_response);
            const byActiveDays = [...people].sort((a, b) => b[1].active_days_count - a[1].active_days_count);
            const byConversations = [...people].sort((a, b) => b[1].conversations_started - a[1].conversations_started);
            const byEngagement = [...people].sort((a, b) => b[1].engagement_rate - a[1].engagement_rate);
            const byWeekend = [...people].sort((a, b) => b[1].weekend_messages - a[1].weekend_messages);
            const byLateNight = [...people].sort((a, b) => b[1].late_night_messages - a[1].late_night_messages);
            const byMorning = [...people].sort((a, b) => b[1].morning_messages - a[1].morning_messages);
            const byLinks = [...people].sort((a, b) => b[1].links - a[1].links);
            const byMentions = [...people].sort((a, b) => b[1].mentions - a[1].mentions);
            const byExclamations = [...people].sort((a, b) => b[1].exclamations - a[1].exclamations);
            const byLongMessages = [...people].sort((a, b) => b[1].long_messages - a[1].long_messages);
            const byShortMessages = [...people].sort((a, b) => b[1].short_messages - a[1].short_messages);
            const byMediaRatio = [...people].sort((a, b) => b[1].media_ratio - a[1].media_ratio);

            // Track assigned people
            const assigned = new Set();

            // Define all possible awards in order of priority
            const allAwards = [
                {
                    list: byMessages,
                    emoji: '👑',
                    title: 'Chat Royalty',
                    getStat: (d) => `${formatNumber(d.messages)} messages sent`,
                    getExplanation: (name, d) => `${name} absolutely dominated the chat this year with ${formatNumber(d.messages)} messages! That's ${Math.round(d.messages / stats.total_messages * 100)}% of all messages. True dedication to the group!`,
                    getExtra: (d) => ({ label: 'Share of chat', value: `${Math.round(d.messages / stats.total_messages * 100)}%` })
                },
                {
                    list: byMedia,
                    emoji: '📸',
                    title: 'Media Mogul',
                    getStat: (d) => `${formatNumber(d.media)} photos/videos shared`,
                    getExplanation: (name, d) => `${name} kept the group entertained with ${formatNumber(d.media)} media files! From memes to memories, they're our visual storyteller.`,
                    getExtra: (d) => ({ label: 'Media ratio', value: `${d.media_ratio}%` })
                },
                {
                    list: byLaughs,
                    emoji: '🤣',
                    title: 'Chief Laughing Officer',
                    getStat: (d) => `${formatNumber(d.laughs)} laughs shared`,
                    getExplanation: (name, d) => `${name} brought the joy with ${formatNumber(d.laughs)} laughing emojis and "lol"s! They either find everything hilarious or are just really supportive.`,
                    getExtra: (d) => ({ label: 'Laugh per message', value: `${(d.laughs / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: byResponse,
                    emoji: '⚡',
                    title: 'Speed Demon',
                    getStat: (d) => `${d.avg_response} min avg response`,
                    getExplanation: (name, d) => `${name} is QUICK! With an average response time of ${d.avg_response} minutes, they never leave anyone hanging. Phone always in hand!`,
                    getExtra: (d) => ({ label: 'Fastest response', value: `${d.fastest_response}m` })
                },
                {
                    list: byConversations,
                    emoji: '🎤',
                    title: 'Conversation Starter',
                    getStat: (d) => `${formatNumber(d.conversations_started)} convos initiated`,
                    getExplanation: (name, d) => `${name} is the spark plug! They kicked off ${formatNumber(d.conversations_started)} conversations this year. When the chat goes quiet, they bring it back to life.`,
                    getExtra: (d) => ({ label: 'Initiative rate', value: `${(d.conversations_started / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: byEmojis,
                    emoji: '🎭',
                    title: 'Emoji Enthusiast',
                    getStat: (d) => `${formatNumber(d.emojis)} emojis used`,
                    getExplanation: (name, d) => `${name} speaks fluent emoji with ${formatNumber(d.emojis)} used this year! Why use words when a 🔥 says it all?`,
                    getExtra: (d) => ({ label: 'Per message', value: `${(d.emojis / d.messages).toFixed(1)}` })
                },
                {
                    list: byActiveDays,
                    emoji: '📅',
                    title: 'Mr. Consistent',
                    getStat: (d) => `Active ${d.active_days_count} days`,
                    getExplanation: (name, d) => `${name} showed up ${d.active_days_count} out of ${stats.total_days} days! That's ${Math.round(d.active_days_count / stats.total_days * 100)}% attendance. Reliable as ever!`,
                    getExtra: (d) => ({ label: 'Attendance', value: `${Math.round(d.active_days_count / stats.total_days * 100)}%` })
                },
                {
                    list: byLateNight,
                    emoji: '🌙',
                    title: 'Night Owl',
                    getStat: (d) => `${formatNumber(d.late_night_messages)} late night msgs`,
                    getExplanation: (name, d) => `${name} doesn't sleep! With ${formatNumber(d.late_night_messages)} messages sent between 11PM-4AM, they're living that nocturnal life.`,
                    getExtra: (d) => ({ label: 'Night ratio', value: `${(d.late_night_messages / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: byMorning,
                    emoji: '🌅',
                    title: 'Early Bird',
                    getStat: (d) => `${formatNumber(d.morning_messages)} morning msgs`,
                    getExplanation: (name, d) => `${name} is up with the sun! ${formatNumber(d.morning_messages)} messages sent between 5AM-9AM. They're either productive or just can't sleep.`,
                    getExtra: (d) => ({ label: 'Morning ratio', value: `${(d.morning_messages / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: byEngagement,
                    emoji: '🧲',
                    title: 'The Influencer',
                    getStat: (d) => `${d.engagement_rate}% engagement rate`,
                    getExplanation: (name, d) => `When ${name} talks, people listen and respond! ${d.engagement_rate}% of their messages get direct replies. They're basically the group's main character.`,
                    getExtra: (d) => ({ label: 'Replies received', value: formatNumber(d.replied_to_count) })
                },
                {
                    list: byQuestions,
                    emoji: '🤔',
                    title: 'The Curious One',
                    getStat: (d) => `${formatNumber(d.questions)} questions asked`,
                    getExplanation: (name, d) => `${name} keeps the conversation going with ${formatNumber(d.questions)} questions! Curious minds want to know everything.`,
                    getExtra: (d) => ({ label: 'Question rate', value: `${(d.questions / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: byAvgChars,
                    emoji: '📖',
                    title: 'The Novelist',
                    getStat: (d) => `${d.avg_chars} chars per message`,
                    getExplanation: (name, d) => `${name} doesn't do short messages! Averaging ${d.avg_chars} characters per message, they write essays while we write tweets.`,
                    getExtra: (d) => ({ label: 'Long messages', value: formatNumber(d.long_messages) })
                },
                {
                    list: byWeekend,
                    emoji: '🎉',
                    title: 'Weekend Warrior',
                    getStat: (d) => `${formatNumber(d.weekend_messages)} weekend msgs`,
                    getExplanation: (name, d) => `${name} comes alive on weekends with ${formatNumber(d.weekend_messages)} messages on Saturdays and Sundays! Work week? Never heard of it.`,
                    getExtra: (d) => ({ label: 'Weekend ratio', value: `${(d.weekend_messages / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: byLinks,
                    emoji: '🔗',
                    title: 'Link Lord',
                    getStat: (d) => `${formatNumber(d.links)} links shared`,
                    getExplanation: (name, d) => `${name} is our source! They've shared ${formatNumber(d.links)} links this year. News, memes, YouTube - they've got it all.`,
                    getExtra: (d) => ({ label: 'Per 100 msgs', value: (d.links / d.messages * 100).toFixed(1) })
                },
                {
                    list: byMentions,
                    emoji: '📢',
                    title: 'The Tagger',
                    getStat: (d) => `${formatNumber(d.mentions)} @mentions`,
                    getExplanation: (name, d) => `${name} makes sure nobody misses out with ${formatNumber(d.mentions)} @mentions! They're bringing everyone into the conversation.`,
                    getExtra: (d) => ({ label: 'Mention rate', value: `${(d.mentions / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: byExclamations,
                    emoji: '❗',
                    title: 'The Exclaimer',
                    getStat: (d) => `${formatNumber(d.exclamations)} exclamations!`,
                    getExplanation: (name, d) => `${name} brings the ENERGY! ${formatNumber(d.exclamations)} messages with exclamation marks! They're always hyped about something!`,
                    getExtra: (d) => ({ label: 'Hype level', value: `${(d.exclamations / d.messages * 100).toFixed(1)}%` })
                },
                {
                    list: bySlowResponse,
                    emoji: '🐢',
                    title: 'The Philosopher',
                    getStat: (d) => `${d.avg_response} min to respond`,
                    getExplanation: (name, d) => `${name} takes their time to craft the perfect response. ${d.avg_response} minutes average - they're thinking deeply or just busy!`,
                    getExtra: (d) => ({ label: 'Response time', value: `${d.avg_response}m` })
                },
                {
                    list: byMediaRatio,
                    emoji: '🖼️',
                    title: 'Visual Communicator',
                    getStat: (d) => `${d.media_ratio}% media ratio`,
                    getExplanation: (name, d) => `${name} lets pictures do the talking! ${d.media_ratio}% of their messages are media. A picture is worth a thousand words.`,
                    getExtra: (d) => ({ label: 'Total media', value: formatNumber(d.media) })
                },
                {
                    list: byShortMessages,
                    emoji: '💨',
                    title: 'Short & Sweet',
                    getStat: (d) => `${formatNumber(d.short_messages)} quick msgs`,
                    getExplanation: (name, d) => `${name} keeps it brief! ${formatNumber(d.short_messages)} messages under 10 characters. "lol", "ok", "nice" - efficiency is key!`,
                    getExtra: (d) => ({ label: 'Brevity rate', value: `${(d.short_messages / d.messages * 100).toFixed(1)}%` })
                },
            ];

            // Assign awards ensuring each person gets exactly one
            const awards = [];
            let colorIndex = 0;

            for (const award of allAwards) {
                if (assigned.size >= people.length) break;

                for (const [name, data] of award.list) {
                    if (!assigned.has(name)) {
                        assigned.add(name);
                        awards.push({
                            ...award,
                            name,
                            data,
                            color: colors[colorIndex % colors.length]
                        });
                        colorIndex++;
                        break;
                    }
                }
            }

            container.innerHTML = awards.map(award => `
                <div class="award-card" data-color="${award.color}">
                    <div class="award-content">
                        <span class="award-emoji">${award.emoji}</span>
                        <div class="award-title">${award.title}</div>
                        <div class="award-winner">${award.name}</div>
                        <div class="award-stat">${award.getStat(award.data)}</div>
                    </div>
                    <div class="award-tooltip">
                        <div class="tooltip-title">Why ${award.name}?</div>
                        <div class="tooltip-content">${award.getExplanation(award.name, award.data)}</div>
                        <div class="tooltip-stat">
                            <span class="tooltip-stat-label">${award.getExtra(award.data).label}</span>
                            <span class="tooltip-stat-value">${award.getExtra(award.data).value}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        // Render leaderboards
        function renderLeaderboards() {
            const medals = ['🥇', '🥈', '🥉'];
            const people = Object.entries(stats.by_person);

            // Messages leaderboard
            const byMessages = [...people].sort((a, b) => b[1].messages - a[1].messages);
            document.getElementById('messageLeaderboard').innerHTML = byMessages.map(([name, data], i) => `
                <div class="leaderboard-item ${i < 3 ? 'rank-' + (i + 1) : ''}">
                    <div class="rank-badge ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : ''}">${medals[i] || '#' + (i + 1)}</div>
                    <div class="player-avatar">${getInitial(name)}</div>
                    <div class="player-info">
                        <div class="player-name">${name}</div>
                        <div class="player-meta">${Math.round(data.messages / stats.total_messages * 100)}% of all messages</div>
                    </div>
                    <div class="player-score">${formatNumber(data.messages)}</div>
                </div>
            `).join('');

            // Response time leaderboard
            const byResponse = [...people].filter(([,d]) => d.avg_response).sort((a, b) => a[1].avg_response - b[1].avg_response);
            document.getElementById('responseLeaderboard').innerHTML = byResponse.slice(0, 10).map(([name, data], i) => `
                <div class="leaderboard-item ${i < 3 ? 'rank-' + (i + 1) : ''}">
                    <div class="rank-badge ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : ''}">${medals[i] || '#' + (i + 1)}</div>
                    <div class="player-avatar">${getInitial(name)}</div>
                    <div class="player-info">
                        <div class="player-name">${name}</div>
                        <div class="player-meta">Lightning fast replies</div>
                    </div>
                    <div class="player-score">${data.avg_response}m</div>
                </div>
            `).join('');

            // Media leaderboard
            const byMedia = [...people].sort((a, b) => b[1].media - a[1].media);
            document.getElementById('mediaLeaderboard').innerHTML = byMedia.slice(0, 10).map(([name, data], i) => `
                <div class="leaderboard-item ${i < 3 ? 'rank-' + (i + 1) : ''}">
                    <div class="rank-badge ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : ''}">${medals[i] || '#' + (i + 1)}</div>
                    <div class="player-avatar">${getInitial(name)}</div>
                    <div class="player-info">
                        <div class="player-name">${name}</div>
                        <div class="player-meta">${stats.total_media > 0 ? Math.round(data.media / stats.total_media * 100) : 0}% of all media</div>
                    </div>
                    <div class="player-score">${formatNumber(data.media)}</div>
                </div>
            `).join('');
        }

        // Render charts
        function renderCharts() {
            // Monthly chart
            const months = Object.entries(stats.by_month).sort((a, b) => a[0].localeCompare(b[0]));
            const maxMonth = Math.max(...months.map(m => m[1]));
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

            document.getElementById('monthlyChart').innerHTML = months.map(([month, count]) => {
                const [year, m] = month.split('-');
                const height = Math.max(5, count / maxMonth * 100);
                const hue = 260 + (parseInt(m) - 1) * 10;
                return `
                    <div class="bar-group">
                        <div class="bar" style="height: ${height}%; background: linear-gradient(180deg, hsl(${hue}, 80%, 60%) 0%, hsl(${hue + 20}, 70%, 50%) 100%);">
                            <div class="bar-tooltip">${formatNumber(count)}</div>
                        </div>
                        <div class="bar-label">${monthNames[parseInt(m) - 1]}</div>
                    </div>
                `;
            }).join('');

            // Day of week chart
            const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const maxDay = Math.max(...stats.by_day_of_week);
            const dayColors = ['#06b6d4', '#8b5cf6', '#8b5cf6', '#8b5cf6', '#8b5cf6', '#8b5cf6', '#06b6d4'];

            document.getElementById('dayChart').innerHTML = stats.by_day_of_week.map((count, i) => {
                const height = Math.max(5, count / maxDay * 100);
                return `
                    <div class="bar-group">
                        <div class="bar" style="height: ${height}%; background: linear-gradient(180deg, ${dayColors[i]} 0%, ${dayColors[i]}99 100%);">
                            <div class="bar-tooltip">${formatNumber(count)}</div>
                        </div>
                        <div class="bar-label">${dayNames[i]}</div>
                    </div>
                `;
            }).join('');

            // Hourly chart
            const maxHour = Math.max(...stats.by_hour);
            document.getElementById('hourlyChart').innerHTML = stats.by_hour.map((count, h) => {
                const height = Math.max(5, count / maxHour * 100);
                const isNight = h >= 22 || h < 6;
                const isMorning = h >= 6 && h < 12;
                const color = isNight ? '#3b82f6' : isMorning ? '#f59e0b' : h < 18 ? '#8b5cf6' : '#f472b6';
                const label = h === 0 ? '12a' : h < 12 ? `${h}a` : h === 12 ? '12p' : `${h-12}p`;
                return `
                    <div class="bar-group">
                        <div class="bar" style="height: ${height}%; background: linear-gradient(180deg, ${color} 0%, ${color}99 100%);">
                            <div class="bar-tooltip">${formatNumber(count)}</div>
                        </div>
                        <div class="bar-label">${label}</div>
                    </div>
                `;
            }).join('');

            // Heatmap (day x hour)
            const heatmapData = [];
            const people = Object.entries(stats.by_person);
            for (let day = 0; day < 7; day++) {
                for (let hour = 0; hour < 24; hour++) {
                    let total = 0;
                    for (const [, data] of people) {
                        total += data.by_hour[hour] * (data.by_day[day] / Math.max(1, ...data.by_day));
                    }
                    heatmapData.push({ day, hour, value: total });
                }
            }
            const maxHeat = Math.max(...heatmapData.map(d => d.value));

            const heatmapDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            let heatmapHTML = '';
            for (let day = 0; day < 7; day++) {
                heatmapHTML += `<div class="heatmap-row"><div class="heatmap-day-label">${heatmapDays[day]}</div>`;
                for (let hour = 0; hour < 24; hour++) {
                    const value = heatmapData[day * 24 + hour].value;
                    const intensity = value / maxHeat;
                    const color = `rgba(139, 92, 246, ${0.1 + intensity * 0.9})`;
                    heatmapHTML += `<div class="heatmap-cell" style="background: ${color};" title="${heatmapDays[day]} ${hour}:00"></div>`;
                }
                heatmapHTML += '</div>';
            }
            document.getElementById('heatmap').innerHTML = heatmapHTML;

            // Heatmap hour labels
            let labelsHTML = '<div></div>';
            for (let h = 0; h < 24; h++) {
                if (h % 3 === 0) {
                    const label = h === 0 ? '12a' : h < 12 ? `${h}a` : h === 12 ? '12p' : `${h-12}p`;
                    labelsHTML += `<div class="heatmap-hour-label">${label}</div>`;
                } else {
                    labelsHTML += '<div></div>';
                }
            }
            document.getElementById('heatmapLabels').innerHTML = labelsHTML;
        }

        // Render fun facts
        function renderFacts() {
            const container = document.getElementById('factsContainer');
            const people = Object.entries(stats.by_person);

            const peakHour = stats.by_hour.indexOf(Math.max(...stats.by_hour));
            const peakHourLabel = peakHour === 0 ? '12 AM' : peakHour < 12 ? `${peakHour} AM` : peakHour === 12 ? '12 PM' : `${peakHour - 12} PM`;

            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const peakDay = stats.by_day_of_week.indexOf(Math.max(...stats.by_day_of_week));

            const activeDate = new Date(stats.most_active_day.date);
            const activeDateStr = activeDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

            const totalWords = Math.round(stats.total_chars / 5);
            const totalEmojis = people.reduce((sum, [,d]) => sum + d.emojis, 0);
            const totalLaughs = people.reduce((sum, [,d]) => sum + d.laughs, 0);
            const totalQuestions = people.reduce((sum, [,d]) => sum + d.questions, 0);
            const totalLinks = people.reduce((sum, [,d]) => sum + d.links, 0);
            const totalConvos = people.reduce((sum, [,d]) => sum + d.conversations_started, 0);

            // Books equivalent (avg book is 75,000 words)
            const booksEquiv = (totalWords / 75000).toFixed(1);

            // Most used words
            const topWords = stats.top_words.slice(0, 5).map(([w]) => w).join(', ');

            // Night owls percentage
            const lateNightMsgs = people.reduce((sum, [,d]) => sum + d.late_night_messages, 0);
            const nightPercent = (lateNightMsgs / stats.total_messages * 100).toFixed(1);

            const facts = [
                { icon: '📚', title: 'Novel Writers', text: `We've typed <span class="fact-highlight">${formatNumber(stats.total_chars)}</span> characters - that's approximately <span class="fact-highlight">${formatNumber(totalWords)}</span> words. Enough to fill <span class="fact-highlight">${booksEquiv} books</span>!` },
                { icon: '⏰', title: 'Prime Time', text: `The chat is on fire at <span class="fact-highlight">${peakHourLabel}</span>. That's when the real tea gets spilled and the best conversations happen!` },
                { icon: '📅', title: 'Favorite Day', text: `<span class="fact-highlight">${dayNames[peakDay]}</span> is our most active day with <span class="fact-highlight">${formatNumber(stats.by_day_of_week[peakDay])}</span> messages. We know how to ${peakDay === 0 || peakDay === 6 ? 'party on weekends' : 'get through the week'}!` },
                { icon: '🔥', title: 'Record Breaker', text: `<span class="fact-highlight">${activeDateStr}</span> was absolutely WILD with <span class="fact-highlight">${formatNumber(stats.most_active_day.count)}</span> messages. What happened that day?!` },
                { icon: '😂', title: 'Laughing Together', text: `We shared <span class="fact-highlight">${formatNumber(totalLaughs)}</span> laughs (LOLs, 😂, HAHAs) this year. That's <span class="fact-highlight">${(totalLaughs / stats.total_days).toFixed(1)}</span> laughs per day!` },
                { icon: '🎭', title: 'Emoji Game', text: `<span class="fact-highlight">${formatNumber(totalEmojis)}</span> emojis were used! We speak fluent emoji at this point. 🔥💀😭` },
                { icon: '❓', title: 'Curious Minds', text: `<span class="fact-highlight">${formatNumber(totalQuestions)}</span> questions were asked. We're either really curious or really confused most of the time!` },
                { icon: '🔗', title: 'Link Droppers', text: `<span class="fact-highlight">${formatNumber(totalLinks)}</span> links were shared. News, memes, YouTube videos - our group is basically a curated feed!` },
                { icon: '🎬', title: 'Visual Vibes', text: `<span class="fact-highlight">${Math.round(stats.total_media / stats.total_messages * 100)}%</span> of messages were media (photos, videos, stickers, GIFs). A picture is worth a thousand words!` },
                { icon: '🌙', title: 'Night Owls', text: `<span class="fact-highlight">${nightPercent}%</span> of messages were sent between 11PM-4AM. Some of us clearly don't believe in sleep!` },
                { icon: '💬', title: 'Conversations', text: `<span class="fact-highlight">${formatNumber(totalConvos)}</span> new conversations were started over the year. That's <span class="fact-highlight">${(totalConvos / stats.total_days).toFixed(1)}</span> topics per day!` },
                { icon: '📊', title: 'Daily Dose', text: `On average, we send <span class="fact-highlight">${Math.round(stats.total_messages / stats.total_days)}</span> messages per day. That's a lot of opinions and hot takes!` },
                { icon: '🏆', title: 'Participation Trophy', text: `<span class="fact-highlight">${people.length}</span> people were active this year across <span class="fact-highlight">${stats.total_days}</span> days. The squad stays connected!` },
                { icon: '📝', title: 'The Longest Message', text: `Someone wrote a <span class="fact-highlight">${formatNumber(stats.longest_message.length)}</span> character message! "${stats.longest_message.preview.slice(0, 80)}..."` },
                { icon: '🔤', title: 'Word Trends', text: `Our most used words this year: <span class="fact-highlight">${topWords}</span>. This is basically our group's vocabulary!` },
            ];

            container.innerHTML = facts.map(fact => `
                <div class="fact-card">
                    <div class="fact-icon">${fact.icon}</div>
                    <div class="fact-content">
                        <div class="fact-title">${fact.title}</div>
                        <div class="fact-text">${fact.text}</div>
                    </div>
                </div>
            `).join('');
        }

        // Render everyone
        function renderEveryone() {
            const container = document.getElementById('everyoneGrid');
            const people = Object.entries(stats.by_person).sort((a, b) => b[1].messages - a[1].messages);

            container.innerHTML = people.map(([name, data]) => {
                const peakHour = data.peak_hour;
                const peakLabel = peakHour === 0 ? '12AM' : peakHour < 12 ? `${peakHour}AM` : peakHour === 12 ? '12PM' : `${peakHour-12}PM`;
                const pct = Math.round(data.messages / stats.total_messages * 100);

                return `
                    <div class="person-card">
                        <div class="person-header">
                            <div class="person-avatar-lg">${getInitial(name)}</div>
                            <div class="person-name-section">
                                <h3>${name}</h3>
                                <p>${pct}% of total messages</p>
                            </div>
                        </div>
                        <div class="person-stats-mini">
                            <div class="mini-stat">
                                <div class="mini-stat-value">${formatNumber(data.messages)}</div>
                                <div class="mini-stat-label">Messages</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${formatNumber(data.media)}</div>
                                <div class="mini-stat-label">Media</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.avg_response ? data.avg_response + 'm' : 'N/A'}</div>
                                <div class="mini-stat-label">Response</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.active_days_count}</div>
                                <div class="mini-stat-label">Days</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${formatNumber(data.emojis)}</div>
                                <div class="mini-stat-label">Emojis</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${formatNumber(data.laughs)}</div>
                                <div class="mini-stat-label">Laughs</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${peakLabel}</div>
                                <div class="mini-stat-label">Peak</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.avg_chars}</div>
                                <div class="mini-stat-label">Avg Len</div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Navigation
        function setupNav() {
            const btns = document.querySelectorAll('.nav-btn');
            const sections = document.querySelectorAll('.section');

            btns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const target = btn.dataset.section;

                    btns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');

                    sections.forEach(s => s.classList.remove('active'));
                    document.getElementById(target).classList.add('active');

                    // Scroll to top of section smoothly
                    window.scrollTo({ top: document.querySelector('.nav').offsetTop, behavior: 'smooth' });
                });
            });
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            renderHeroStats();
            renderAwards();
            renderLeaderboards();
            renderCharts();
            renderFacts();
            renderEveryone();
            setupNav();

            // Intersection observer for animations
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                    }
                });
            }, { threshold: 0.1 });

            document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
        });
    </script>
</body>
</html>'''

    return html_template

def main():
    print("THE OBRUTS 2025 - Chat Stats Generator V2")
    print("=" * 50)

    print("Parsing chat file...")
    messages = parse_chat('/Users/abanobnashat/Desktop/OBRUTS 25/Stats/_chat.txt')
    print(f"Total messages parsed: {len(messages)}")

    print("Filtering to last 365 days...")
    filtered = filter_last_365_days(messages)
    print(f"Messages in last 365 days: {len(filtered)}")

    print("Calculating stats...")
    stats = calculate_stats(filtered)

    print(f"\nSummary:")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Total media: {stats['total_media']}")
    print(f"  Active members: {len(stats['by_person'])}")
    print(f"  Days active: {stats['total_days']}")
    print(f"  Most active day: {stats['most_active_day']['date']} ({stats['most_active_day']['count']} messages)")

    print("\nGenerating premium HTML dashboard...")
    html_content = generate_html(stats)

    stats_json = json.dumps(stats, indent=2, default=str)
    html_content = html_content.replace('STATS_PLACEHOLDER', stats_json)

    output_path = '/Users/abanobnashat/Desktop/OBRUTS 25/Stats/obruts_wrapped_2025.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nPremium dashboard generated: {output_path}")
    print("\nOpen the HTML file in your browser!")

if __name__ == '__main__':
    main()
