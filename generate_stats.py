#!/usr/bin/env python3
"""
THE OBRUTS 2025 - Chat Stats Generator
Processes WhatsApp chat export and generates an interactive HTML dashboard
"""

import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
import html

def parse_chat(filepath):
    """Parse WhatsApp chat export file"""
    messages = []
    # Handle optional leading special chars like \u200e
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

            # Remove leading special characters for matching
            clean_line = line.lstrip('\u200e\u200f\u202a\u202b\u202c\u202d\u202e')

            match = message_pattern.match(clean_line) or message_pattern.match(line)
            if match:
                if current_message:
                    messages.append(current_message)

                date_str, time_str, sender, content = match.groups()

                # Parse date (MM/DD/YY)
                month, day, year = map(int, date_str.split('/'))
                full_year = 2000 + year if year < 50 else 1900 + year

                # Parse time
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

                # Clean content of special chars
                content = content.strip().lstrip('\u200e\u200f\u202a\u202b\u202c\u202d\u202e')

                # Check for media - be more inclusive
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
    cutoff = datetime(2024, 11, 25)  # One year before Nov 25, 2025
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
            'emojis': 0,
            'questions': 0,
            'laughs': 0,
            'first_message': None,
            'last_message': None,
        }),
        'by_month': defaultdict(int),
        'by_hour': [0] * 24,
        'by_day_of_week': [0] * 7,
        'daily_counts': defaultdict(int),
        'longest_message': {'sender': '', 'length': 0, 'preview': ''},
        'active_days': set(),
    }

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002600-\U000026FF"  # Misc symbols
        "\U00002700-\U000027BF"  # Dingbats
        "]+", flags=re.UNICODE
    )

    laugh_pattern = re.compile(r'😂|😆|🤣|lol|lmao|haha|hehe|rofl', re.IGNORECASE)

    prev_message = None

    for msg in messages:
        if msg['is_system']:
            continue

        sender = normalize_name(msg['sender'])
        date_key = msg['date'].strftime('%Y-%m-%d')
        month_key = msg['date'].strftime('%Y-%m')
        hour = msg['date'].hour
        day_of_week = msg['date'].weekday()  # 0 = Monday
        # Convert to Sunday = 0 format
        day_of_week = (day_of_week + 1) % 7

        person = stats['by_person'][sender]

        # Basic counts
        person['messages'] += 1
        stats['total_messages'] += 1
        person['active_days'].add(date_key)
        stats['active_days'].add(date_key)
        person['by_hour'][hour] += 1
        stats['by_hour'][hour] += 1
        stats['by_day_of_week'][day_of_week] += 1
        stats['by_month'][month_key] += 1
        stats['daily_counts'][date_key] += 1

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

            # Count emojis
            emojis = emoji_pattern.findall(content)
            person['emojis'] += len(emojis)

            # Count questions
            if '?' in content:
                person['questions'] += 1

            # Count laughs
            laughs = laugh_pattern.findall(content)
            person['laughs'] += len(laughs)

            # Longest message
            if len(content) > stats['longest_message']['length']:
                stats['longest_message'] = {
                    'sender': sender,
                    'length': len(content),
                    'preview': content[:100] + ('...' if len(content) > 100 else '')
                }

        # Response time
        if prev_message and prev_message['sender'] != msg['sender']:
            time_diff = (msg['date'] - prev_message['date']).total_seconds() / 60
            if 0 < time_diff < 60:  # Within an hour
                person['response_times'].append(time_diff)

        prev_message = msg

    # Calculate derived stats
    for sender, person in stats['by_person'].items():
        # Convert sets to counts for JSON serialization
        person['active_days_count'] = len(person['active_days'])
        person['active_days'] = list(person['active_days'])

        # Average chars per message (excluding media)
        text_messages = person['messages'] - person['media']
        person['avg_chars'] = round(person['total_chars'] / text_messages) if text_messages > 0 else 0

        # Average response time
        if person['response_times']:
            person['avg_response'] = round(sum(person['response_times']) / len(person['response_times']), 1)
        else:
            person['avg_response'] = None

        # Peak hour
        person['peak_hour'] = person['by_hour'].index(max(person['by_hour']))

        # Convert datetimes to strings
        if person['first_message']:
            person['first_message'] = person['first_message'].isoformat()
        if person['last_message']:
            person['last_message'] = person['last_message'].isoformat()

        # Remove response times list (too large)
        del person['response_times']

    # Find most active day
    most_active_day = max(stats['daily_counts'].items(), key=lambda x: x[1])
    stats['most_active_day'] = {'date': most_active_day[0], 'count': most_active_day[1]}

    # Convert sets and defaultdicts
    stats['active_days'] = list(stats['active_days'])
    stats['total_days'] = len(stats['active_days'])
    stats['by_person'] = dict(stats['by_person'])
    stats['by_month'] = dict(stats['by_month'])
    stats['daily_counts'] = dict(stats['daily_counts'])

    return stats

