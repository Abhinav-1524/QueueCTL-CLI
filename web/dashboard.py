from flask import Flask, render_template_string
from core.storage import Database
from datetime import datetime

app = Flask(__name__)
db = Database()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QueueCTL Dashboard</title>

<style>
:root {
    --bg: #0e1117;
    --card-bg: rgba(255, 255, 255, 0.05);
    --text: #e0e6ed;
    --muted: #a3a9b3;
    --accent: #3b82f6;
    --border: rgba(255, 255, 255, 0.08);
    --shadow: rgba(0, 0, 0, 0.3);
    --radius: 14px;

    --pending: #facc15;
    --processing: #38bdf8;
    --completed: #22c55e;
    --failed: #ef4444;
    --dead: #a855f7;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background: var(--bg);
    color: var(--text);
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
    padding: 32px;
    overflow-x: hidden;
}

h1 {
    font-size: 1.8rem;
    font-weight: 600;
    color: white;
    letter-spacing: -0.5px;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.timestamp {
    font-size: 0.9rem;
    color: var(--muted);
}

button.refresh {
    background: var(--accent);
    border: none;
    color: white;
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s ease;
}
button.refresh:hover {
    background: #2563eb;
}

.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    backdrop-filter: blur(12px);
    border-radius: var(--radius);
    padding: 20px;
    box-shadow: 0 4px 8px var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 16px var(--shadow);
}

.card h3 {
    font-size: 0.9rem;
    text-transform: uppercase;
    color: var(--muted);
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}
.card span {
    font-size: 1.8rem;
    font-weight: 600;
}

.table-wrapper {
    background: var(--card-bg);
    border: 1px solid var(--border);
    backdrop-filter: blur(12px);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 4px 8px var(--shadow);
}

table {
    width: 100%;
    border-collapse: collapse;
    color: var(--text);
    font-size: 0.9rem;
}

th, td {
    text-align: left;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
}
th {
    background: rgba(255, 255, 255, 0.05);
    font-weight: 500;
    color: #aab0bb;
    text-transform: uppercase;
    font-size: 0.75rem;
}
tr:hover td {
    background: rgba(255, 255, 255, 0.04);
}

.status-pill {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: capitalize;
}
.status-pending { background: var(--pending); color: #111; }
.status-processing { background: var(--processing); color: #fff; }
.status-completed { background: var(--completed); color: #fff; }
.status-failed { background: var(--failed); color: #fff; }
.status-dead { background: var(--dead); color: #fff; }

footer {
    text-align: center;
    margin-top: 2rem;
    color: var(--muted);
    font-size: 0.85rem;
}

.fade-in {
    animation: fadeIn 0.5s ease forwards;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
</head>
<body>

<div class="topbar">
    <h1>QueueCTL Monitor</h1>
    <div class="timestamp">
        <span>{{ now }}</span>
        <button class="refresh" onclick="location.reload()">Refresh</button>
    </div>
</div>

<div class="stats fade-in">
    {% for state, count in summary.items() %}
    <div class="card" style="border-top: 4px solid var(--{{ state }})">
        <h3>{{ state.capitalize() }}</h3>
        <span>{{ count }}</span>
    </div>
    {% endfor %}
</div>

<div class="table-wrapper fade-in">
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Command</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Attempts</th>
                <th>Created</th>
                <th>Updated</th>
            </tr>
        </thead>
        <tbody>
            {% for job in jobs %}
            <tr>
                <td>{{ job['id'] }}</td>
                <td style="color: var(--muted)">{{ job['command'] }}</td>
                <td><span class="status-pill status-{{ job['status'] }}">{{ job['status'] }}</span></td>
                <td>{{ job['priority'] }}</td>
                <td>{{ job['attempts'] }}</td>
                <td>{{ job['created_at'] }}</td>
                <td>{{ job['updated_at'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<footer>
    QueueCTL &nbsp;•&nbsp; Updated at {{ now }} (UTC)
</footer>

</body>
</html>
"""

@app.route("/")
def dashboard():
    summary = db.summary()
    cur = db.con.cursor()
    cur.execute("""
        SELECT * FROM jobs
        ORDER BY datetime(created_at) DESC
        LIMIT 20;
    """)
    jobs = cur.fetchall()
    return render_template_string(
        HTML_TEMPLATE,
        summary=summary,
        jobs=jobs,
        now=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


if __name__ == "__main__":
    print(" QueueCTL Dashboard available at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
