from flask import Flask, render_template, request, jsonify
import pdfplumber, docx, re

app = Flask(__name__)

MIN_JOB_SKILLS = 5
MAX_ATS = 90

# ================= ROLE → DOMAIN → JD =================
ROLE_CONFIG = {

    # -------- TECH / CSE --------
    "software engineer": {
        "domain": "cse",
        "jd": "Software Engineer with skills in Python, Java or C++, SQL, GitHub, and problem solving."
    },
    "ai engineer": {
        "domain": "cse",
        "jd": "AI Engineer with experience in Python, Artificial Intelligence, Machine Learning, SQL, and data analysis."
    },
    "data analyst": {
        "domain": "cse",
        "jd": "Data Analyst with strong skills in Python, SQL, Excel, data analysis, and reporting."
    },

    # -------- FINANCE --------
    "financial analyst": {
        "domain": "finance",
        "jd": "Financial Analyst with knowledge of financial analysis, accounting, Excel, budgeting, and investment analysis."
    },
    "accounts executive": {
        "domain": "finance",
        "jd": "Accounts Executive with experience in accounting, bookkeeping, Tally ERP, GST, Excel, and financial reporting."
    },

    # -------- BUSINESS --------
    "business analyst": {
        "domain": "business",
        "jd": "Business Analyst with skills in business analysis, market research, Excel, reporting, and stakeholder communication."
    },

    # -------- MARKETING --------
    "digital marketing executive": {
        "domain": "marketing",
        "jd": "Digital Marketing Executive with experience in SEO, social media marketing, content creation, campaign analysis, and analytics tools."
    },

    # -------- HR --------
    "hr executive": {
        "domain": "hr",
        "jd": "HR Executive with experience in recruitment, onboarding, employee engagement, payroll coordination, and HR operations."
    },

    # -------- OPERATIONS --------
    "operations executive": {
        "domain": "operations",
        "jd": "Operations Executive responsible for process coordination, reporting, operational efficiency, and cross-team support."
    }
}

# ================= DOMAIN SKILLS =================
DOMAIN_SKILLS = {
    "cse": [
        "python", "java", "c", "c++", "sql",
        "machine learning", "data analysis",
        "excel", "github", "html", "css", "javascript"
    ],
    "finance": [
        "finance", "financial", "accounting",
        "excel", "budgeting", "investment",
        "gst", "tally", "reporting"
    ],
    "business": [
        "business analysis", "market research",
        "sales", "management", "reporting"
    ],
    "marketing": [
        "seo", "digital marketing", "social media",
        "content", "campaign", "analytics", "branding"
    ],
    "hr": [
        "recruitment", "hr", "human resources",
        "payroll", "onboarding", "employee engagement"
    ],
    "operations": [
        "operations", "process", "coordination",
        "logistics", "reporting", "efficiency"
    ]
}

# ================= SKILL WEIGHTS =================
CORE_SKILLS = {
    "python": 3,
    "sql": 3,
    "data analysis": 3
}

SECONDARY_SKILLS = {
    "excel": 1,
    "github": 1,
    "machine learning": 1
}

# ================= UTIL FUNCTIONS =================
def extract_text(file):
    text = ""

    if file.filename.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + " "

    elif file.filename.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + " "

    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def detect_domain(text):
    scores = {}
    for domain, skills in DOMAIN_SKILLS.items():
        scores[domain] = sum(1 for skill in skills if skill in text)

    best_domain = max(scores, key=scores.get)
    return best_domain if scores[best_domain] > 0 else "general"


def section_score(text, keywords):
    found = sum(1 for k in keywords if k in text)
    return int((found / len(keywords)) * 100) if keywords else 0


# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/auto-jd", methods=["POST"])
def auto_jd():
    role = request.json.get("role", "").strip().lower()

    if role in ROLE_CONFIG:
        return jsonify({
            "job_description": ROLE_CONFIG[role]["jd"],
            "domain": ROLE_CONFIG[role]["domain"]
        })

    # Fallback (should not happen if dropdown matches)
    return jsonify({
        "job_description": "General role requiring relevant skills and domain knowledge.",
        "domain": "general"
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    resume = request.files["resume"]
    job_desc = request.form["job_description"].lower()

    resume_text = extract_text(resume)
    combined_text = resume_text + " " + job_desc

    domain = detect_domain(combined_text)
    skills_db = DOMAIN_SKILLS.get(domain, [])

    # ================= SKILL MATCHING =================
    resume_skills = [s for s in skills_db if s in resume_text]
    job_skills = [s for s in skills_db if s in job_desc]

    matched = list(set(resume_skills) & set(job_skills))
    missing = list(set(job_skills) - set(resume_skills))

    # ================= ATS SCORE =================
    score = 0
    max_score = sum(CORE_SKILLS.values()) + sum(SECONDARY_SKILLS.values())

    for skill, weight in CORE_SKILLS.items():
        if skill in resume_text and skill in job_desc:
            score += weight

    for skill, weight in SECONDARY_SKILLS.items():
        if skill in resume_text and skill in job_desc:
            score += weight

    ats = int((score / max_score) * 100)
    ats = min(ats, MAX_ATS)

    # ================= ROLE FIT =================
    if ats >= 75:
        fit = "Excellent"
    elif ats >= 60:
        fit = "Good"
    elif ats >= 40:
        fit = "Average"
    else:
        fit = "Poor"

    # ================= SECTION ANALYSIS =================
    section_scores = {
        "Skills": section_score(resume_text, skills_db),
        "Projects": section_score(resume_text, ["project", "analysis", "dataset", "model"]),
        "Experience": section_score(resume_text, ["intern", "experience", "company"]),
        "Education": section_score(resume_text, ["b.e", "b.tech", "degree", "university"])
    }

    # ================= RESPONSE =================
    return jsonify({
        "Domain": domain.upper(),
        "ATS_Score": f"{ats}%",
        "Role_Fit": fit,
        "Matched_Skills": matched,
        "Missing_Skills": missing,
        "Section_Analysis": section_scores,
        "Skill_Gap_Overview": {
            "Matched": len(matched),
            "Missing": len(missing)
        },
        "Interview_Tips": [
            f"Add project experience in {s}" for s in missing[:3]
        ]
    })


if __name__ == "__main__":
    app.run(debug=True)