def generate_html(stats):
    """Generate the HTML dashboard with embedded stats"""

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THE OBRUTS 2025 - Group Chat Stats</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&family=Orbitron:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #ec4899;
            --accent: #14b8a6;
            --gold: #f59e0b;
            --silver: #94a3b8;
            --bronze: #d97706;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --gradient-1: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            --gradient-2: linear-gradient(135deg, #14b8a6 0%, #6366f1 100%);
            --gradient-3: linear-gradient(135deg, #f59e0b 0%, #ec4899 100%);
            --glow: 0 0 40px rgba(99, 102, 241, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background:
                radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(236, 72, 153, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(20, 184, 166, 0.1) 0%, transparent 50%);
            animation: bgPulse 10s ease-in-out infinite;
        }

        @keyframes bgPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            pointer-events: none;
        }

        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--primary);
            border-radius: 50%;
            animation: float 15s infinite;
            opacity: 0.5;
        }

        @keyframes float {
            0%, 100% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 0.5; }
            90% { opacity: 0.5; }
            100% { transform: translateY(-100vh) rotate(720deg); opacity: 0; }
        }

        .header {
            text-align: center;
            padding: 60px 20px;
            position: relative;
        }

        .logo {
            font-family: 'Orbitron', sans-serif;
            font-size: clamp(3rem, 10vw, 6rem);
            font-weight: 900;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: var(--glow);
            letter-spacing: 0.1em;
            animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from { filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.5)); }
            to { filter: drop-shadow(0 0 40px rgba(236, 72, 153, 0.5)); }
        }

        .tagline {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-top: 10px;
            font-weight: 300;
        }

        .year-badge {
            display: inline-block;
            background: var(--gradient-3);
            padding: 8px 24px;
            border-radius: 50px;
            font-weight: 700;
            margin-top: 20px;
            font-size: 1.1rem;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 20px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .stat-card {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-1);
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--glow);
            border-color: var(--primary);
        }

        .stat-number {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 8px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .section-title {
            text-align: center;
            padding: 60px 20px 30px;
        }

        .section-title h2 {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            background: var(--gradient-2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .section-title .emoji {
            font-size: 2.5rem;
            margin-bottom: 10px;
            display: block;
        }

        .leaderboard {
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .leaderboard-item {
            display: flex;
            align-items: center;
            background: var(--bg-card);
            border-radius: 16px;
            padding: 20px 30px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.05);
            position: relative;
            overflow: hidden;
        }

        .leaderboard-item:hover {
            transform: translateX(10px);
            border-color: var(--primary);
            box-shadow: var(--glow);
        }

        .leaderboard-item.gold {
            border-color: var(--gold);
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, var(--bg-card) 100%);
        }

        .leaderboard-item.silver {
            border-color: var(--silver);
            background: linear-gradient(135deg, rgba(148, 163, 184, 0.1) 0%, var(--bg-card) 100%);
        }

        .leaderboard-item.bronze {
            border-color: var(--bronze);
            background: linear-gradient(135deg, rgba(217, 119, 6, 0.1) 0%, var(--bg-card) 100%);
        }

        .rank {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            width: 60px;
            text-align: center;
        }

        .rank.gold { color: var(--gold); }
        .rank.silver { color: var(--silver); }
        .rank.bronze { color: var(--bronze); }

        .avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--gradient-1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.2rem;
            margin-right: 20px;
        }

        .player-info {
            flex: 1;
        }

        .player-name {
            font-weight: 600;
            font-size: 1.1rem;
        }

        .player-stat {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .score {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            padding: 20px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .stats-panel {
            background: var(--bg-card);
            border-radius: 24px;
            padding: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .stats-panel h3 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .awards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            padding: 20px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .award-card {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }

        .award-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg, transparent, var(--primary), transparent, var(--secondary), transparent);
            animation: rotate 4s linear infinite;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .award-card:hover::before {
            opacity: 0.1;
        }

        @keyframes rotate {
            100% { transform: rotate(360deg); }
        }

        .award-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.2);
        }

        .award-emoji {
            font-size: 4rem;
            margin-bottom: 15px;
            display: block;
        }

        .award-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 1rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 10px;
        }

        .award-winner {
            font-size: 1.4rem;
            font-weight: 700;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .award-stat {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 8px;
        }

        .chart-container {
            background: var(--bg-card);
            border-radius: 24px;
            padding: 30px;
            margin: 20px 40px;
            max-width: 1320px;
            margin-left: auto;
            margin-right: auto;
        }

        .chart-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .bar-chart {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            height: 200px;
            padding-top: 20px;
        }

        .bar-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            height: 100%;
        }

        .bar {
            width: 60%;
            background: var(--gradient-1);
            border-radius: 8px 8px 0 0;
            transition: all 0.3s ease;
            position: relative;
            min-height: 5px;
        }

        .bar:hover {
            filter: brightness(1.2);
            transform: scaleY(1.02);
        }

        .bar-label {
            color: var(--text-secondary);
            font-size: 0.75rem;
            margin-top: 10px;
            text-align: center;
        }

        .bar-value {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--accent);
            opacity: 0;
            transition: opacity 0.3s;
        }

        .bar:hover .bar-value {
            opacity: 1;
        }

        .fun-facts {
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(99, 102, 241, 0.1) 100%);
            border-radius: 24px;
            padding: 40px;
            margin: 40px;
            max-width: 1320px;
            margin-left: auto;
            margin-right: auto;
        }

        .fact-item {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .fact-item:last-child {
            border-bottom: none;
        }

        .fact-icon {
            font-size: 2.5rem;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-dark);
            border-radius: 50%;
        }

        .fact-content h4 {
            font-size: 1.1rem;
            margin-bottom: 5px;
        }

        .fact-content p {
            color: var(--text-secondary);
        }

        .fact-highlight {
            color: var(--accent);
            font-weight: 700;
        }

        .footer {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }

        .footer-logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }

        .tabs {
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
            padding: 20px;
        }

        .tab-btn {
            background: var(--bg-card);
            border: 2px solid transparent;
            color: var(--text-primary);
            padding: 12px 24px;
            border-radius: 50px;
            cursor: pointer;
            font-family: 'Poppins', sans-serif;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .tab-btn:hover, .tab-btn.active {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.2);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .person-details {
            background: var(--bg-card);
            border-radius: 24px;
            padding: 30px;
            margin: 20px 0;
        }

        .person-header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }

        .person-avatar-large {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: var(--gradient-1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            font-weight: 700;
        }

        .person-stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
        }

        .mini-stat {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
        }

        .mini-stat-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            color: var(--accent);
        }

        .mini-stat-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 5px;
        }

        .animate-in {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease;
        }

        .animate-in.visible {
            opacity: 1;
            transform: translateY(0);
        }

        @media (max-width: 768px) {
            .stats-overview {
                grid-template-columns: repeat(2, 1fr);
                padding: 20px;
            }

            .stats-grid, .awards-grid {
                padding: 20px;
            }

            .leaderboard-item {
                padding: 15px;
            }

            .fun-facts {
                margin: 20px;
                padding: 20px;
            }

            .chart-container {
                margin: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="particles" id="particles"></div>

    <header class="header">
        <div class="logo">THE OBRUTS</div>
        <p class="tagline">"TURBO" spelled backwards - Friends since forever</p>
        <div class="year-badge">2024-2025 STATS</div>
    </header>

    <section class="stats-overview" id="overview"></section>

    <div class="tabs">
        <button class="tab-btn active" data-tab="leaderboards">Leaderboards</button>
        <button class="tab-btn" data-tab="awards">Awards</button>
        <button class="tab-btn" data-tab="activity">Activity</button>
        <button class="tab-btn" data-tab="funfacts">Fun Facts</button>
        <button class="tab-btn" data-tab="everyone">Everyone</button>
    </div>

    <div class="tab-content active" id="leaderboards">
        <div class="section-title">
            <span class="emoji">🏆</span>
            <h2>MESSAGE LEADERBOARD</h2>
        </div>
        <div class="leaderboard" id="messageLeaderboard"></div>

        <div class="section-title">
            <span class="emoji">⚡</span>
            <h2>FASTEST RESPONDERS</h2>
        </div>
        <div class="leaderboard" id="responseLeaderboard"></div>

        <div class="section-title">
            <span class="emoji">📸</span>
            <h2>MEDIA SHARERS</h2>
        </div>
        <div class="leaderboard" id="mediaLeaderboard"></div>
    </div>

    <div class="tab-content" id="awards">
        <div class="section-title">
            <span class="emoji">🎖️</span>
            <h2>SPECIAL AWARDS</h2>
        </div>
        <div class="awards-grid" id="awardsGrid"></div>
    </div>

    <div class="tab-content" id="activity">
        <div class="section-title">
            <span class="emoji">📊</span>
            <h2>MONTHLY ACTIVITY</h2>
        </div>
        <div class="chart-container">
            <div class="chart-title"><span>📈</span> Messages Per Month</div>
            <div class="bar-chart" id="monthlyChart"></div>
        </div>

        <div class="section-title">
            <span class="emoji">🕐</span>
            <h2>WHEN DO WE CHAT?</h2>
        </div>
        <div class="chart-container">
            <div class="chart-title"><span>⏰</span> Activity by Hour (0-23)</div>
            <div class="bar-chart" id="hourlyChart"></div>
        </div>

        <div class="section-title">
            <span class="emoji">📅</span>
            <h2>DAY OF WEEK ACTIVITY</h2>
        </div>
        <div class="chart-container">
            <div class="chart-title"><span>📆</span> Messages by Day of Week</div>
            <div class="bar-chart" id="dayChart"></div>
        </div>
    </div>

    <div class="tab-content" id="funfacts">
        <div class="section-title">
            <span class="emoji">🎉</span>
            <h2>FUN FACTS & INSIGHTS</h2>
        </div>
        <div class="fun-facts" id="funFactsContainer"></div>
    </div>

    <div class="tab-content" id="everyone">
        <div class="section-title">
            <span class="emoji">👥</span>
            <h2>EVERYONE'S STATS</h2>
        </div>
        <div class="stats-grid" id="everyoneStats"></div>
    </div>

    <footer class="footer">
        <div class="footer-logo">THE OBRUTS</div>
        <p>Group Chat Stats - Generated with love</p>
        <p style="margin-top: 10px; font-size: 0.8rem;">Data from November 25, 2024 to November 25, 2025</p>
    </footer>

    <script>
        const stats = STATS_PLACEHOLDER;

        function renderOverview() {
            const container = document.getElementById('overview');
            const avgPerDay = Math.round(stats.total_messages / stats.total_days);
            const memberCount = Object.keys(stats.by_person).length;

            container.innerHTML = `
                <div class="stat-card animate-in">
                    <div class="stat-number">${stats.total_messages.toLocaleString()}</div>
                    <div class="stat-label">Total Messages</div>
                </div>
                <div class="stat-card animate-in">
                    <div class="stat-number">${stats.total_media.toLocaleString()}</div>
                    <div class="stat-label">Media Shared</div>
                </div>
                <div class="stat-card animate-in">
                    <div class="stat-number">${memberCount}</div>
                    <div class="stat-label">Active Members</div>
                </div>
                <div class="stat-card animate-in">
                    <div class="stat-number">${stats.total_days}</div>
                    <div class="stat-label">Days Active</div>
                </div>
                <div class="stat-card animate-in">
                    <div class="stat-number">${avgPerDay}</div>
                    <div class="stat-label">Avg/Day</div>
                </div>
                <div class="stat-card animate-in">
                    <div class="stat-number">${stats.most_active_day.count}</div>
                    <div class="stat-label">Most Active Day</div>
                </div>
            `;
        }

        function renderLeaderboard() {
            const messageContainer = document.getElementById('messageLeaderboard');
            const sortedByMessages = Object.entries(stats.by_person)
                .sort((a, b) => b[1].messages - a[1].messages);

            messageContainer.innerHTML = sortedByMessages.map(([name, data], index) => {
                const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
                const medals = ['🥇', '🥈', '🥉'];
                const medal = medals[index] || `#${index + 1}`;
                const percentage = Math.round(data.messages / stats.total_messages * 100);

                return `
                    <div class="leaderboard-item ${rankClass} animate-in">
                        <div class="rank ${rankClass}">${medal}</div>
                        <div class="avatar">${name.charAt(0)}</div>
                        <div class="player-info">
                            <div class="player-name">${name}</div>
                            <div class="player-stat">${percentage}% of all messages</div>
                        </div>
                        <div class="score">${data.messages.toLocaleString()}</div>
                    </div>
                `;
            }).join('');

            const responseContainer = document.getElementById('responseLeaderboard');
            const sortedByResponse = Object.entries(stats.by_person)
                .filter(([, data]) => data.avg_response !== null)
                .sort((a, b) => a[1].avg_response - b[1].avg_response);

            responseContainer.innerHTML = sortedByResponse.slice(0, 10).map(([name, data], index) => {
                const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
                const medals = ['🥇', '🥈', '🥉'];
                const medal = medals[index] || `#${index + 1}`;

                return `
                    <div class="leaderboard-item ${rankClass} animate-in">
                        <div class="rank ${rankClass}">${medal}</div>
                        <div class="avatar">${name.charAt(0)}</div>
                        <div class="player-info">
                            <div class="player-name">${name}</div>
                            <div class="player-stat">Lightning fast responses</div>
                        </div>
                        <div class="score">${data.avg_response}m</div>
                    </div>
                `;
            }).join('');

            const mediaContainer = document.getElementById('mediaLeaderboard');
            const sortedByMedia = Object.entries(stats.by_person)
                .sort((a, b) => b[1].media - a[1].media);

            mediaContainer.innerHTML = sortedByMedia.slice(0, 10).map(([name, data], index) => {
                const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
                const medals = ['🥇', '🥈', '🥉'];
                const medal = medals[index] || `#${index + 1}`;
                const percentage = stats.total_media > 0 ? Math.round(data.media / stats.total_media * 100) : 0;

                return `
                    <div class="leaderboard-item ${rankClass} animate-in">
                        <div class="rank ${rankClass}">${medal}</div>
                        <div class="avatar">${name.charAt(0)}</div>
                        <div class="player-info">
                            <div class="player-name">${name}</div>
                            <div class="player-stat">${percentage}% of all media</div>
                        </div>
                        <div class="score">${data.media.toLocaleString()}</div>
                    </div>
                `;
            }).join('');
        }

        function renderAwards() {
            const container = document.getElementById('awardsGrid');
            const sorted = Object.entries(stats.by_person);

            const mostMessages = [...sorted].sort((a, b) => b[1].messages - a[1].messages)[0];
            const fastestResponder = [...sorted].filter(([, d]) => d.avg_response !== null).sort((a, b) => a[1].avg_response - b[1].avg_response)[0];
            const slowestResponder = [...sorted].filter(([, d]) => d.avg_response !== null).sort((a, b) => b[1].avg_response - a[1].avg_response)[0];
            const mostMedia = [...sorted].sort((a, b) => b[1].media - a[1].media)[0];
            const mostEmojis = [...sorted].sort((a, b) => b[1].emojis - a[1].emojis)[0];
            const mostQuestions = [...sorted].sort((a, b) => b[1].questions - a[1].questions)[0];
            const mostLaughs = [...sorted].sort((a, b) => b[1].laughs - a[1].laughs)[0];
            const longestAvgMsg = [...sorted].sort((a, b) => b[1].avg_chars - a[1].avg_chars)[0];
            const shortestAvgMsg = [...sorted].filter(([, d]) => d.avg_chars > 0).sort((a, b) => a[1].avg_chars - b[1].avg_chars)[0];
            const mostActiveDays = [...sorted].sort((a, b) => b[1].active_days_count - a[1].active_days_count)[0];
            const leastMessages = [...sorted].sort((a, b) => a[1].messages - b[1].messages)[0];

            const nightOwl = [...sorted].sort((a, b) => {
                const nightHours = [22, 23, 0, 1, 2, 3, 4];
                const aNight = nightHours.reduce((sum, h) => sum + a[1].by_hour[h], 0);
                const bNight = nightHours.reduce((sum, h) => sum + b[1].by_hour[h], 0);
                return bNight - aNight;
            })[0];

            const earlyBird = [...sorted].sort((a, b) => {
                const morningHours = [5, 6, 7, 8, 9];
                const aMorning = morningHours.reduce((sum, h) => sum + a[1].by_hour[h], 0);
                const bMorning = morningHours.reduce((sum, h) => sum + b[1].by_hour[h], 0);
                return bMorning - aMorning;
            })[0];

            const awards = [
                { emoji: '👑', title: 'Chat Champion', winner: mostMessages[0], stat: `${mostMessages[1].messages.toLocaleString()} messages` },
                { emoji: '⚡', title: 'Speed Demon', winner: fastestResponder ? fastestResponder[0] : 'N/A', stat: fastestResponder ? `${fastestResponder[1].avg_response}min avg response` : 'N/A' },
                { emoji: '🐢', title: 'The Tortoise', winner: slowestResponder ? slowestResponder[0] : 'N/A', stat: slowestResponder ? `${slowestResponder[1].avg_response}min avg response` : 'N/A' },
                { emoji: '📸', title: 'Media Master', winner: mostMedia[0], stat: `${mostMedia[1].media.toLocaleString()} media shared` },
                { emoji: '😂', title: 'Class Clown', winner: mostLaughs[0], stat: `${mostLaughs[1].laughs.toLocaleString()} laughs` },
                { emoji: '🤔', title: 'The Curious One', winner: mostQuestions[0], stat: `${mostQuestions[1].questions.toLocaleString()} questions asked` },
                { emoji: '📝', title: 'The Novelist', winner: longestAvgMsg[0], stat: `${longestAvgMsg[1].avg_chars} chars/msg avg` },
                { emoji: '💬', title: 'Short & Sweet', winner: shortestAvgMsg ? shortestAvgMsg[0] : 'N/A', stat: shortestAvgMsg ? `${shortestAvgMsg[1].avg_chars} chars/msg avg` : 'N/A' },
                { emoji: '🎭', title: 'Emoji King', winner: mostEmojis[0], stat: `${mostEmojis[1].emojis.toLocaleString()} emojis used` },
                { emoji: '📅', title: 'Most Consistent', winner: mostActiveDays[0], stat: `${mostActiveDays[1].active_days_count} days active` },
                { emoji: '🌙', title: 'Night Owl', winner: nightOwl[0], stat: `Active late nights` },
                { emoji: '🌅', title: 'Early Bird', winner: earlyBird[0], stat: `Catches the worm` },
                { emoji: '👻', title: 'The Ghost', winner: leastMessages[0], stat: `${leastMessages[1].messages} messages only` },
                { emoji: '📚', title: 'Longest Message', winner: stats.longest_message.sender, stat: `${stats.longest_message.length} characters` },
            ];

            container.innerHTML = awards.map(award => `
                <div class="award-card animate-in">
                    <span class="award-emoji">${award.emoji}</span>
                    <div class="award-title">${award.title}</div>
                    <div class="award-winner">${award.winner}</div>
                    <div class="award-stat">${award.stat}</div>
                </div>
            `).join('');
        }

        function renderCharts() {
            const monthlyContainer = document.getElementById('monthlyChart');
            const months = Object.entries(stats.by_month).sort((a, b) => a[0].localeCompare(b[0]));
            const maxMonth = Math.max(...months.map(m => m[1]));
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

            monthlyContainer.innerHTML = months.map(([month, count]) => {
                const [year, monthNum] = month.split('-');
                const height = (count / maxMonth * 100);
                const label = `${monthNames[parseInt(monthNum) - 1]} '${year.slice(2)}`;
                return `
                    <div class="bar-wrapper">
                        <div class="bar" style="height: ${height}%">
                            <span class="bar-value">${count.toLocaleString()}</span>
                        </div>
                        <div class="bar-label">${label}</div>
                    </div>
                `;
            }).join('');

            const hourlyContainer = document.getElementById('hourlyChart');
            const maxHour = Math.max(...stats.by_hour);

            hourlyContainer.innerHTML = stats.by_hour.map((count, hour) => {
                const height = (count / maxHour * 100);
                const label = hour === 0 ? '12a' : hour < 12 ? `${hour}a` : hour === 12 ? '12p' : `${hour-12}p`;
                const isNight = hour >= 22 || hour < 6;
                const isMorning = hour >= 6 && hour < 12;
                const gradient = isNight ? 'linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%)' :
                                 isMorning ? 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)' :
                                 'var(--gradient-1)';
                return `
                    <div class="bar-wrapper">
                        <div class="bar" style="height: ${height}%; background: ${gradient}">
                            <span class="bar-value">${count.toLocaleString()}</span>
                        </div>
                        <div class="bar-label">${label}</div>
                    </div>
                `;
            }).join('');

            const dayContainer = document.getElementById('dayChart');
            const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const maxDay = Math.max(...stats.by_day_of_week);

            dayContainer.innerHTML = stats.by_day_of_week.map((count, day) => {
                const height = (count / maxDay * 100);
                const isWeekend = day === 0 || day === 6;
                return `
                    <div class="bar-wrapper">
                        <div class="bar" style="height: ${height}%; background: ${isWeekend ? 'linear-gradient(135deg, #14b8a6 0%, #06b6d4 100%)' : 'var(--gradient-1)'}">
                            <span class="bar-value">${count.toLocaleString()}</span>
                        </div>
                        <div class="bar-label">${dayNames[day]}</div>
                    </div>
                `;
            }).join('');
        }

        function renderFunFacts() {
            const container = document.getElementById('funFactsContainer');
            const peakHour = stats.by_hour.indexOf(Math.max(...stats.by_hour));
            const peakHourLabel = peakHour === 0 ? '12 AM' : peakHour < 12 ? `${peakHour} AM` : peakHour === 12 ? '12 PM' : `${peakHour - 12} PM`;

            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const peakDay = stats.by_day_of_week.indexOf(Math.max(...stats.by_day_of_week));

            const activeDate = new Date(stats.most_active_day.date);
            const activeDateStr = activeDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

            const totalWords = Math.round(stats.total_chars / 5);
            const mediaPercent = Math.round(stats.total_media / stats.total_messages * 100);

            const facts = [
                { icon: '💬', title: 'Total Characters Typed', fact: `The group has typed over <span class="fact-highlight">${stats.total_chars.toLocaleString()}</span> characters - that's roughly <span class="fact-highlight">${totalWords.toLocaleString()}</span> words!` },
                { icon: '📈', title: 'Busiest Time', fact: `The chat is most active at <span class="fact-highlight">${peakHourLabel}</span> - that's when the real conversations happen!` },
                { icon: '📅', title: 'Favorite Day', fact: `<span class="fact-highlight">${dayNames[peakDay]}</span> is the most active day of the week with <span class="fact-highlight">${stats.by_day_of_week[peakDay].toLocaleString()}</span> messages.` },
                { icon: '🔥', title: 'Record Breaking Day', fact: `<span class="fact-highlight">${activeDateStr}</span> was WILD with <span class="fact-highlight">${stats.most_active_day.count}</span> messages!` },
                { icon: '📊', title: 'Daily Average', fact: `On average, the group sends <span class="fact-highlight">${Math.round(stats.total_messages / stats.total_days)}</span> messages per day.` },
                { icon: '🎬', title: 'Media Madness', fact: `<span class="fact-highlight">${mediaPercent}%</span> of all messages are images, videos, stickers, or GIFs!` },
                { icon: '📝', title: 'The Longest Message', fact: `"${stats.longest_message.preview}" - sent by <span class="fact-highlight">${stats.longest_message.sender}</span> (${stats.longest_message.length} characters)` },
                { icon: '👥', title: 'Group Participation', fact: `<span class="fact-highlight">${Object.keys(stats.by_person).length}</span> members have been active in the past year!` },
            ];

            container.innerHTML = facts.map(fact => `
                <div class="fact-item animate-in">
                    <div class="fact-icon">${fact.icon}</div>
                    <div class="fact-content">
                        <h4>${fact.title}</h4>
                        <p>${fact.fact}</p>
                    </div>
                </div>
            `).join('');
        }

        function renderEveryone() {
            const container = document.getElementById('everyoneStats');
            const sorted = Object.entries(stats.by_person).sort((a, b) => b[1].messages - a[1].messages);

            container.innerHTML = sorted.map(([name, data]) => {
                const peakHour = data.peak_hour;
                const peakHourLabel = peakHour === 0 ? '12 AM' : peakHour < 12 ? `${peakHour} AM` : peakHour === 12 ? '12 PM' : `${peakHour - 12} PM`;
                const percentage = Math.round(data.messages / stats.total_messages * 100);

                return `
                    <div class="person-details animate-in">
                        <div class="person-header">
                            <div class="person-avatar-large">${name.charAt(0)}</div>
                            <div>
                                <h3 style="margin: 0; font-size: 1.5rem;">${name}</h3>
                                <p style="color: var(--text-secondary); margin: 5px 0 0;">${percentage}% of chat</p>
                            </div>
                        </div>
                        <div class="person-stats-grid">
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.messages.toLocaleString()}</div>
                                <div class="mini-stat-label">Messages</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.media.toLocaleString()}</div>
                                <div class="mini-stat-label">Media</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.avg_response !== null ? data.avg_response + 'm' : 'N/A'}</div>
                                <div class="mini-stat-label">Avg Response</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.avg_chars}</div>
                                <div class="mini-stat-label">Chars/Msg</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.active_days_count}</div>
                                <div class="mini-stat-label">Days Active</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${peakHourLabel}</div>
                                <div class="mini-stat-label">Peak Hour</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.emojis.toLocaleString()}</div>
                                <div class="mini-stat-label">Emojis</div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-value">${data.laughs.toLocaleString()}</div>
                                <div class="mini-stat-label">Laughs</div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function setupTabs() {
            const tabBtns = document.querySelectorAll('.tab-btn');
            const tabContents = document.querySelectorAll('.tab-content');

            tabBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const targetTab = btn.dataset.tab;
                    tabBtns.forEach(b => b.classList.remove('active'));
                    tabContents.forEach(c => c.classList.remove('active'));
                    btn.classList.add('active');
                    document.getElementById(targetTab).classList.add('active');
                    setTimeout(() => {
                        document.querySelectorAll('.animate-in').forEach(el => el.classList.add('visible'));
                    }, 100);
                });
            });
        }

        function createParticles() {
            const container = document.getElementById('particles');
            const colors = ['#6366f1', '#ec4899', '#14b8a6', '#f59e0b'];
            for (let i = 0; i < 30; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 15 + 's';
                particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
                particle.style.background = colors[Math.floor(Math.random() * colors.length)];
                container.appendChild(particle);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            renderOverview();
            renderLeaderboard();
            renderAwards();
            renderCharts();
            renderFunFacts();
            renderEveryone();
            setupTabs();
            createParticles();
            setTimeout(() => {
                document.querySelectorAll('.animate-in').forEach(el => el.classList.add('visible'));
            }, 100);
        });
    </script>
</body>
</html>'''

    return html_template

def main():
    print("THE OBRUTS 2025 - Chat Stats Generator")
    print("=" * 50)

    # Parse chat
    print("Parsing chat file...")
    messages = parse_chat('/Users/abanobnashat/Desktop/OBRUTS 25/Stats/_chat.txt')
    print(f"Total messages parsed: {len(messages)}")

    # Filter last 365 days
    print("Filtering to last 365 days...")
    filtered = filter_last_365_days(messages)
    print(f"Messages in last 365 days: {len(filtered)}")

    # Calculate stats
    print("Calculating stats...")
    stats = calculate_stats(filtered)

    # Print summary
    print(f"\nSummary:")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Total media: {stats['total_media']}")
    print(f"  Active members: {len(stats['by_person'])}")
    print(f"  Days active: {stats['total_days']}")
    print(f"  Most active day: {stats['most_active_day']['date']} ({stats['most_active_day']['count']} messages)")

    # Generate HTML
    print("\nGenerating HTML...")
    html_content = generate_html(stats)

    # Replace placeholder with actual stats
    stats_json = json.dumps(stats, indent=2, default=str)
    html_content = html_content.replace('STATS_PLACEHOLDER', stats_json)

    # Write HTML file
    output_path = '/Users/abanobnashat/Desktop/OBRUTS 25/Stats/obruts_stats_dashboard.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nDashboard generated: {output_path}")
    print("\nOpen the HTML file in your browser to view the stats!")

if __name__ == '__main__':
    main()
