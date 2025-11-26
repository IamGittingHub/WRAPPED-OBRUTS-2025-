#!/usr/bin/env python3
"""
THE OBRUTS 2025 - Chat Stats Generator V3
Premium Edition with Dramatic Reveal Leaderboards
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
    cutoff = datetime(2024, 11, 25)
    end_date = datetime(2025, 11, 25, 23, 59, 59)
    return [m for m in messages if cutoff <= m['date'] <= end_date]

def normalize_name(name):
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
            'long_messages': 0,
            'short_messages': 0,
            'first_message': None,
            'last_message': None,
            'conversations_started': 0,
            'replied_to_count': 0,
            'weekend_messages': 0,
            'late_night_messages': 0,
            'morning_messages': 0,
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

    for msg in messages:
        if msg['is_system']:
            continue

        sender = normalize_name(msg['sender'])
        date_key = msg['date'].strftime('%Y-%m-%d')
        month_key = msg['date'].strftime('%Y-%m')
        hour = msg['date'].hour
        day_of_week = (msg['date'].weekday() + 1) % 7

        person = stats['by_person'][sender]

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

        if day_of_week == 0 or day_of_week == 6:
            person['weekend_messages'] += 1

        if hour >= 23 or hour < 4:
            person['late_night_messages'] += 1

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

            if len(content) > 200:
                person['long_messages'] += 1
            elif len(content) < 10:
                person['short_messages'] += 1

            emojis = emoji_pattern.findall(content)
            person['emojis'] += len(emojis)

            if '?' in content:
                person['questions'] += 1

            if '!' in content:
                person['exclamations'] += 1

            if len(content) > 5 and content.isupper():
                person['caps_messages'] += 1

            laughs = laugh_pattern.findall(content)
            person['laughs'] += len(laughs)

            links = link_pattern.findall(content)
            person['links'] += len(links)

            mentions = mention_pattern.findall(content)
            person['mentions'] += len(mentions)

            if len(content) > stats['longest_message']['length']:
                stats['longest_message'] = {
                    'sender': sender,
                    'length': len(content),
                    'preview': content[:150] + ('...' if len(content) > 150 else '')
                }

            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            stats['word_counts'].update(words)

        if prev_message:
            time_diff = (msg['date'] - prev_message['date']).total_seconds() / 60

            if time_diff > 120:
                person['conversations_started'] += 1

            if prev_message['sender'] != msg['sender'] and 0 < time_diff < 60:
                person['response_times'].append(time_diff)

            if prev_message['sender'] != msg['sender'] and time_diff < 30:
                prev_sender = normalize_name(prev_message['sender'])
                if prev_sender in stats['by_person']:
                    stats['by_person'][prev_sender]['replied_to_count'] += 1

        prev_message = msg

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
        person['engagement_rate'] = round(person['replied_to_count'] / person['messages'] * 100, 1) if person['messages'] > 0 else 0
        person['media_ratio'] = round(person['media'] / person['messages'] * 100, 1) if person['messages'] > 0 else 0

        if person['first_message']:
            person['first_message'] = person['first_message'].isoformat()
        if person['last_message']:
            person['last_message'] = person['last_message'].isoformat()

        del person['response_times']
        del person['message_lengths']

    most_active_day = max(stats['daily_counts'].items(), key=lambda x: x[1])
    stats['most_active_day'] = {'date': most_active_day[0], 'count': most_active_day[1]}

    common_words = {'that', 'this', 'with', 'have', 'will', 'your', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'would', 'there', 'could', 'other', 'into', 'more', 'some', 'them', 'then', 'like', 'just', 'know', 'what', 'about', 'when', 'make', 'time', 'very', 'after', 'come', 'made', 'find', 'here', 'want', 'going', 'back', 'really', 'yeah', 'okay', 'good', 'gonna', 'dont', 'didnt', 'cant', 'wont', 'isnt'}
    stats['top_words'] = [(word, count) for word, count in stats['word_counts'].most_common(50) if word not in common_words][:20]

    stats['active_days'] = list(stats['active_days'])
    stats['total_days'] = len(stats['active_days'])
    stats['by_person'] = dict(stats['by_person'])
    stats['by_month'] = dict(stats['by_month'])
    stats['daily_counts'] = dict(stats['daily_counts'])
    del stats['word_counts']
    del stats['conversations']

    return stats

def generate_html(stats):
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
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #f472b6 50%, #f97316 100%);
            --gradient-gold: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            --gradient-cool: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
            --gradient-warm: linear-gradient(135deg, #f97316 0%, #f472b6 100%);
            --glass: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --glow-purple: 0 0 60px rgba(139, 92, 246, 0.4);
            --glow-gold: 0 0 80px rgba(251, 191, 36, 0.5);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            line-height: 1.6;
        }

        .mesh-bg {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: -2;
            background: var(--bg-dark);
        }

        .mesh-bg::before {
            content: '';
            position: absolute;
            inset: 0;
            background:
                radial-gradient(ellipse 80% 50% at 20% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 80% 30%, rgba(244, 114, 182, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse 50% 50% at 50% 80%, rgba(52, 211, 153, 0.08) 0%, transparent 50%);
            animation: meshMove 20s ease-in-out infinite;
        }

        @keyframes meshMove {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(2%, -2%) scale(1.02); }
        }

        .noise {
            position: fixed;
            inset: 0;
            z-index: -1;
            opacity: 0.03;
            pointer-events: none;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        }

        /* Hero */
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

        .hero-content { max-width: 900px; z-index: 1; }

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
        }

        .hero-stats {
            display: flex;
            justify-content: center;
            gap: 60px;
            flex-wrap: wrap;
            margin-bottom: 60px;
        }

        .hero-stat { text-align: center; }

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

        .scroll-indicator svg { width: 24px; height: 24px; }

        @keyframes bounce {
            0%, 100% { transform: translateX(-50%) translateY(0); }
            50% { transform: translateX(-50%) translateY(10px); }
        }

        /* Navigation */
        .nav {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(10, 10, 15, 0.85);
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

        .nav-inner::-webkit-scrollbar { display: none; }

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

        /* ============================================
           DRAMATIC REVEAL LEADERBOARD STYLES
           ============================================ */

        .reveal-container {
            max-width: 800px;
            margin: 0 auto 80px;
        }

        .reveal-header {
            text-align: center;
            margin-bottom: 40px;
        }

        .reveal-category {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.2em;
            margin-bottom: 10px;
        }

        .reveal-title {
            font-family: 'Syne', sans-serif;
            font-size: clamp(1.8rem, 4vw, 2.5rem);
            font-weight: 700;
            color: var(--text-primary);
        }

        .reveal-title span {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* The dramatic reveal card */
        .reveal-stage {
            position: relative;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 40px;
        }

        .reveal-card {
            position: absolute;
            width: 100%;
            max-width: 500px;
            background: var(--bg-card);
            border: 2px solid var(--glass-border);
            border-radius: 32px;
            padding: 50px 40px;
            text-align: center;
            opacity: 0;
            transform: scale(0.8) translateY(50px);
            transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
            backdrop-filter: blur(20px);
        }

        .reveal-card.active {
            opacity: 1;
            transform: scale(1) translateY(0);
            z-index: 10;
        }

        .reveal-card.exit-left {
            opacity: 0;
            transform: scale(0.8) translateX(-100px);
        }

        .reveal-card.exit-right {
            opacity: 0;
            transform: scale(0.8) translateX(100px);
        }

        .reveal-card.rank-1 {
            border-color: var(--gold);
            box-shadow: var(--glow-gold);
        }

        .reveal-card.rank-2 {
            border-color: var(--silver);
            box-shadow: 0 0 60px rgba(156, 163, 175, 0.3);
        }

        .reveal-card.rank-3 {
            border-color: var(--bronze);
            box-shadow: 0 0 60px rgba(245, 158, 11, 0.3);
        }

        .reveal-rank {
            font-family: 'Syne', sans-serif;
            font-size: 5rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 20px;
        }

        .reveal-rank.gold { color: var(--gold); }
        .reveal-rank.silver { color: var(--silver); }
        .reveal-rank.bronze { color: var(--bronze); }

        .reveal-rank-label {
            font-size: 1rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 30px;
        }

        .reveal-avatar {
            width: 100px;
            height: 100px;
            border-radius: 28px;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Syne', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0 auto 20px;
            box-shadow: 0 10px 40px rgba(139, 92, 246, 0.3);
        }

        .reveal-name {
            font-family: 'Syne', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .reveal-stat {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.3rem;
            color: var(--accent);
            font-weight: 600;
        }

        .reveal-stat-label {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-top: 5px;
        }

        /* Navigation dots and buttons */
        .reveal-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            margin-top: 30px;
        }

        .reveal-btn {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            font-size: 1.5rem;
        }

        .reveal-btn:hover {
            background: var(--primary);
            border-color: var(--primary);
            transform: scale(1.1);
        }

        .reveal-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
            transform: none;
        }

        .reveal-dots {
            display: flex;
            gap: 12px;
        }

        .reveal-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--glass-border);
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .reveal-dot.active {
            background: var(--primary);
            transform: scale(1.3);
        }

        .reveal-dot.gold.active { background: var(--gold); }
        .reveal-dot.silver.active { background: var(--silver); }
        .reveal-dot.bronze.active { background: var(--bronze); }

        /* Show full list button */
        .show-full-btn {
            display: block;
            margin: 40px auto 0;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 16px 40px;
            border-radius: 100px;
            cursor: pointer;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .show-full-btn:hover {
            background: var(--gradient-primary);
            border-color: transparent;
            transform: translateY(-2px);
        }

        /* Full leaderboard (initially hidden) */
        .full-leaderboard {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.6s ease, opacity 0.4s ease;
            opacity: 0;
        }

        .full-leaderboard.expanded {
            max-height: 2000px;
            opacity: 1;
            margin-top: 40px;
        }

        .full-list-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.2rem;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 24px;
        }

        .leaderboard-item {
            display: flex;
            align-items: center;
            gap: 20px;
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 20px 28px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .leaderboard-item:hover {
            transform: translateX(8px);
            border-color: rgba(139, 92, 246, 0.3);
        }

        .leaderboard-item.rank-1 {
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, var(--bg-card) 100%);
            border-color: rgba(251, 191, 36, 0.4);
        }

        .leaderboard-item.rank-2 {
            background: linear-gradient(135deg, rgba(156, 163, 175, 0.15) 0%, var(--bg-card) 100%);
            border-color: rgba(156, 163, 175, 0.4);
        }

        .leaderboard-item.rank-3 {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, var(--bg-card) 100%);
            border-color: rgba(245, 158, 11, 0.4);
        }

        .rank-badge {
            font-family: 'Syne', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            width: 50px;
            text-align: center;
        }

        .rank-badge.gold { color: var(--gold); }
        .rank-badge.silver { color: var(--silver); }
        .rank-badge.bronze { color: var(--bronze); }

        .player-avatar {
            width: 52px;
            height: 52px;
            border-radius: 16px;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 1.3rem;
            flex-shrink: 0;
        }

        .player-info { flex: 1; }

        .player-name {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 2px;
        }

        .player-meta {
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        .player-score {
            font-family: 'Syne', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }

        /* Confetti burst for #1 */
        .confetti-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 100;
        }

        .confetti {
            position: absolute;
            width: 10px;
            height: 10px;
            opacity: 0;
        }

        .confetti.burst {
            animation: confettiBurst 1s ease-out forwards;
        }

        @keyframes confettiBurst {
            0% {
                opacity: 1;
                transform: translate(0, 0) rotate(0deg) scale(1);
            }
            100% {
                opacity: 0;
                transform: translate(var(--tx), var(--ty)) rotate(720deg) scale(0);
            }
        }

        /* ============================================
           AWARDS STYLES
           ============================================ */

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

        .award-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(139, 92, 246, 0.3);
            box-shadow: var(--glow-purple);
        }

        .award-content { position: relative; z-index: 1; }

        .award-emoji {
            font-size: 3.5rem;
            margin-bottom: 16px;
            display: block;
        }

        .award-title {
            font-family: 'Syne', sans-serif;
            font-size: 1rem;
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
        }

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

        .tooltip-stat-label { color: var(--text-muted); }
        .tooltip-stat-value { color: var(--accent); font-weight: 600; }

        .award-card[data-color="purple"] { --card-accent: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%); }
        .award-card[data-color="pink"] { --card-accent: linear-gradient(135deg, #ec4899 0%, #f472b6 100%); }
        .award-card[data-color="blue"] { --card-accent: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); }
        .award-card[data-color="cyan"] { --card-accent: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%); }
        .award-card[data-color="green"] { --card-accent: linear-gradient(135deg, #10b981 0%, #34d399 100%); }
        .award-card[data-color="yellow"] { --card-accent: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%); }
        .award-card[data-color="orange"] { --card-accent: linear-gradient(135deg, #f97316 0%, #fb923c 100%); }
        .award-card[data-color="red"] { --card-accent: linear-gradient(135deg, #ef4444 0%, #f87171 100%); }

        /* ============================================
           ACTIVITY & CHARTS
           ============================================ */

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

        .chart-icon { font-size: 1.8rem; }

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

        .bar:hover .bar-tooltip { opacity: 1; }

        .bar-label {
            color: var(--text-muted);
            font-size: 0.7rem;
            margin-top: 10px;
            text-align: center;
        }

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

        .heatmap-row { display: contents; }

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
        }

        .heatmap-cell:hover {
            transform: scale(1.4);
            z-index: 10;
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

        /* ============================================
           FUN FACTS
           ============================================ */

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

        .fact-content { flex: 1; }

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

        /* ============================================
           EVERYONE STATS
           ============================================ */

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
            .hero-stats { gap: 30px; }
            .charts-grid { grid-template-columns: 1fr; }
            .awards-grid { grid-template-columns: 1fr; }
            .everyone-grid { grid-template-columns: 1fr; }
            .person-stats-mini { grid-template-columns: repeat(2, 1fr); }
            .heatmap { display: none; }
            .reveal-card { padding: 40px 24px; }
            .reveal-name { font-size: 2rem; }
            .fact-card { flex-direction: column; text-align: center; }
            .fact-icon { margin: 0 auto; }
        }

        /* Animations */
        .stagger-children > * {
            opacity: 0;
            transform: translateY(20px);
            animation: staggerFade 0.5s ease forwards;
        }

        @keyframes staggerFade {
            to { opacity: 1; transform: translateY(0); }
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

    <!-- Navigation - Leaderboards FIRST -->
    <nav class="nav">
        <div class="nav-inner">
            <button class="nav-btn active" data-section="leaderboards">Leaderboards</button>
            <button class="nav-btn" data-section="awards">The Awards</button>
            <button class="nav-btn" data-section="activity">Activity</button>
            <button class="nav-btn" data-section="facts">Fun Facts</button>
            <button class="nav-btn" data-section="everyone">Everyone</button>
        </div>
    </nav>

    <!-- LEADERBOARDS SECTION - NOW FIRST with Dramatic Reveals -->
    <section class="section active" id="leaderboards">
        <div class="section-header">
            <span class="section-icon">🏆</span>
            <h2 class="section-title">The Leaderboards</h2>
            <p class="section-subtitle">Who dominated the chat this year? Click through to reveal the top 3!</p>
        </div>

        <!-- MESSAGES LEADERBOARD -->
        <div class="reveal-container" id="messagesReveal">
            <div class="reveal-header">
                <div class="reveal-category">Category</div>
                <div class="reveal-title">Most <span>Messages</span> Sent</div>
            </div>
            <div class="reveal-stage" id="messagesStage">
                <!-- Cards will be injected here -->
            </div>
            <div class="reveal-controls">
                <button class="reveal-btn" id="messagesPrev">←</button>
                <div class="reveal-dots" id="messagesDots"></div>
                <button class="reveal-btn" id="messagesNext">→</button>
            </div>
            <button class="show-full-btn" id="messagesShowFull">Show Full Rankings</button>
            <div class="full-leaderboard" id="messagesFullList">
                <div class="full-list-title">Complete Rankings</div>
                <div id="messagesLeaderboard"></div>
            </div>
        </div>

        <!-- RESPONSE TIME LEADERBOARD -->
        <div class="reveal-container" id="responseReveal">
            <div class="reveal-header">
                <div class="reveal-category">Category</div>
                <div class="reveal-title">Fastest <span>Responders</span></div>
            </div>
            <div class="reveal-stage" id="responseStage">
                <!-- Cards will be injected here -->
            </div>
            <div class="reveal-controls">
                <button class="reveal-btn" id="responsePrev">←</button>
                <div class="reveal-dots" id="responseDots"></div>
                <button class="reveal-btn" id="responseNext">→</button>
            </div>
            <button class="show-full-btn" id="responseShowFull">Show Full Rankings</button>
            <div class="full-leaderboard" id="responseFullList">
                <div class="full-list-title">Complete Rankings</div>
                <div id="responseLeaderboard"></div>
            </div>
        </div>

        <!-- MEDIA LEADERBOARD -->
        <div class="reveal-container" id="mediaReveal">
            <div class="reveal-header">
                <div class="reveal-category">Category</div>
                <div class="reveal-title">Top <span>Media</span> Sharers</div>
            </div>
            <div class="reveal-stage" id="mediaStage">
                <!-- Cards will be injected here -->
            </div>
            <div class="reveal-controls">
                <button class="reveal-btn" id="mediaPrev">←</button>
                <div class="reveal-dots" id="mediaDots"></div>
                <button class="reveal-btn" id="mediaNext">→</button>
            </div>
            <button class="show-full-btn" id="mediaShowFull">Show Full Rankings</button>
            <div class="full-leaderboard" id="mediaFullList">
                <div class="full-list-title">Complete Rankings</div>
                <div id="mediaLeaderboard"></div>
            </div>
        </div>
    </section>

    <!-- Awards Section -->
    <section class="section" id="awards">
        <div class="section-header">
            <span class="section-icon">🎖️</span>
            <h2 class="section-title">The Awards</h2>
            <p class="section-subtitle">Everyone gets their moment to shine. Hover over each award to see the full story.</p>
        </div>
        <div class="awards-grid stagger-children" id="awardsGrid"></div>
    </section>

    <!-- Activity Section -->
    <section class="section" id="activity">
        <div class="section-header">
            <span class="section-icon">📈</span>
            <h2 class="section-title">Activity Patterns</h2>
            <p class="section-subtitle">When and how we communicate</p>
        </div>
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-icon">📅</span>
                    <span class="chart-title">Messages by Month</span>
                </div>
                <div class="bar-chart" id="monthlyChart"></div>
            </div>
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-icon">📆</span>
                    <span class="chart-title">Day of Week</span>
                </div>
                <div class="bar-chart" id="dayChart"></div>
            </div>
        </div>
        <div class="heatmap-container" style="margin-top: 30px;">
            <div class="chart-header">
                <span class="chart-icon">🔥</span>
                <span class="chart-title">Activity Heatmap - When We're Most Active</span>
            </div>
            <div class="heatmap" id="heatmap"></div>
            <div class="heatmap-hour-labels" id="heatmapLabels"></div>
        </div>
        <div class="chart-card" style="margin-top: 30px;">
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

        const formatNumber = (num) => num.toLocaleString();
        const getInitial = (name) => name.charAt(0).toUpperCase();
        const colors = ['purple', 'pink', 'blue', 'cyan', 'green', 'yellow', 'orange', 'red'];

        // ============================================
        // DRAMATIC REVEAL LEADERBOARD CLASS
        // ============================================
        class RevealLeaderboard {
            constructor(options) {
                this.data = options.data;
                this.stageId = options.stageId;
                this.dotsId = options.dotsId;
                this.prevId = options.prevId;
                this.nextId = options.nextId;
                this.showFullId = options.showFullId;
                this.fullListId = options.fullListId;
                this.leaderboardId = options.leaderboardId;
                this.statFormatter = options.statFormatter;
                this.statLabel = options.statLabel;
                this.metaFormatter = options.metaFormatter || (() => '');

                this.currentIndex = 2; // Start at #3 (index 2)
                this.revealed = [false, false, false];

                this.init();
            }

            init() {
                this.renderCards();
                this.renderDots();
                this.renderFullList();
                this.bindEvents();
                this.showCard(this.currentIndex);
            }

            renderCards() {
                const stage = document.getElementById(this.stageId);
                const top3 = this.data.slice(0, 3);
                const rankClasses = ['rank-1', 'rank-2', 'rank-3'];
                const rankColors = ['gold', 'silver', 'bronze'];
                const medals = ['🥇', '🥈', '🥉'];

                stage.innerHTML = top3.map(([name, data], i) => `
                    <div class="reveal-card ${rankClasses[i]}" data-index="${i}">
                        <div class="reveal-rank ${rankColors[i]}">${medals[i]}</div>
                        <div class="reveal-rank-label">${i === 0 ? '1st Place' : i === 1 ? '2nd Place' : '3rd Place'}</div>
                        <div class="reveal-avatar">${getInitial(name)}</div>
                        <div class="reveal-name">${name}</div>
                        <div class="reveal-stat">${this.statFormatter(data)}</div>
                        <div class="reveal-stat-label">${this.statLabel}</div>
                        <div class="confetti-container" id="confetti-${this.stageId}-${i}"></div>
                    </div>
                `).join('');
            }

            renderDots() {
                const dots = document.getElementById(this.dotsId);
                const dotClasses = ['bronze', 'silver', 'gold'];
                // Dots in order: #3, #2, #1 (bronze, silver, gold)
                dots.innerHTML = [2, 1, 0].map((i, idx) => `
                    <div class="reveal-dot ${dotClasses[idx]}" data-index="${i}"></div>
                `).join('');
            }

            renderFullList() {
                const container = document.getElementById(this.leaderboardId);
                const medals = ['🥇', '🥈', '🥉'];

                container.innerHTML = this.data.map(([name, data], i) => `
                    <div class="leaderboard-item ${i < 3 ? 'rank-' + (i + 1) : ''}">
                        <div class="rank-badge ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : ''}">${medals[i] || '#' + (i + 1)}</div>
                        <div class="player-avatar">${getInitial(name)}</div>
                        <div class="player-info">
                            <div class="player-name">${name}</div>
                            <div class="player-meta">${this.metaFormatter(data)}</div>
                        </div>
                        <div class="player-score">${this.statFormatter(data)}</div>
                    </div>
                `).join('');
            }

            bindEvents() {
                document.getElementById(this.prevId).addEventListener('click', () => this.prev());
                document.getElementById(this.nextId).addEventListener('click', () => this.next());
                document.getElementById(this.showFullId).addEventListener('click', () => this.toggleFullList());

                document.querySelectorAll(`#${this.dotsId} .reveal-dot`).forEach(dot => {
                    dot.addEventListener('click', () => {
                        const index = parseInt(dot.dataset.index);
                        this.goTo(index);
                    });
                });
            }

            showCard(index) {
                const cards = document.querySelectorAll(`#${this.stageId} .reveal-card`);
                const dots = document.querySelectorAll(`#${this.dotsId} .reveal-dot`);

                cards.forEach((card, i) => {
                    card.classList.remove('active', 'exit-left', 'exit-right');
                    if (i === index) {
                        card.classList.add('active');
                        // Trigger confetti for #1
                        if (index === 0 && !this.revealed[0]) {
                            this.revealed[0] = true;
                            setTimeout(() => this.burstConfetti(index), 300);
                        }
                    }
                });

                dots.forEach((dot, i) => {
                    // Dots are in reverse order: [2, 1, 0] maps to indexes [0, 1, 2]
                    const dotIndex = [2, 1, 0][i];
                    dot.classList.toggle('active', dotIndex === index);
                });

                // Update button states
                document.getElementById(this.prevId).disabled = index === 2;
                document.getElementById(this.nextId).disabled = index === 0;
            }

            burstConfetti(index) {
                const container = document.getElementById(`confetti-${this.stageId}-${index}`);
                const colors = ['#fbbf24', '#f472b6', '#8b5cf6', '#34d399', '#f97316', '#60a5fa'];

                for (let i = 0; i < 30; i++) {
                    const confetti = document.createElement('div');
                    confetti.className = 'confetti';
                    confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
                    confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
                    confetti.style.width = (Math.random() * 10 + 5) + 'px';
                    confetti.style.height = (Math.random() * 10 + 5) + 'px';

                    const angle = (Math.random() * 360) * (Math.PI / 180);
                    const distance = Math.random() * 150 + 50;
                    confetti.style.setProperty('--tx', Math.cos(angle) * distance + 'px');
                    confetti.style.setProperty('--ty', Math.sin(angle) * distance + 'px');

                    container.appendChild(confetti);
                    setTimeout(() => confetti.classList.add('burst'), 10);
                    setTimeout(() => confetti.remove(), 1100);
                }
            }

            prev() {
                if (this.currentIndex < 2) {
                    this.currentIndex++;
                    this.showCard(this.currentIndex);
                }
            }

            next() {
                if (this.currentIndex > 0) {
                    this.currentIndex--;
                    this.showCard(this.currentIndex);
                }
            }

            goTo(index) {
                this.currentIndex = index;
                this.showCard(index);
            }

            toggleFullList() {
                const fullList = document.getElementById(this.fullListId);
                const btn = document.getElementById(this.showFullId);
                fullList.classList.toggle('expanded');
                btn.textContent = fullList.classList.contains('expanded') ? 'Hide Full Rankings' : 'Show Full Rankings';
            }
        }

        // ============================================
        // RENDER FUNCTIONS
        // ============================================

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

        function initLeaderboards() {
            const people = Object.entries(stats.by_person);

            // Messages leaderboard
            const byMessages = [...people].sort((a, b) => b[1].messages - a[1].messages);
            new RevealLeaderboard({
                data: byMessages,
                stageId: 'messagesStage',
                dotsId: 'messagesDots',
                prevId: 'messagesPrev',
                nextId: 'messagesNext',
                showFullId: 'messagesShowFull',
                fullListId: 'messagesFullList',
                leaderboardId: 'messagesLeaderboard',
                statFormatter: (d) => formatNumber(d.messages),
                statLabel: 'messages sent',
                metaFormatter: (d) => `${Math.round(d.messages / stats.total_messages * 100)}% of all messages`
            });

            // Response time leaderboard
            const byResponse = [...people].filter(([,d]) => d.avg_response).sort((a, b) => a[1].avg_response - b[1].avg_response);
            new RevealLeaderboard({
                data: byResponse,
                stageId: 'responseStage',
                dotsId: 'responseDots',
                prevId: 'responsePrev',
                nextId: 'responseNext',
                showFullId: 'responseShowFull',
                fullListId: 'responseFullList',
                leaderboardId: 'responseLeaderboard',
                statFormatter: (d) => d.avg_response + 'm',
                statLabel: 'average response time',
                metaFormatter: (d) => `Fastest: ${d.fastest_response}m`
            });

            // Media leaderboard
            const byMedia = [...people].sort((a, b) => b[1].media - a[1].media);
            new RevealLeaderboard({
                data: byMedia,
                stageId: 'mediaStage',
                dotsId: 'mediaDots',
                prevId: 'mediaPrev',
                nextId: 'mediaNext',
                showFullId: 'mediaShowFull',
                fullListId: 'mediaFullList',
                leaderboardId: 'mediaLeaderboard',
                statFormatter: (d) => formatNumber(d.media),
                statLabel: 'media shared',
                metaFormatter: (d) => `${d.media_ratio}% of their messages`
            });
        }

        function renderAwards() {
            const container = document.getElementById('awardsGrid');
            const people = Object.entries(stats.by_person);

            const assigned = new Set();

            const allAwards = [
                { list: [...people].sort((a, b) => b[1].messages - a[1].messages), emoji: '👑', title: 'Chat Royalty', getStat: (d) => `${formatNumber(d.messages)} messages`, getExplanation: (name, d) => `${name} dominated with ${formatNumber(d.messages)} messages - ${Math.round(d.messages / stats.total_messages * 100)}% of all chat!`, getExtra: (d) => ({ label: 'Share', value: `${Math.round(d.messages / stats.total_messages * 100)}%` }) },
                { list: [...people].sort((a, b) => b[1].media - a[1].media), emoji: '📸', title: 'Media Mogul', getStat: (d) => `${formatNumber(d.media)} media shared`, getExplanation: (name, d) => `${name} kept us entertained with ${formatNumber(d.media)} photos, videos, and memes!`, getExtra: (d) => ({ label: 'Media ratio', value: `${d.media_ratio}%` }) },
                { list: [...people].sort((a, b) => b[1].laughs - a[1].laughs), emoji: '🤣', title: 'Chief Laughing Officer', getStat: (d) => `${formatNumber(d.laughs)} laughs`, getExplanation: (name, d) => `${name} brought the joy with ${formatNumber(d.laughs)} laughs!`, getExtra: (d) => ({ label: 'Laugh rate', value: `${(d.laughs / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].filter(([,d]) => d.avg_response).sort((a, b) => a[1].avg_response - b[1].avg_response), emoji: '⚡', title: 'Speed Demon', getStat: (d) => `${d.avg_response}m avg response`, getExplanation: (name, d) => `${name} is QUICK with ${d.avg_response}min average response!`, getExtra: (d) => ({ label: 'Fastest', value: `${d.fastest_response}m` }) },
                { list: [...people].sort((a, b) => b[1].conversations_started - a[1].conversations_started), emoji: '🎤', title: 'Conversation Starter', getStat: (d) => `${formatNumber(d.conversations_started)} convos`, getExplanation: (name, d) => `${name} kicked off ${formatNumber(d.conversations_started)} conversations!`, getExtra: (d) => ({ label: 'Initiative', value: `${(d.conversations_started / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].sort((a, b) => b[1].emojis - a[1].emojis), emoji: '🎭', title: 'Emoji Enthusiast', getStat: (d) => `${formatNumber(d.emojis)} emojis`, getExplanation: (name, d) => `${name} speaks fluent emoji with ${formatNumber(d.emojis)} used!`, getExtra: (d) => ({ label: 'Per message', value: `${(d.emojis / d.messages).toFixed(1)}` }) },
                { list: [...people].sort((a, b) => b[1].active_days_count - a[1].active_days_count), emoji: '📅', title: 'Mr. Consistent', getStat: (d) => `${d.active_days_count} days active`, getExplanation: (name, d) => `${name} showed up ${d.active_days_count} days - ${Math.round(d.active_days_count / stats.total_days * 100)}% attendance!`, getExtra: (d) => ({ label: 'Attendance', value: `${Math.round(d.active_days_count / stats.total_days * 100)}%` }) },
                { list: [...people].sort((a, b) => b[1].late_night_messages - a[1].late_night_messages), emoji: '🌙', title: 'Night Owl', getStat: (d) => `${formatNumber(d.late_night_messages)} late msgs`, getExplanation: (name, d) => `${name} doesn't sleep! ${formatNumber(d.late_night_messages)} messages between 11PM-4AM.`, getExtra: (d) => ({ label: 'Night ratio', value: `${(d.late_night_messages / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].sort((a, b) => b[1].morning_messages - a[1].morning_messages), emoji: '🌅', title: 'Early Bird', getStat: (d) => `${formatNumber(d.morning_messages)} morning msgs`, getExplanation: (name, d) => `${name} is up early! ${formatNumber(d.morning_messages)} messages between 5-9AM.`, getExtra: (d) => ({ label: 'Morning ratio', value: `${(d.morning_messages / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].sort((a, b) => b[1].engagement_rate - a[1].engagement_rate), emoji: '🧲', title: 'The Influencer', getStat: (d) => `${d.engagement_rate}% engagement`, getExplanation: (name, d) => `When ${name} talks, people respond! ${d.engagement_rate}% engagement rate.`, getExtra: (d) => ({ label: 'Replies', value: formatNumber(d.replied_to_count) }) },
                { list: [...people].sort((a, b) => b[1].questions - a[1].questions), emoji: '🤔', title: 'The Curious One', getStat: (d) => `${formatNumber(d.questions)} questions`, getExplanation: (name, d) => `${name} asked ${formatNumber(d.questions)} questions - always curious!`, getExtra: (d) => ({ label: 'Question rate', value: `${(d.questions / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].sort((a, b) => b[1].avg_chars - a[1].avg_chars), emoji: '📖', title: 'The Novelist', getStat: (d) => `${d.avg_chars} chars/msg`, getExplanation: (name, d) => `${name} writes essays averaging ${d.avg_chars} characters per message!`, getExtra: (d) => ({ label: 'Long msgs', value: formatNumber(d.long_messages) }) },
                { list: [...people].sort((a, b) => b[1].weekend_messages - a[1].weekend_messages), emoji: '🎉', title: 'Weekend Warrior', getStat: (d) => `${formatNumber(d.weekend_messages)} weekend msgs`, getExplanation: (name, d) => `${name} comes alive on weekends with ${formatNumber(d.weekend_messages)} messages!`, getExtra: (d) => ({ label: 'Weekend ratio', value: `${(d.weekend_messages / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].sort((a, b) => b[1].links - a[1].links), emoji: '🔗', title: 'Link Lord', getStat: (d) => `${formatNumber(d.links)} links`, getExplanation: (name, d) => `${name} shared ${formatNumber(d.links)} links - our news source!`, getExtra: (d) => ({ label: 'Per 100 msgs', value: (d.links / d.messages * 100).toFixed(1) }) },
                { list: [...people].sort((a, b) => b[1].mentions - a[1].mentions), emoji: '📢', title: 'The Tagger', getStat: (d) => `${formatNumber(d.mentions)} @mentions`, getExplanation: (name, d) => `${name} tagged people ${formatNumber(d.mentions)} times!`, getExtra: (d) => ({ label: 'Mention rate', value: `${(d.mentions / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].sort((a, b) => b[1].exclamations - a[1].exclamations), emoji: '❗', title: 'The Exclaimer', getStat: (d) => `${formatNumber(d.exclamations)} exclamations!`, getExplanation: (name, d) => `${name} brings ENERGY with ${formatNumber(d.exclamations)} exclamation messages!`, getExtra: (d) => ({ label: 'Hype level', value: `${(d.exclamations / d.messages * 100).toFixed(1)}%` }) },
                { list: [...people].filter(([,d]) => d.avg_response).sort((a, b) => b[1].avg_response - a[1].avg_response), emoji: '🐢', title: 'The Philosopher', getStat: (d) => `${d.avg_response}m to respond`, getExplanation: (name, d) => `${name} takes time to craft responses - ${d.avg_response} minutes average.`, getExtra: (d) => ({ label: 'Response time', value: `${d.avg_response}m` }) },
                { list: [...people].sort((a, b) => b[1].media_ratio - a[1].media_ratio), emoji: '🖼️', title: 'Visual Communicator', getStat: (d) => `${d.media_ratio}% media ratio`, getExplanation: (name, d) => `${name} lets pictures talk - ${d.media_ratio}% of messages are media!`, getExtra: (d) => ({ label: 'Total media', value: formatNumber(d.media) }) },
                { list: [...people].sort((a, b) => b[1].short_messages - a[1].short_messages), emoji: '💨', title: 'Short & Sweet', getStat: (d) => `${formatNumber(d.short_messages)} quick msgs`, getExplanation: (name, d) => `${name} keeps it brief with ${formatNumber(d.short_messages)} messages under 10 chars!`, getExtra: (d) => ({ label: 'Brevity rate', value: `${(d.short_messages / d.messages * 100).toFixed(1)}%` }) },
            ];

            const awards = [];
            let colorIndex = 0;

            for (const award of allAwards) {
                if (assigned.size >= people.length) break;
                for (const [name, data] of award.list) {
                    if (!assigned.has(name)) {
                        assigned.add(name);
                        awards.push({ ...award, name, data, color: colors[colorIndex % colors.length] });
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

        function renderCharts() {
            const months = Object.entries(stats.by_month).sort((a, b) => a[0].localeCompare(b[0]));
            const maxMonth = Math.max(...months.map(m => m[1]));
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

            document.getElementById('monthlyChart').innerHTML = months.map(([month, count]) => {
                const [year, m] = month.split('-');
                const height = Math.max(5, count / maxMonth * 100);
                const hue = 260 + (parseInt(m) - 1) * 10;
                return `<div class="bar-group"><div class="bar" style="height: ${height}%; background: linear-gradient(180deg, hsl(${hue}, 80%, 60%) 0%, hsl(${hue + 20}, 70%, 50%) 100%);"><div class="bar-tooltip">${formatNumber(count)}</div></div><div class="bar-label">${monthNames[parseInt(m) - 1]}</div></div>`;
            }).join('');

            const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const maxDay = Math.max(...stats.by_day_of_week);
            const dayColors = ['#06b6d4', '#8b5cf6', '#8b5cf6', '#8b5cf6', '#8b5cf6', '#8b5cf6', '#06b6d4'];

            document.getElementById('dayChart').innerHTML = stats.by_day_of_week.map((count, i) => {
                const height = Math.max(5, count / maxDay * 100);
                return `<div class="bar-group"><div class="bar" style="height: ${height}%; background: linear-gradient(180deg, ${dayColors[i]} 0%, ${dayColors[i]}99 100%);"><div class="bar-tooltip">${formatNumber(count)}</div></div><div class="bar-label">${dayNames[i]}</div></div>`;
            }).join('');

            const maxHour = Math.max(...stats.by_hour);
            document.getElementById('hourlyChart').innerHTML = stats.by_hour.map((count, h) => {
                const height = Math.max(5, count / maxHour * 100);
                const isNight = h >= 22 || h < 6;
                const isMorning = h >= 6 && h < 12;
                const color = isNight ? '#3b82f6' : isMorning ? '#f59e0b' : h < 18 ? '#8b5cf6' : '#f472b6';
                const label = h === 0 ? '12a' : h < 12 ? `${h}a` : h === 12 ? '12p' : `${h-12}p`;
                return `<div class="bar-group"><div class="bar" style="height: ${height}%; background: linear-gradient(180deg, ${color} 0%, ${color}99 100%);"><div class="bar-tooltip">${formatNumber(count)}</div></div><div class="bar-label">${label}</div></div>`;
            }).join('');

            // Heatmap
            const people = Object.entries(stats.by_person);
            const heatmapData = [];
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
                    heatmapHTML += `<div class="heatmap-cell" style="background: ${color};"></div>`;
                }
                heatmapHTML += '</div>';
            }
            document.getElementById('heatmap').innerHTML = heatmapHTML;

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
            const booksEquiv = (totalWords / 75000).toFixed(1);
            const topWords = stats.top_words.slice(0, 5).map(([w]) => w).join(', ');
            const lateNightMsgs = people.reduce((sum, [,d]) => sum + d.late_night_messages, 0);
            const nightPercent = (lateNightMsgs / stats.total_messages * 100).toFixed(1);

            const facts = [
                { icon: '📚', title: 'Novel Writers', text: `We've typed <span class="fact-highlight">${formatNumber(stats.total_chars)}</span> characters - approximately <span class="fact-highlight">${formatNumber(totalWords)}</span> words. Enough to fill <span class="fact-highlight">${booksEquiv} books</span>!` },
                { icon: '⏰', title: 'Prime Time', text: `The chat is on fire at <span class="fact-highlight">${peakHourLabel}</span>. That's when the real tea gets spilled!` },
                { icon: '📅', title: 'Favorite Day', text: `<span class="fact-highlight">${dayNames[peakDay]}</span> is our most active day with <span class="fact-highlight">${formatNumber(stats.by_day_of_week[peakDay])}</span> messages!` },
                { icon: '🔥', title: 'Record Breaker', text: `<span class="fact-highlight">${activeDateStr}</span> was WILD with <span class="fact-highlight">${formatNumber(stats.most_active_day.count)}</span> messages!` },
                { icon: '😂', title: 'Laughing Together', text: `We shared <span class="fact-highlight">${formatNumber(totalLaughs)}</span> laughs - that's <span class="fact-highlight">${(totalLaughs / stats.total_days).toFixed(1)}</span> per day!` },
                { icon: '🎭', title: 'Emoji Game', text: `<span class="fact-highlight">${formatNumber(totalEmojis)}</span> emojis were used! We speak fluent emoji.` },
                { icon: '❓', title: 'Curious Minds', text: `<span class="fact-highlight">${formatNumber(totalQuestions)}</span> questions asked. Always curious!` },
                { icon: '🔗', title: 'Link Droppers', text: `<span class="fact-highlight">${formatNumber(totalLinks)}</span> links shared - our curated feed!` },
                { icon: '🎬', title: 'Visual Vibes', text: `<span class="fact-highlight">${Math.round(stats.total_media / stats.total_messages * 100)}%</span> of messages were media!` },
                { icon: '🌙', title: 'Night Owls', text: `<span class="fact-highlight">${nightPercent}%</span> of messages sent between 11PM-4AM. Some don't sleep!` },
                { icon: '💬', title: 'Conversations', text: `<span class="fact-highlight">${formatNumber(totalConvos)}</span> conversations started - <span class="fact-highlight">${(totalConvos / stats.total_days).toFixed(1)}</span> topics per day!` },
                { icon: '📊', title: 'Daily Dose', text: `On average, <span class="fact-highlight">${Math.round(stats.total_messages / stats.total_days)}</span> messages per day!` },
                { icon: '🏆', title: 'Participation Trophy', text: `<span class="fact-highlight">${people.length}</span> people active across <span class="fact-highlight">${stats.total_days}</span> days!` },
                { icon: '📝', title: 'Longest Message', text: `Someone wrote <span class="fact-highlight">${formatNumber(stats.longest_message.length)}</span> characters! "${stats.longest_message.preview.slice(0, 60)}..."` },
                { icon: '🔤', title: 'Word Trends', text: `Most used words: <span class="fact-highlight">${topWords}</span>` },
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
                            <div class="mini-stat"><div class="mini-stat-value">${formatNumber(data.messages)}</div><div class="mini-stat-label">Messages</div></div>
                            <div class="mini-stat"><div class="mini-stat-value">${formatNumber(data.media)}</div><div class="mini-stat-label">Media</div></div>
                            <div class="mini-stat"><div class="mini-stat-value">${data.avg_response ? data.avg_response + 'm' : 'N/A'}</div><div class="mini-stat-label">Response</div></div>
                            <div class="mini-stat"><div class="mini-stat-value">${data.active_days_count}</div><div class="mini-stat-label">Days</div></div>
                            <div class="mini-stat"><div class="mini-stat-value">${formatNumber(data.emojis)}</div><div class="mini-stat-label">Emojis</div></div>
                            <div class="mini-stat"><div class="mini-stat-value">${formatNumber(data.laughs)}</div><div class="mini-stat-label">Laughs</div></div>
                            <div class="mini-stat"><div class="mini-stat-value">${peakLabel}</div><div class="mini-stat-label">Peak</div></div>
                            <div class="mini-stat"><div class="mini-stat-value">${data.avg_chars}</div><div class="mini-stat-label">Avg Len</div></div>
                        </div>
                    </div>
                `;
            }).join('');
        }

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
                    window.scrollTo({ top: document.querySelector('.nav').offsetTop, behavior: 'smooth' });
                });
            });
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            renderHeroStats();
            initLeaderboards();
            renderAwards();
            renderCharts();
            renderFacts();
            renderEveryone();
            setupNav();
        });
    </script>
</body>
</html>'''

    return html_template

def main():
    print("THE OBRUTS 2025 - Chat Stats Generator V3")
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

    print("\nGenerating HTML with dramatic reveals...")
    html_content = generate_html(stats)

    stats_json = json.dumps(stats, indent=2, default=str)
    html_content = html_content.replace('STATS_PLACEHOLDER', stats_json)

    output_path = '/Users/abanobnashat/Desktop/OBRUTS 25/Stats/obruts_wrapped_2025.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nDashboard generated: {output_path}")

if __name__ == '__main__':
    main()
