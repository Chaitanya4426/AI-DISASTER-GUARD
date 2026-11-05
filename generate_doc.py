import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

doc = docx.Document()

# Set standard margins
for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

def add_custom_heading(text, level=1):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    run = h.add_run(text)
    run.bold = True
    run.font.name = 'Arial'
    if level == 1:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0, 51, 102)
    elif level == 2:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(30, 80, 150)
    return h

def add_code_block(code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    shading_xml = parse_xml(r'<w:shd {} w:fill="F4F6F9"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shading_xml)
    
    borders_xml = parse_xml(r'''
        <w:tcBorders {} >
            <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="0056B3"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
        </w:tcBorders>
    '''.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(borders_xml)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_text.strip())
    run.font.name = 'Consolas'
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# 1. Add Vignan banner
banner_path = r'C:\Users\Chaitanya\Desktop\mfef\vignan_banner.png'
if os.path.exists(banner_path):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(6)
    p_img.add_run().add_picture(banner_path, width=Inches(6.8))

# 2. Header info
p_course = doc.add_paragraph()
p_course.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_course.paragraph_format.space_after = Pt(12)
r_course = p_course.add_run('24CS810-Modern Front-End Frameworks and SPA Development')
r_course.bold = True
r_course.font.name = 'Arial'
r_course.font.size = Pt(11)

# Student Meta Block
meta_table = doc.add_table(rows=4, cols=2)
meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
meta_data = [
    ('NAME OF STUDENT:', ''),
    ('REGD NO:', ''),
    ('SECTION:', ''),
    ('PROJECT TITLE:', 'AI DisasterGuard: Intelligent Multi-Hazard Risk Monitoring & Operations Dashboard')
]
for i, (label, val) in enumerate(meta_data):
    cell_lbl, cell_val = meta_table.cell(i, 0), meta_table.cell(i, 1)
    cell_lbl.width = Inches(1.8)
    cell_val.width = Inches(5.0)
    p_l = cell_lbl.paragraphs[0]
    p_l.paragraph_format.space_before = Pt(2)
    p_l.paragraph_format.space_after = Pt(2)
    r_l = p_l.add_run(label)
    r_l.bold = True
    r_l.font.name = 'Arial'
    r_l.font.size = Pt(9.5)
    
    p_v = cell_val.paragraphs[0]
    p_v.paragraph_format.space_before = Pt(2)
    p_v.paragraph_format.space_after = Pt(2)
    r_v = p_v.add_run(val)
    r_v.font.name = 'Arial'
    r_v.font.size = Pt(9.5)

p_fac = doc.add_paragraph()
p_fac.alignment = WD_ALIGN_PARAGRAPH.RIGHT
p_fac.paragraph_format.space_before = Pt(18)
p_fac.paragraph_format.space_after = Pt(14)
r_fac = p_fac.add_run('FACULTY SIGNATURE                                                                       ')
r_fac.bold = True
r_fac.font.name = 'Arial'
r_fac.font.size = Pt(10)

# AIM
add_custom_heading('AIM:')
p_aim = doc.add_paragraph()
p_aim.paragraph_format.space_after = Pt(8)
r_aim = p_aim.add_run('To design and develop an AI-powered Disaster Risk Intelligence and Multi-Hazard Early Warning Operations System using Flask, HTML5, CSS3, JavaScript (Fetch API, Chart.js, Leaflet.js GIS), and SQLite/MySQL database to monitor real-time weather hazards, analyze hydrological risk parameters, predict disaster susceptibilities (floods, cyclones, landslides), visualize geospatial risk zones, and coordinate emergency advisories.')
r_aim.font.name = 'Arial'
r_aim.font.size = Pt(10)

# SOFTWARE REQUIREMENTS
add_custom_heading('SOFTWARE REQUIREMENTS:')
reqs = [
    ('Operating System', 'Windows 10/11'),
    ('Frontend', 'HTML5, CSS3 (Modern Flexbox/Grid), JavaScript (ES6+), Chart.js (Data Visualization), Leaflet.js (GIS Mapping), Font Awesome 6.5'),
    ('Backend', 'Python 3.x, Flask Web Framework (v3.1.0), Flask-SQLAlchemy (v3.1.1), Flask-Login (v0.6.3), Werkzeug (v3.1.3)'),
    ('Database', 'SQLite (instance/disasterguard.db) / MySQL compatible'),
    ('Data Analysis & ML', 'Pandas, NumPy, Scikit-Learn, Joblib'),
    ('External REST APIs', 'Open-Meteo Global Forecasting API'),
    ('Code Editor', 'Visual Studio Code'),
    ('Web Browser', 'Google Chrome / Microsoft Edge'),
    ('Package Manager', 'pip (Python Package Installer)'),
    ('API Testing Tool', 'Browser DevTools / Postman')
]
p_req = doc.add_paragraph()
p_req.paragraph_format.space_after = Pt(8)
for k, v in reqs:
    r_k = p_req.add_run(f'• {k}: ')
    r_k.bold = True
    r_k.font.name = 'Arial'
    r_k.font.size = Pt(9.5)
    r_v = p_req.add_run(f'{v}\n')
    r_v.font.name = 'Arial'
    r_v.font.size = Pt(9.5)

# OBJECTIVE
add_custom_heading('OBJECTIVE:')
p_obj = doc.add_paragraph()
p_obj.paragraph_format.space_after = Pt(8)
r_obj = p_obj.add_run('To create a responsive, modern web application providing an operational decision support dashboard for multi-hazard disaster monitoring (floods, cyclones, landslides, and extreme weather), allowing administrators and responders to track real-time weather conditions via Open-Meteo, execute hydrological risk prediction models, visualize mapped disaster locations on interactive GIS layers, manage evacuation readiness, and export standardized emergency assessment reports.')
r_obj.font.name = 'Arial'
r_obj.font.size = Pt(10)

# PROJECT STRUCTURE
add_custom_heading('PROJECT STRUCTURE')
tree_str = '''disasterguard-management/
├── app.py
├── requirements.txt
├── instance/
│   └── disasterguard.db
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── landing.html
    ├── login.html
    ├── register.html
    ├── map.html
    ├── module.html
    └── weather.html'''
add_code_block(tree_str)

# SOURCE CODE
add_custom_heading('SOURCE CODE:')
add_custom_heading('BACKEND', level=2)

p_fn1 = doc.add_paragraph()
p_fn1.paragraph_format.space_after = Pt(2)
r_fn1 = p_fn1.add_run('app.py (Flask Application, User Authentication & REST APIs)')
r_fn1.bold = True
r_fn1.font.name = 'Arial'
r_fn1.font.size = Pt(9.5)

code_backend = '''import os
from datetime import datetime
import requests
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("The SECRET_KEY environment variable must be set.")
app.config["SECRET_KEY"] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "disasterguard.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="registered_user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("landing.html", page_title="AI DisasterGuard")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", page_title="Disaster Dashboard")

@app.route("/api/dashboard-summary")
def dashboard_summary():
    alerts = [
        {"title": "Cyclone watch for coastal districts", "hazard": "Cyclone", "severity": "High", "time": "15 min ago"},
        {"title": "River level rising near Jamuna basin", "hazard": "Flood", "severity": "Moderate", "time": "42 min ago"},
        {"title": "Heavy rainfall advisory in hill tracts", "hazard": "Weather", "severity": "Warning", "time": "1 hr ago"},
    ]
    risk_locations = [
        {"name": "Sunamganj", "risk": "Critical", "lat": 25.07, "lng": 91.40},
        {"name": "Cox's Bazar", "risk": "High", "lat": 21.42, "lng": 91.98},
        {"name": "Khagrachhari", "risk": "Moderate", "lat": 23.10, "lng": 91.97},
    ]
    return jsonify({
        "status": "success",
        "alerts": alerts,
        "risk_locations": risk_locations,
        "active_alerts_count": len(alerts),
        "high_risk_count": 2
    })

@app.route("/api/predict/flood", methods=["POST"])
def predict_flood():
    data = request.get_json() or {}
    rainfall = float(data.get("rainfall_intensity", 58))
    accumulation = float(data.get("rainfall_accumulation", 126))
    river_level = float(data.get("river_water_level", 64))
    soil_moisture = float(data.get("soil_moisture", 74))
    elevation = float(data.get("elevation", 19))
    slope = float(data.get("slope", 23))
    
    score = (rainfall * 0.25) + (accumulation * 0.15) + (river_level * 0.3) + (soil_moisture * 0.2) - (elevation * 0.1)
    probability = min(max(int(score), 10), 98)
    risk_category = "Critical" if probability >= 80 else "High" if probability >= 60 else "Moderate"
    
    return jsonify({
        "flood_probability": probability,
        "risk_category": risk_category,
        "risk_explanation": f"Elevated river water level ({river_level}%) and saturated soil moisture ({soil_moisture}%) indicate significant runoff susceptibility.",
        "contributing_factors": ["High rainfall intensity", "Elevated river stage", "Saturated soil moisture"]
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)'''
add_code_block(code_backend)

# FRONTEND
add_custom_heading('FRONTEND SOURCE CODE', level=2)

p_fn2 = doc.add_paragraph()
p_fn2.paragraph_format.space_after = Pt(2)
r_fn2 = p_fn2.add_run('templates/dashboard.html (Operations Dashboard View)')
r_fn2.bold = True
r_fn2.font.name = 'Arial'
r_fn2.font.size = Pt(9.5)

code_dash = '''{% extends "base.html" %}

{% block content %}
<div class="page-header">
  <div>
    <span class="section-tag">Operations dashboard</span>
    <h2>Multi-hazard intelligence overview</h2>
  </div>
  <div class="page-header-actions">
    <span class="status-pill warning">Demo metrics</span>
    <button class="primary-btn small-btn" type="button" id="export-report"><i class="fa-solid fa-download"></i> Export report</button>
  </div>
</div>

<section class="stats-grid" id="dashboard-page">
  <div class="stat-card danger">
    <div class="stat-label">Active demo alerts</div>
    <div class="stat-value" id="stat-alerts">3</div>
    <div class="stat-trend">Records in the sample alert feed</div>
  </div>
  <div class="stat-card warning">
    <div class="stat-label">High-risk demo areas</div>
    <div class="stat-value" id="stat-risk-areas">2</div>
    <div class="stat-trend">High and critical mapped locations</div>
  </div>
  <div class="stat-card success">
    <div class="stat-label">Weather feed status</div>
    <div class="stat-value" id="stat-weather-stations">Connected</div>
    <div class="stat-trend">Open-Meteo connection status</div>
  </div>
</section>

<section class="chart-grid">
  <div class="panel-card">
    <div class="panel-head"><h3>Rainfall forecast</h3><span class="status-pill info">Open-Meteo</span></div>
    <div class="chart-frame"><canvas id="rainfallChart"></canvas></div>
  </div>
  <div class="panel-card">
    <div class="panel-head"><h3>Temperature forecast</h3><span class="status-pill info">Open-Meteo</span></div>
    <div class="chart-frame"><canvas id="temperatureChart"></canvas></div>
  </div>
  <div class="panel-card">
    <div class="panel-head"><h3>Alert count by hazard</h3><span class="status-pill warning">Demo feed</span></div>
    <div class="chart-frame"><canvas id="frequencyChart"></canvas></div>
  </div>
</section>

<section class="content-grid">
  <div class="panel-card wide" id="risk-panel">
    <div class="panel-head"><h3>Flood prediction model</h3><span class="status-pill warning">Assessment Engine</span></div>
    <form id="flood-form" class="prediction-form">
      <div class="field-grid">
        <label>Rainfall intensity (mm/h)<input type="number" name="rainfall_intensity" value="58" required /></label>
        <label>Rainfall accumulation (mm)<input type="number" name="rainfall_accumulation" value="126" required /></label>
        <label>River water level (%)<input type="number" name="river_water_level" value="64" required /></label>
        <label>Soil moisture (%)<input type="number" name="soil_moisture" value="74" required /></label>
        <label>Elevation (m)<input type="number" name="elevation" value="19" required /></label>
        <label>Slope (deg)<input type="number" name="slope" value="23" required /></label>
      </div>
      <button type="submit" class="primary-btn">Run prediction</button>
    </form>
    <div class="prediction-result" id="prediction-result">
      <div class="result-row"><span>Probability:</span><strong id="risk-probability">67%</strong></div>
      <div class="result-row"><span>Risk category:</span><strong id="risk-category">High</strong></div>
    </div>
  </div>
</section>
{% endblock %}'''
add_code_block(code_dash)

p_fn3 = doc.add_paragraph()
p_fn3.paragraph_format.space_after = Pt(2)
r_fn3 = p_fn3.add_run('static/css/style.css (Modern Design System & Layout)')
r_fn3.bold = True
r_fn3.font.name = 'Arial'
r_fn3.font.size = Pt(9.5)

code_css = ''':root {
  --bg-primary: #f8fafc;
  --bg-card: #ffffff;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --primary: #0056b3;
  --primary-hover: #004494;
  --danger: #ef4444;
  --warning: #f59e0b;
  --success: #10b981;
  --border: #e2e8f0;
  --radius: 12px;
  --shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
}

body {
  margin: 0;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-main);
}

.stats-grid, .chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card, .panel-card {
  background: var(--bg-card);
  padding: 1.25rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  margin: 0.5rem 0;
  color: var(--primary);
}

.primary-btn {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 0.65rem 1.25rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.primary-btn:hover {
  background: var(--primary-hover);
}'''
add_code_block(code_css)

p_fn4 = doc.add_paragraph()
p_fn4.paragraph_format.space_after = Pt(2)
r_fn4 = p_fn4.add_run('static/js/app.js (Dashboard Controller & Async Data Loading)')
r_fn4.bold = True
r_fn4.font.name = 'Arial'
r_fn4.font.size = Pt(9.5)

code_js = '''document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
  initFloodPrediction();
});

async function initDashboard() {
  try {
    const res = await fetch('/api/dashboard-summary');
    const data = await res.json();
    if (document.getElementById('stat-alerts')) {
      document.getElementById('stat-alerts').textContent = data.alerts.length;
    }
  } catch (err) {
    console.error('Failed to load dashboard summary', err);
  }
}

function initFloodPrediction() {
  const form = document.getElementById('flood-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());

    const response = await fetch('/api/predict/flood', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    document.getElementById('risk-probability').textContent = `${result.flood_probability}%`;
    document.getElementById('risk-category').textContent = result.risk_category;
  });
}'''
add_code_block(code_js)

# OUTPUTS
add_custom_heading('OUTPUTS')

p_out1_lbl = doc.add_paragraph()
p_out1_lbl.paragraph_format.space_before = Pt(6)
p_out1_lbl.paragraph_format.space_after = Pt(4)
r_out1_lbl = p_out1_lbl.add_run('Output 1: Operations Dashboard Overview with Forecasting Analytics & Hazard Charts (http://127.0.0.1:5000/dashboard)')
r_out1_lbl.bold = True
r_out1_lbl.font.name = 'Arial'
r_out1_lbl.font.size = Pt(10)

img1_path = r'C:\Users\Chaitanya\Desktop\mfef\dashboard_output_1.png'
if os.path.exists(img1_path):
    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_after = Pt(14)
    p_img1.add_run().add_picture(img1_path, width=Inches(6.8))

p_out2_lbl = doc.add_paragraph()
p_out2_lbl.paragraph_format.space_before = Pt(6)
p_out2_lbl.paragraph_format.space_after = Pt(4)
r_out2_lbl = p_out2_lbl.add_run('Output 2: Real-Time Weather Monitoring, Early Warning Alerts & Flood Prediction Model Execution (http://127.0.0.1:5000/dashboard)')
r_out2_lbl.bold = True
r_out2_lbl.font.name = 'Arial'
r_out2_lbl.font.size = Pt(10)

img2_path = r'C:\Users\Chaitanya\Desktop\mfef\dashboard_output_2.png'
if os.path.exists(img2_path):
    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_after = Pt(14)
    p_img2.add_run().add_picture(img2_path, width=Inches(6.8))

output_path = r'C:\Users\Chaitanya\Desktop\mfef\24CS810_AI_DisasterGuard_Lab_Report.docx'
doc.save(output_path)
print('Document generated successfully at:', output_path)
