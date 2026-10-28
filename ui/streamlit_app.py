
import html
import json
import os

import requests
import streamlit as st


# =========================================================
# CONFIGURATION
# =========================================================
API_BASE_URL = os.getenv(
    "CAREER_COPILOT_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")
MAX_RESUME_SIZE = 5 * 1024 * 1024
REQUEST_TIMEOUT = 300
CONNECT_TIMEOUT = 5


st.set_page_config(
    page_title="Career Copilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SESSION STATE
# =========================================================
DEFAULTS = {
    "career_report": None,
    "career_request": None,
    "candidate_id": 1,
    "candidate_id_input": 1,
    "uploaded_profile": None,
    "upload_success": "",
    "upload_file_name": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CUSTOM UI THEME
# =========================================================
st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {
        --bg: #0b1020;
        --panel: #11182b;
        --border: #26324b;
        --text: #f1f5f9;
        --muted: #9aa9c4;
        --purple: #a78bfa;
        --cyan: #67e8f9;
        --green: #86efac;
    }

    .stApp {
        background:
          radial-gradient(ellipse at 5% 0%, #201b48 0%, transparent 32%),
          radial-gradient(ellipse at 95% 10%, #102b43 0%, transparent 30%),
          var(--bg);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(11,16,32,.7);
    }

    [data-testid="stSidebar"] {
        background: #0d1425;
        border-right: 1px solid var(--border);
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        letter-spacing: -.5px;
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
    }

    .brand-icon {
        width: 46px;
        height: 46px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        color: white;
        font-size: 25px;
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        box-shadow: 0 8px 25px rgba(124,58,237,.25);
    }

    .brand-name {
        color: #fff;
        font-size: 17px;
        font-weight: 800;
        letter-spacing: 1px;
    }

    .brand-subtitle {
        color: var(--muted);
        font-size: 10px;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }

    .hero {
        border: 1px solid #34315c;
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 25px;
        background:
          radial-gradient(circle at 90% 0%, #373078 0%, transparent 35%),
          linear-gradient(120deg, #17152f, #101b31 70%, #102638);
    }

    .eyebrow {
        display: inline-block;
        border: 1px solid #51438c;
        background: rgba(124,58,237,.15);
        color: #c4b5fd;
        padding: 7px 12px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 17px;
    }

    .hero h1 {
        font-size: clamp(30px, 4vw, 46px);
        line-height: 1.15;
        color: white;
        font-weight: 800;
        margin: 0 0 15px 0;
    }

    .gradient-text {
        background: linear-gradient(90deg, #c4b5fd, #67e8f9);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero p {
        max-width: 680px;
        color: #b4c1d8;
        line-height: 1.8;
        font-size: 14px;
        margin-bottom: 0;
    }

    .section-label {
        color: #9aa9c4;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.7px;
        text-transform: uppercase;
        margin: 25px 0 12px;
    }

    .kpi-card {
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 19px;
        min-height: 125px;
        background: linear-gradient(145deg, #141e33, #101727);
    }

    .kpi-label {
        color: var(--muted);
        font-size: 11px;
        font-weight: 600;
    }

    .kpi-value {
        color: white;
        font-size: 28px;
        font-weight: 800;
        margin: 10px 0 5px;
        overflow-wrap: anywhere;
    }

    .kpi-foot {
        color: #91a1bb;
        font-size: 11px;
    }

    .job-card {
        border: 1px solid var(--border);
        border-radius: 17px;
        background: linear-gradient(140deg, #141e32, #101727);
        padding: 20px;
        margin-bottom: 12px;
    }

    .job-top {
        display: flex;
        align-items: flex-start;
        gap: 13px;
    }

    .company-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        height: 44px;
        border-radius: 12px;
        background: linear-gradient(135deg, #30245e, #173750);
        color: #c4b5fd;
        font-size: 17px;
        font-weight: 800;
    }

    .job-title {
        color: #f8fafc;
        font-size: 16px;
        font-weight: 700;
        line-height: 1.5;
    }

    .company-name {
        color: #b3bfd3;
        font-size: 12px;
        margin-top: 4px;
    }

    .match-pill {
        border: 1px solid #3a6757;
        background: #142d2a;
        color: #86efac;
        border-radius: 10px;
        padding: 8px 10px;
        text-align: center;
        font-size: 12px;
        font-weight: 800;
        white-space: nowrap;
    }

    .job-meta {
        color: #a7b5cc;
        font-size: 12px;
        margin-top: 14px;
        line-height: 1.8;
    }

    .skill-chip {
        display: inline-block;
        color: #c4b5fd;
        border: 1px solid #43376b;
        background: #211d3d;
        border-radius: 7px;
        font-size: 11px;
        padding: 5px 8px;
        margin: 4px 4px 0 0;
    }

    .skill-chip.missing {
        color: #fbbf9b;
        border-color: #6b4335;
        background: #32221f;
    }

    .empty-state {
        border: 1px dashed #34415c;
        border-radius: 17px;
        padding: 30px;
        text-align: center;
        color: #aab7cd;
        background: rgba(17,24,43,.6);
    }

    .review-banner {
        border: 1px solid #3a6757;
        border-radius: 13px;
        background: #142d2a;
        color: #a7f3d0;
        padding: 16px;
        margin-bottom: 14px;
    }

    .review-warning {
        border: 1px solid #77532e;
        border-radius: 13px;
        background: #30251b;
        color: #fcd6a0;
        padding: 16px;
        margin-bottom: 14px;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        min-height: 42px;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(100deg, #7c3aed, #4f46e5);
        border: none;
        color: white;
    }

    div[data-testid="stMetric"] {
        border: 1px solid var(--border);
        background: #11182b;
        border-radius: 13px;
        padding: 14px;
    }

    .footer {
        border-top: 1px solid var(--border);
        margin-top: 35px;
        padding-top: 18px;
        color: #71819e;
        font-size: 11px;
        text-align: center;
        line-height: 1.8;
    }

    @media (max-width: 700px) {
        .hero { padding: 22px; }
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .job-top { flex-wrap: wrap; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================
@st.cache_data(ttl=15, show_spinner=False)
def check_api_status():
    """Check whether the FastAPI service is reachable."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/openapi.json",
            timeout=CONNECT_TIMEOUT,
        )
        response.raise_for_status()
        return True, "Backend connected"
    except requests.exceptions.RequestException:
        return False, "Backend unavailable"


def safe_text(value):
    return html.escape(str(value or ""))


def render_kpi(label, value, footnote):
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{safe_text(label)}</div>
          <div class="kpi-value">{safe_text(value)}</div>
          <div class="kpi-foot">{safe_text(footnote)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_list(items, empty_message):
    if not items:
        st.caption(empty_message)
        return

    for item in items:
        st.markdown(f"- {item}")


def render_job_card(job, rank):
    try:
        score = float(job.get("match_score", 0) or 0)
    except (TypeError, ValueError):
        score = 0.0

    title = safe_text(job.get("title", "Untitled role"))
    company = safe_text(job.get("company", "Unknown company"))
    location = safe_text(job.get("location") or "Not specified")
    source = safe_text(job.get("source", "Job provider"))

    matched = job.get("matched_skills") or []
    missing = job.get("missing_skills") or []

    matched_html = " ".join(
    f'<span class="skill-chip">{safe_text(skill)}</span>'
    for skill in matched[:8]
)

    missing_html = " ".join(
        f'<span class="skill-chip missing">{safe_text(skill)}</span>'
        for skill in missing[:8]
    )

    st.markdown(
        f"""
        <div class="job-card">
          <div class="job-top">
            <div class="company-icon">{rank:02}</div>
            <div style="flex:1;min-width:120px">
              <div class="job-title">{title}</div>
              <div class="company-name">{company}</div>
            </div>
            <div class="match-pill">{score:.0f} match points</div>
          </div>
          <div class="job-meta">
            📍 {location} &nbsp; · &nbsp; Source: {source}
          </div>
          <div style="margin-top:13px;color:#9aa9c4;font-size:11px">
            MATCHED SKILLS
          </div>
          <div>{matched_html or '<span style="color:#9aa9c4;font-size:12px">No skills detected</span>'}</div>
          <div style="margin-top:12px;color:#9aa9c4;font-size:11px">
            REQUIREMENTS NOT MATCHED
          </div>
          <div>{missing_html or '<span style="color:#9aa9c4;font-size:12px">None identified by the current detector</span>'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    url = job.get("job_url")
    if isinstance(url, str) and url.startswith("https://"):
        st.markdown(f"[↗ View original job posting]({url})")

    coverage = job.get("skill_coverage_percent")
    if coverage is not None:
        try:
            coverage = max(0.0, min(100.0, float(coverage)))
        except (TypeError, ValueError):
            coverage = None

        if coverage is not None:
            st.progress(
                coverage / 100,
                text=f"Detected skill coverage: {coverage:.0f}%",
            )


def upload_resume(file_bytes, file_name, mime_type):
    """Upload a resume to the existing FastAPI endpoint."""
    return requests.post(
        f"{API_BASE_URL}/api/resumes/upload",
        files={
            "file": (
                file_name,
                file_bytes,
                mime_type or "application/octet-stream",
            )
        },
        timeout=180,
    )


def extract_candidate_id(upload_data):
    """Support common flat and nested response shapes."""
    candidate = upload_data.get("candidate") or {}
    return (
        upload_data.get("candidate_id")
        or candidate.get("id")
    )


def extract_profile(upload_data):
    candidate = upload_data.get("candidate") or {}
    return (
        upload_data.get("profile")
        or upload_data.get("extracted_profile")
        or upload_data.get("candidate_profile")
        or candidate
    )


# =========================================================
# SIDEBAR — BRAND AND RESUME UPLOAD
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
          <div class="brand-icon">✦</div>
          <div>
            <div class="brand-name">Career Copilot</div>
            <div class="brand-subtitle">CAREER INTELLIGENCE</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # RESUME UPLOAD
    # -----------------------------------------------------
    st.markdown("### 📄 Resume Studio")
    st.caption("Upload a resume to create or update your candidate profile.")

    uploaded_resume = st.file_uploader(
        "Choose your resume",
        type=["pdf", "docx"],
        key="resume_uploader",
        help="PDF or DOCX, maximum 5 MB.",
    )

    if st.button(
        "✦ Upload & Analyze Resume",
        type="secondary",
        use_container_width=True,
        disabled=uploaded_resume is None,
    ):
        if uploaded_resume is not None:
            file_bytes = uploaded_resume.getvalue()

            if len(file_bytes) > MAX_RESUME_SIZE:
                st.error("The resume exceeds the 5 MB limit.")
            else:
                try:
                    with st.spinner(
                        "Extracting resume details and building your profile..."
                    ):
                        response = upload_resume(
                            file_bytes,
                            uploaded_resume.name,
                            uploaded_resume.type,
                        )
                        response.raise_for_status()
                        upload_data = response.json()

                    new_candidate_id = extract_candidate_id(upload_data)

                    if new_candidate_id is None:
                        st.error(
                            "The upload endpoint did not return a candidate ID. "
                            "Check the response schema of POST /api/resumes/upload."
                        )
                    else:
                        new_candidate_id = int(new_candidate_id)

                        st.session_state["candidate_id"] = new_candidate_id
                        st.session_state["candidate_id_input"] = new_candidate_id
                        st.session_state["uploaded_profile"] = extract_profile(
                            upload_data
                        )
                        st.session_state["upload_file_name"] = (
                            uploaded_resume.name
                        )
                        st.session_state["upload_success"] = (
                            f"Resume analyzed successfully. "
                            f"Candidate ID: {new_candidate_id}"
                        )

                        # Clear any stale report belonging to a previous run.
                        st.session_state["career_report"] = None
                        st.session_state["career_request"] = None

                        st.rerun()

                except requests.exceptions.HTTPError as exc:
                    try:
                        detail = response.json().get("detail", str(exc))
                    except ValueError:
                        detail = str(exc)

                    st.error(f"Resume upload failed: {detail}")

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Cannot connect to FastAPI. Start the backend first."
                    )

                except requests.exceptions.Timeout:
                    st.error(
                        "Resume analysis timed out. Check FastAPI logs "
                        "before attempting another upload."
                    )

                except (
                    requests.exceptions.RequestException,
                    ValueError,
                ) as exc:
                    st.error(f"Could not process the upload response: {exc}")

    if st.session_state.get("upload_success"):
        st.success(st.session_state["upload_success"])

    profile = st.session_state.get("uploaded_profile") or {}

    if profile:
        with st.expander("View extracted profile"):
            st.json(profile)

    st.divider()

    # -----------------------------------------------------
    # CAREER SEARCH FORM
    # -----------------------------------------------------
    st.markdown("### 🎯 Career Search")
    st.caption("Configure the jobs you want to discover.")

    with st.form("career_search_form"):
        candidate_id = st.number_input(
            "Candidate ID",
            min_value=1,
            value=int(st.session_state.get("candidate_id", 1)),
            step=1,
            key="candidate_id_input",
        )

        search = st.text_input(
            "Target job title",
            value="data scientist",
            placeholder="e.g. AI Engineer",
        )

        category = st.text_input(
            "Job category (optional)",
            value="",
            placeholder="e.g. Software Development",
        )

        discovery_limit = st.select_slider(
            "Live listings to fetch",
            options=[5, 10, 15, 20],
            value=5,
        )

        matching_limit = st.select_slider(
            "Saved jobs to evaluate",
            options=[5, 10, 20, 30, 50],
            value=10,
        )

        submitted = st.form_submit_button(
            "🚀 Run Career Copilot",
            type="primary",
            use_container_width=True,
        )

    st.divider()

    st.markdown("#### Multi-agent workflow")
    st.markdown("`01`  Job Discovery MCP")
    st.markdown("`02`  PostgreSQL Persistence")
    st.markdown("`03`  Job Matching")
    st.markdown("`04`  Resume Optimization")
    st.markdown("`05`  Quality Review")

    st.divider()

    api_online, api_message = check_api_status()
    if api_online:
        st.success(f"● {api_message}", icon="🟢")
    else:
        st.warning(
            f"● {api_message}. Start FastAPI before running the workflow.",
            icon="⚠️",
        )

    st.caption("LangGraph · Groq · MCP · PostgreSQL · FastAPI")

    if st.button("Clear displayed results", use_container_width=True):
        st.session_state["career_report"] = None
        st.session_state["career_request"] = None
        st.rerun()


# =========================================================
# HERO SECTION
# =========================================================
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">✦ YOUR AI CAREER WORKSPACE</div>
      <h1>
        Find your next opportunity.<br>
        <span class="gradient-text">Showcase your potential.</span>
      </h1>
      <p>
        Discover live jobs, evaluate your skill alignment, and generate
        evidence-based resume recommendations with a coordinated
        multi-agent AI workflow.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CANDIDATE PROFILE
# =========================================================
profile = st.session_state.get("uploaded_profile") or {}

if profile:
    st.markdown(
        '<div class="section-label">YOUR CANDIDATE PROFILE</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        left, right = st.columns([1, 2])

        with left:
            st.markdown("#### Candidate")
            st.write(profile.get("full_name") or "Name not detected")
            st.caption(profile.get("email") or "Email not detected")
            st.caption(
                f"Candidate ID: {st.session_state.get('candidate_id')}"
            )

        with right:
            st.markdown("#### Career summary")

            target_role = profile.get("target_role")
            experience = profile.get("experience_years")
            skills = profile.get("skills") or []

            if target_role:
                st.write(f"**Target role:** {target_role}")

            if experience is not None:
                st.write(f"**Experience:** {experience} years")

            st.write(
                "**Skills:** "
                + (", ".join(map(str, skills)) if skills else "Not detected")
            )

            st.caption(
                "Review these extracted details for accuracy before "
                "relying on job matches and resume recommendations."
            )


# =========================================================
# OVERVIEW CARDS
# =========================================================
st.markdown(
    '<div class="section-label">CAREER INTELLIGENCE OVERVIEW</div>',
    unsafe_allow_html=True,
)

overview_cols = st.columns(3)

overview_items = [
    ("01", "Live job discovery", "Real listings retrieved through MCP"),
    ("02", "Skill-based matching", "Transparent heuristic ranking"),
    ("03", "Resume quality review", "Recommendations flagged for verification"),
]

for col, (number, heading, description) in zip(
    overview_cols, overview_items
):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card" style="min-height:110px">
              <div style="color:#a78bfa;font-size:11px;font-weight:800">
                MODULE {number}
              </div>
              <div style="color:#fff;font-size:15px;font-weight:700;margin-top:12px">
                {heading}
              </div>
              <div class="kpi-foot" style="margin-top:7px">
                {description}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# EXECUTE CAREER COPILOT
# =========================================================
if submitted:
    if not search.strip():
        st.error("Please enter a target job title.")
    else:
        payload = {
            "candidate_id": int(candidate_id),
            "search": search.strip(),
            "category": category.strip(),
            "discovery_limit": int(discovery_limit),
            "matching_limit": int(matching_limit),
        }

        with st.spinner(
            "Coordinating job discovery, matching, resume optimization, "
            "and quality review..."
        ):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/career-copilot/run",
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                report = data.get("report")

                if not isinstance(report, dict):
                    st.error(
                        "The API response did not contain a valid report."
                    )
                else:
                    st.session_state["career_report"] = report
                    st.session_state["career_request"] = payload

            except requests.exceptions.Timeout:
                st.error(
                    "The request timed out. Check the FastAPI terminal "
                    "before retrying to avoid duplicate work."
                )

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to FastAPI. Start the backend using "
                    "`uvicorn app.main:app --reload`."
                )

            except requests.exceptions.HTTPError as exc:
                try:
                    detail = response.json().get("detail", str(exc))
                except ValueError:
                    detail = str(exc)

                st.error(f"Backend request failed: {detail}")

            except (
                requests.exceptions.RequestException,
                ValueError,
            ) as exc:
                st.error(f"Could not retrieve a valid API response: {exc}")


# =========================================================
# RESULTS DASHBOARD
# =========================================================
report = st.session_state.get("career_report")
request_info = st.session_state.get("career_request")

if report is not None:
    discovery = report.get("discovery", {})
    matching = report.get("job_matching", {})
    suggestions = report.get("resume_optimization", {})
    review = report.get("quality_review", {})
    matches = matching.get("matches", [])
    errors = report.get("errors", [])

    st.markdown(
        '<div class="section-label">YOUR CAREER REPORT</div>',
        unsafe_allow_html=True,
    )

    if request_info:
        st.caption(
            f"Search: **{request_info['search']}** · "
            f"Candidate ID: **{request_info['candidate_id']}**"
        )

    top_score = (
        matches[0].get("match_score", 0)
        if matches
        else None
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        render_kpi(
            "LIVE JOBS DISCOVERED",
            discovery.get("jobs_discovered", 0),
            "Listings returned by provider",
        )

    with k2:
        render_kpi(
            "JOBS EVALUATED",
            matching.get("jobs_evaluated", len(matches)),
            "Saved jobs evaluated",
        )

    with k3:
        render_kpi(
            "TOP MATCH SCORE",
            f"{top_score:.0f}" if top_score is not None else "N/A",
            "Heuristic points, not hiring probability",
        )

    with k4:
        render_kpi(
            "QUALITY REVIEW",
            review.get("status", "Skipped"),
            (
                f"Score: {review.get('quality_score', 'N/A')}/100"
                if review
                else "No review available"
            ),
        )

    if errors:
        with st.expander("Workflow warnings and errors", expanded=True):
            for error in errors:
                st.warning(error)

    st.write("")

    tab_jobs, tab_resume, tab_review, tab_details = st.tabs(
        [
            "✦ Job Matches",
            "▤ Resume Studio",
            "◈ Quality Review",
            "⌘ Workflow Details",
        ]
    )

    # -----------------------------------------------------
    # JOB MATCHES
    # -----------------------------------------------------
    with tab_jobs:
        st.subheader("Opportunities for you")
        st.caption(
            "Review the original job descriptions before applying. "
            "Scores are ranking signals, not hiring odds."
        )

        if matches:
            render_job_card(matches[0], 1)

            if len(matches) > 1:
                with st.expander(
                    f"View {len(matches) - 1} additional job matches"
                ):
                    for index, job in enumerate(matches[1:], start=2):
                        render_job_card(job, index)
        else:
            st.markdown(
                """
                <div class="empty-state">
                  <h3>No ranked matches yet</h3>
                  <p>
                    Try a different search or verify that the candidate
                    profile and saved jobs exist in PostgreSQL.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.caption(
            "The current skill detector has a limited vocabulary. "
            "A low score does not necessarily mean you are unqualified."
        )

    # -----------------------------------------------------
    # RESUME STUDIO
    # -----------------------------------------------------
    with tab_resume:
        st.subheader("Resume Studio")

        if suggestions:
            st.markdown("#### Target role")
            st.write(suggestions.get("job_target", "Not specified"))

            st.markdown("#### AI assessment")
            st.write(
                suggestions.get(
                    "overall_assessment",
                    "No assessment returned.",
                )
            )

            left, right = st.columns(2)

            with left:
                st.markdown("#### Supported skills")
                show_list(
                    suggestions.get("supported_matching_skills", []),
                    "No supported skills were returned.",
                )

            with right:
                st.markdown("#### Requirements not evidenced")
                show_list(
                    suggestions.get("requirements_not_evidenced", []),
                    "No unevidenced requirements were returned.",
                )

            st.divider()
            st.markdown("#### Improvement plan")

            for index, item in enumerate(
                suggestions.get("improvement_suggestions", []),
                start=1,
            ):
                st.markdown(f"**{index}.** {item}")

            st.divider()
            st.markdown("#### Suggested resume bullets")

            bullets = suggestions.get("rewritten_bullets", [])

            if bullets:
                for index, bullet in enumerate(bullets, start=1):
                    with st.container(border=True):
                        st.caption(f"EDIT {index}")
                        st.markdown("**Original evidence**")
                        st.write(bullet.get("original_evidence", ""))
                        st.markdown("**Suggested wording**")
                        st.write(bullet.get("suggested_bullet", ""))
            else:
                st.info("No rewritten bullets were generated.")

            st.warning(
                suggestions.get(
                    "verification_note",
                    "Verify every edit against the original resume.",
                )
            )
        else:
            st.info(
                "Resume optimization was not completed. Check the selected "
                "job match and workflow errors."
            )

    # -----------------------------------------------------
    # QUALITY REVIEW
    # -----------------------------------------------------
    with tab_review:
        st.subheader("Quality & Trust Review")

        if review:
            status = review.get("status", "NEEDS_REVIEW")

            if status == "PASS":
                st.markdown(
                    """
                    <div class="review-banner">
                      <b>Review status: PASS</b><br>
                      Verify all claims against the original resume before use.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="review-warning">
                      <b>Review status: NEEDS REVIEW</b><br>
                      Check the flagged issues before using these suggestions.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            score = review.get("quality_score", 0)
            try:
                score = max(0, min(100, float(score)))
            except (TypeError, ValueError):
                score = 0

            st.progress(
                score / 100,
                text=f"LLM quality score: {score:.0f}/100",
            )

            st.markdown("#### Issues identified")
            show_list(
                review.get("issues", []),
                "No issues were returned.",
            )

            st.markdown("#### Claims requiring verification")
            show_list(
                review.get("unsupported_claims_to_verify", []),
                "No claims were specifically flagged.",
            )

            st.markdown("#### Reviewer recommendations")
            show_list(
                review.get("recommendations", []),
                "No recommendations were returned.",
            )

            st.info(
                "An AI quality score is not proof of factual accuracy."
            )
        else:
            st.info("No quality review is available.")

    # -----------------------------------------------------
    # WORKFLOW DETAILS
    # -----------------------------------------------------
    with tab_details:
        st.subheader("Workflow Execution")

        persistence = discovery.get("persistence", {})

        p1, p2, p3 = st.columns(3)

        p1.metric("Jobs inserted", persistence.get("inserted", 0))
        p2.metric("Jobs updated", persistence.get("updated", 0))
        p3.metric(
            "Jobs processed",
            persistence.get("total_processed", 0),
        )

        st.markdown("#### LangGraph pipeline")

        st.code(
            "Job Discovery MCP\n"
            "       ↓\n"
            "PostgreSQL Persistence\n"
            "       ↓\n"
            "Job Matching Agent\n"
            "       ↓\n"
            "Resume Optimization Agent\n"
            "       ↓\n"
            "Quality Review Agent\n"
            "       ↓\n"
            "Final Career Report",
            language="text",
        )

        with st.expander("Inspect complete report JSON"):
            st.json(report)

        st.download_button(
            label="Download Career Copilot Report (JSON)",
            data=json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            ),
            file_name="amanai_career_copilot_report.json",
            mime="application/json",
            use_container_width=True,
        )

else:
    st.markdown(
        """
        <div class="empty-state" style="margin-top:28px">
          <div style="font-size:38px">✦</div>
          <h3>Your next opportunity starts here</h3>
          <p>
            Upload your resume in the sidebar, configure your target role,
            and run the Career Copilot to see matching jobs and
            personalized resume recommendations.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-label">HOW YOUR AI TEAM WORKS</div>',
        unsafe_allow_html=True,
    )

    stages = st.columns(4)

    stage_data = [
        ("01", "Discover", "Retrieve real job listings through MCP."),
        ("02", "Match", "Compare skills with job requirements."),
        ("03", "Optimize", "Generate targeted resume suggestions."),
        ("04", "Review", "Flag issues for human verification."),
    ]

    for col, (number, title, description) in zip(stages, stage_data):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card" style="min-height:145px">
                  <div style="color:#a78bfa;font-weight:800;font-size:11px">
                    STEP {number}
                  </div>
                  <div style="color:white;font-size:17px;font-weight:700;margin-top:14px">
                    {title}
                  </div>
                  <div class="kpi-foot" style="margin-top:9px;line-height:1.7">
                    {description}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# FOOTER
# =========================================================
st.markdown(
    """
    <div class="footer">
      AMANAI LAB · AI CAREER COPILOT<br>
      Built with LangGraph, MCP, Groq, FastAPI, PostgreSQL and Streamlit.
    </div>
    """,
    unsafe_allow_html=True,
)
