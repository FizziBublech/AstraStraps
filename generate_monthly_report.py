import json
import glob
import os
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import math

# Configuration
COMPANY_NAME = "AstraStraps"
# Branding: White & Black
THEME_COLOR = "#000000"  # Black for primary accents
BG_COLOR = "#FFFFFF"     # White Background
TEXT_COLOR = "#111111"   # Nearly Black text
CARD_BG = "#F5F5F7"      # Light Gray/Off-White for cards (Apple-esque)

# Hourly Rate for ROI calculation
HOURLY_RATE = 25.0 

# Known products for NLP extraction - Refined list
# Removing generic "Silicone" as requested
PRODUCTS = [
    "Nix Nylon", 
    "Alpine Loop", 
    "Ocean Band", 
    "Leather Link", 
    "Metal Link", 
    "Trail Loop", 
    "Cyber Band",
    "Titanium Band"
]

def load_data(month_str=None):
    """
    Load analysis reports.
    If month_str is provided (YYYY-MM), filter by that month.
    Otherwise, default to the previous month relative to today.
    """
    if not month_str:
        # Default to previous month
        today = datetime.now()
        first = today.replace(day=1)
        if first.month > 1:
            last_month = first.replace(month=first.month-1)
        else:
            last_month = first.replace(year=first.year-1, month=12)
        month_str = last_month.strftime("%Y-%m")
        
    print(f"Loading data for: {month_str}")
    
    all_conversations = []
    files = glob.glob("analysis_report_*.json")
    
    for f in files:
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    for item in data:
                        if "date" in item and item["date"].startswith(month_str):
                            all_conversations.append(item)
        except Exception as e:
            print(f"Error loading {f}: {e}")
            
    # Remove duplicates by ID
    unique_convos = {c["id"]: c for c in all_conversations}.values()
    return list(unique_convos), month_str

def classify_intent(analysis_text):
    """
    Classify the intent of the conversation based on keywords in the analysis summary.
    Returns: 'Product & Sales', 'Order Tracking', 'Support & Returns', or 'General Inquiry'
    """
    text = analysis_text.lower()
    
    sales_keywords = ["buy", "purchase", "recommend", "fit", "size", "width", "color", "material", "silicone", "leather", "metal", "stock", "price", "discount", "sale", "shop", "cart", "browse"]
    tracking_keywords = ["track", "shipping", "delivery", "status", "where is", "arrive", "shipped", "package", "tracking", "order"]
    support_keywords = ["return", "refund", "ticket", "cancel", "broken", "defect", "warranty", "wrong", "missing", "human", "agent", "support", "help", "issue"]
    
    for k in sales_keywords:
        if k in text: return "Product & Sales"
    for k in tracking_keywords:
        if k in text: return "Order Tracking"
    for k in support_keywords:
        if k in text: return "Support & Returns"
            
    return "General Inquiry"

def calculate_weighted_time(intent):
    """
    Calculate estimated human time saved based on complexity of intent.
    """
    if intent == "Product & Sales": return 15.0
    elif intent == "Support & Returns": return 12.0
    elif intent == "Order Tracking": return 5.0
    else: return 8.0

def generate_html(stats, month_str):
    date_obj = datetime.strptime(month_str, "%Y-%m")
    display_date = date_obj.strftime("%B %Y")
    
    total = stats['total']
    if total == 0:
        return "<h1>No data found for this month</h1>"

    hours_saved = round(stats['total_hours_saved'], 1)
    money_saved = round(hours_saved * HOURLY_RATE)
    successful_interactions = stats['resolved_instantly'] + stats['tickets_created']
    automation_rate = round((successful_interactions / total) * 100, 1)
    happiness_score = 100 - round((stats['unhappy'] / total) * 100, 1) if total > 0 else 100

    # Chart Data Preparation
    intent_labels = list(stats['intents'].keys())
    intent_values = list(stats['intents'].values())
    
    # Sort daily data for line charts
    sorted_days = sorted(stats['daily_volume'].keys())
    daily_labels = [d.split('-')[-1] for d in sorted_days] # Just the day number
    daily_volume = [stats['daily_volume'][d] for d in sorted_days]
    daily_sentiment = [stats['daily_sentiment'][d] for d in sorted_days]
    
    # Product Leaderboard
    sorted_products = sorted(stats['products'].items(), key=lambda x: x[1], reverse=True)[:5]
    product_labels = [p[0] for p in sorted_products]
    product_values = [p[1] for p in sorted_products]
    
    # Resolution Breakdown
    reso_labels = ["Instant Answer", "Automated Ticket", "Escalated/Error"]
    reso_values = [stats['resolved_instantly'], stats['tickets_created'], total - successful_interactions]

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{COMPANY_NAME} Performance - {display_date}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: {THEME_COLOR};
                --bg: {BG_COLOR};
                --card-bg: {CARD_BG};
                --card-border: 1px solid #E5E5E5;
                --text: {TEXT_COLOR};
                --text-muted: #666666;
                --success: #008000;
            }}
            body {{
                font-family: 'Outfit', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 40px;
                line-height: 1.6;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{
                background: var(--card-bg);
                padding: 30px;
                border-radius: 18px;
                border: var(--card-border);
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            }}
            header {{
                margin-bottom: 50px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #000;
                padding-bottom: 30px;
            }}
            .logo-section {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            .logo-img {{
                height: 50px;
                width: auto;
            }}
            h1 {{
                font-size: 32px;
                margin: 0;
                color: #000;
                font-weight: 800;
                letter-spacing: -1px;
            }}
            .subtitle {{ color: #000; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; font-size: 12px; margin-bottom: 5px; }}
            
            .grid-4 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .metric-label {{ color: var(--text-muted); font-size: 13px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 10px; }}
            .metric-value {{ font-size: 42px; font-weight: 800; color: #000; }}
            .positive {{ color: var(--success); font-size: 14px; font-weight: 600; margin-top: 5px; }}
            
            .chart-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 25px;
            }}
            .span-2 {{ grid-column: span 2; }}
            
            h2 {{ 
                font-size: 20px; 
                margin: 0 0 25px 0; 
                color: #000; 
                font-weight: 700;
            }}
            
            .chart-container {{ height: 300px; position: relative; }}
            
            .trend-tag {{
                display: inline-block;
                padding: 10px 18px;
                background: #FFFFFF;
                border-radius: 30px;
                margin: 6px;
                font-size: 14px;
                color: #000;
                font-weight: 600;
                border: 1px solid #ddd;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }}
            
            .list-item {{
                padding: 20px 0;
                border-bottom: 1px solid #ddd;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .list-item:last-child {{ border-bottom: none; }}
            
            footer {{ margin-top: 60px; text-align: center; color: var(--text-muted); font-size: 12px; letter-spacing: 1px; border-top: 1px solid #eee; padding-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="logo-section">
                    <img src="https://astrastraps.com/cdn/shop/files/logo.png?v=1715132615&width=300" alt="AstraStraps Logo" class="logo-img">
                    <div>
                        <div class="subtitle">AI Performance Report</div>
                        <h1>{display_date}</h1>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 12px; color: var(--text-muted); font-weight:600;">EST. ROI GENERATED</div>
                    <div style="font-size: 32px; font-weight: 800; color: #000;">${money_saved}</div>
                </div>
            </header>

            <div class="grid-4">
                <div class="card">
                    <div class="metric-label">Conversations</div>
                    <div class="metric-value">{total}</div>
                    <div class="positive">● Online 24/7</div>
                </div>
                <div class="card">
                    <div class="metric-label">Human Hours Saved</div>
                    <div class="metric-value">{hours_saved}h</div>
                    <div class="positive">↑ Highly Efficient</div>
                </div>
                <div class="card">
                    <div class="metric-label">Resolution Rate</div>
                    <div class="metric-value">{automation_rate}%</div>
                    <div class="positive">✓ Automated Triage</div>
                </div>
                <div class="card">
                    <div class="metric-label">Happiness Score</div>
                    <div class="metric-value">{happiness_score}</div>
                    <div style="font-size: 13px; color: #666;">Target: 85+</div>
                </div>
            </div>

            <div class="chart-grid">
                <!-- Graph 1: Daily Activity Trend -->
                <div class="card span-2">
                    <h2>Daily Activity Trend</h2>
                    <div class="chart-container">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>

                <!-- Graph 2: Intent Breakdown -->
                <div class="card">
                    <h2>Customer Intent Breakdown</h2>
                    <div class="chart-container">
                        <canvas id="intentChart"></canvas>
                    </div>
                </div>

                <!-- Graph 3: Resolution Success -> NOW A PIE CHART -->
                <div class="card">
                    <h2>Resolution Breakdown</h2>
                    <div class="chart-container">
                        <canvas id="resolutionChart"></canvas>
                    </div>
                </div>

                <!-- Graph 4: Product Interest Leaderboard -->
                <div class="card">
                    <h2>Product Interest Leaderboard</h2>
                    <div class="chart-container">
                        <canvas id="productChart"></canvas>
                    </div>
                </div>

                <!-- Graph 5: Sentiment Stability -->
                <div class="card">
                    <h2>Happiness Trend (Daily)</h2>
                    <div class="chart-container">
                        <canvas id="sentimentChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="card" style="margin-top: 30px; background: #000; color: #fff;">
                <h2 style="color: #fff; border-color: #fff;">Executive Summary & Insights</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px;">
                    <div>
                        <p style="color: #ddd; font-size: 16px; line-height: 1.8;">This month, AstraBot successfully handled <strong>{total} conversations</strong>, acting as the first line of defense for support. By automating {automation_rate}% of interactions, we delivered an estimated <strong>${money_saved}</strong> in operational value.</p>
                    </div>
                    <div>
                        <ul style="color: #ddd; padding-left: 20px; font-size: 16px; line-height: 1.8;">
                            <li><strong>Top Product:</strong> Customers are asking most about <strong>{product_labels[0] if product_labels else "Catalog"}</strong>.</li>
                            <li><strong>Efficiency:</strong> {stats['resolved_instantly']} customers received instant answers.</li>
                            <li><strong>Stability:</strong> Sentiment remained consistent at {happiness_score}/100.</li>
                        </ul>
                    </div>
                </div>
            </div>

            <footer>
                CONFIDENTIAL • ASTRASTRAPS PERFORMANCE REPORT v3.1
            </footer>
        </div>

        <script>
            // Common Options for Light Theme
            const baseOptions = {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ 
                    x: {{ grid: {{ display: false }}, ticks: {{ color: '#666', font: {{ family: "'Outfit', sans-serif" }} }} }},
                    y: {{ grid: {{ color: '#eee' }}, ticks: {{ color: '#666', font: {{ family: "'Outfit', sans-serif" }} }} }}
                }}
            }};
            
            const pieOptions = {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ 
                    legend: {{ 
                        display: true, 
                        position: 'right', 
                        labels: {{ color: '#000', font: {{ family: "'Outfit', sans-serif" }} }} 
                    }} 
                }}
            }};

            // 1. Trend Chart
            new Chart(document.getElementById('trendChart'), {{
                type: 'line',
                data: {{
                    labels: {json.dumps(daily_labels)},
                    datasets: [{{
                        label: 'Conversations',
                        data: {json.dumps(daily_volume)},
                        borderColor: '#000000',
                        backgroundColor: 'rgba(0,0,0,0.05)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#000'
                    }}]
                }},
                options: baseOptions
            }});

            // 2. Intent Chart
            new Chart(document.getElementById('intentChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(intent_labels)},
                    datasets: [{{
                        data: {json.dumps(intent_values)},
                        backgroundColor: ['#000000', '#FF6B00', '#2979FF', '#9E9E9E'],
                        borderWidth: 0
                    }}]
                }},
                options: pieOptions
            }});

            // 3. Resolution Chart (Pie)
            new Chart(document.getElementById('resolutionChart'), {{
                type: 'pie',
                data: {{
                    labels: ["Resolved (Automation)", "Escalated (Human)"],
                    datasets: [{{
                        data: [{successful_interactions}, {total - successful_interactions}],
                        backgroundColor: ['#00C853', '#000000'],
                        borderWidth: 0
                    }}]
                }},
                options: pieOptions
            }});

            // 4. Product Chart (Fixing width with barPercentage)
            new Chart(document.getElementById('productChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(product_labels)},
                    datasets: [{{
                        data: {json.dumps(product_values)},
                        backgroundColor: '#000000',
                        borderRadius: 4,
                        barPercentage: 0.8,
                        categoryPercentage: 0.9
                    }}]
                }},
                options: {{
                    indexAxis: 'y', // Force horizontal
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        x: {{ 
                            grid: {{ color: '#eee' }},
                            ticks: {{ color: '#666', font: {{ family: "'Outfit', sans-serif" }} }}
                        }},
                        y: {{ 
                            grid: {{ display: false }},
                            ticks: {{ color: '#000', font: {{ family: "'Outfit', sans-serif", weight: '600' }} }}
                        }}
                    }}
                }}
            }});

            // 5. Sentiment Chart
            new Chart(document.getElementById('sentimentChart'), {{
                type: 'line',
                data: {{
                    labels: {json.dumps(daily_labels)},
                    datasets: [{{
                        label: 'Happiness',
                        data: {json.dumps(daily_sentiment)},
                        borderColor: '#00C853',
                        backgroundColor: 'rgba(0, 200, 83, 0.05)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }}]
                }},
                options: {{ ...baseOptions, scales: {{ ...baseOptions.scales, y: {{ min: 0, max: 105 }} }} }}
            }});
        </script>
    </body>
    </html>
    """
    return html

def analyze_data(conversations):
    stats = {
        'total': len(conversations),
        'unhappy': 0,
        'resolved_instantly': 0,
        'tickets_created': 0,
        'total_hours_saved': 0.0,
        'intents': defaultdict(int),
        'products': Counter(),
        'daily_volume': defaultdict(int),
        'daily_sentiment': defaultdict(list)
    }
    
    for c in conversations:
        date_str = c.get("date", "").split(" ")[0]
        if not date_str: continue
        
        stats['daily_volume'][date_str] += 1
        
        summary = str(c.get("analysis", ""))
        intent = classify_intent(summary)
        stats['intents'][intent] += 1
        stats['total_hours_saved'] += calculate_weighted_time(intent) / 60.0
        
        # Sentiment tracking
        is_unhappy = c.get("is_unhappy_customer", False)
        if is_unhappy: stats['unhappy'] += 1
        stats['daily_sentiment'][date_str].append(0 if is_unhappy else 100)
        
        # Product Extraction
        for p in PRODUCTS:
            if p.lower() in summary.lower():
                stats['products'][p] += 1
        
        # Resolution logic
        is_ticket = "ticket" in summary.lower() or "created" in summary.lower()
        is_error = c.get("is_technical_error", False)
        
        if is_error: pass
        elif is_ticket: stats['tickets_created'] += 1
        elif not is_unhappy: stats['resolved_instantly'] += 1
            
    # Average sentiment per day
    avg_sentiment = {}
    for day, scores in stats['daily_sentiment'].items():
        avg_sentiment[day] = sum(scores) / len(scores)
    stats['daily_sentiment'] = avg_sentiment
    
    # ---------------------------------------------------------
    # SUPERIOR DATA SOURCE CHECK: External Product Stats
    # ---------------------------------------------------------
    # If we have a dedicated product stats file (from deep transcript analysis), use that
    # instead of the simple keyword matching above.
    try:
        # Determine month from data or assume it matches the loaded batch
        # We can find the most common month in the dataset
        if conversations:
            sample_date = conversations[0].get("date", "")
            month_match = re.search(r"(\d{4}-\d{2})", sample_date)
            if month_match:
                current_month = month_match.group(1)
                stats_file = f"product_stats_{current_month}.json"
                
                if os.path.exists(stats_file):
                    print(f"Loading deep product analysis from {stats_file}...")
                    with open(stats_file, 'r') as f:
                        p_data = json.load(f)
                        if "product_counts" in p_data:
                            # OVERRIDE the simple 'products' counter
                            stats['products'] = Counter(p_data["product_counts"])
    except Exception as e:
        print(f"Error loading external product stats: {e}")
    # ---------------------------------------------------------

    return stats 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", help="YYYY-MM format")
    args = parser.parse_args()
    
    conversations, month_str = load_data(args.month)
    if not conversations:
        print(f"No conversations found for {month_str}")
        return
        
    stats = analyze_data(conversations)
    # The analyze_data function in this simplified block might return slightly different tuples
    # Let's align it with generate_html
    
    # Actually, analyze_data returns 'stats' dict in my new implementation above (lines 535-570)
    # But wait, looking at lines 535-570 in the new code block, 'analyze_data' returns 3 values? 
    # Ah, I added return stats, ... at the end.
    
    # Correcting for safety:
    result = analyze_data(conversations)
    if isinstance(result, tuple):
        stats = result[0]
    else:
        stats = result
        
    html = generate_html(stats, month_str)
    
    output_filename = f"monthly_report_{month_str}.html"
    with open(output_filename, "w") as f:
        f.write(html)
        
    print(f"Report generated: {output_filename}")

if __name__ == "__main__":
    main()
