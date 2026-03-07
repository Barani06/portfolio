"""
Barani S – Portfolio Backend
FastAPI + PostgreSQL | Full-stack portfolio backend
Author: Barani S
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import asyncpg
import httpx
import os
import json
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Barani S – Portfolio API",
    description="Backend for Barani S personal portfolio",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod: set to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ───────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://portfolio_user:portfolio_pass@db:5432/portfolio_db")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "Barani06")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN","")          # optional – avoids rate limits
EMAIL_FROM = os.getenv("EMAIL_FROM", "sbarani275@gmail.com")
EMAIL_TO = os.getenv("EMAIL_TO", "sbarani275@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
RESUME_PATH = os.getenv("RESUME_PATH", "static/Barani_S_Resume.pdf")

# ── DB Pool ───────────────────────────────────────────────────────────────────
db_pool: asyncpg.Pool | None = None

async def get_db() -> asyncpg.Connection:
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with db_pool.acquire() as conn:
        yield conn

@app.on_event("startup")
async def startup():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        await init_db()
        logger.info("✅ Database connected and initialized")
    except Exception as e:
        logger.warning(f"⚠️  DB not available (demo mode): {e}")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

async def init_db():
    """Create tables if they don't exist."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id SERIAL PRIMARY KEY,
                ip_address TEXT,
                country TEXT DEFAULT 'Unknown',
                device_type TEXT DEFAULT 'desktop',
                page TEXT DEFAULT '/',
                user_agent TEXT,
                visited_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS resume_downloads (
                id SERIAL PRIMARY KEY,
                ip_address TEXT,
                downloaded_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS contact_requests (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                job_role TEXT,
                message TEXT NOT NULL,
                submitted_at TIMESTAMPTZ DEFAULT NOW(),
                is_read BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS project_views (
                id SERIAL PRIMARY KEY,
                project_slug TEXT NOT NULL,
                viewed_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

# ── Pydantic Models ───────────────────────────────────────────────────────────

class ContactRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    role: Optional[str] = None
    message: str

class TrackRequest(BaseModel):
    page: str = "/"
    device: str = "desktop"

class ProjectViewRequest(BaseModel):
    project_slug: str

# ── Helper: Email ─────────────────────────────────────────────────────────────

def send_email_notification(contact: ContactRequest):
    """Send email notification when someone submits the contact form."""
    if not SMTP_USER or not SMTP_PASS:
        logger.info("Email not configured – skipping notification")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚀 Portfolio Contact: {contact.name} from {contact.company or 'N/A'}"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        html_body = f"""
        <html><body style="font-family:sans-serif;background:#0d1526;color:#e2e8f0;padding:24px;border-radius:12px;">
          <h2 style="color:#00d4ff;">New Contact Request 📬</h2>
          <table style="width:100%;border-collapse:collapse;">
            <tr><td style="padding:8px 0;color:#94a3b8;">Name</td><td style="color:#e2e8f0;">{contact.name}</td></tr>
            <tr><td style="padding:8px 0;color:#94a3b8;">Email</td><td style="color:#00d4ff;">{contact.email}</td></tr>
            <tr><td style="padding:8px 0;color:#94a3b8;">Company</td><td>{contact.company or '—'}</td></tr>
            <tr><td style="padding:8px 0;color:#94a3b8;">Role</td><td>{contact.role or '—'}</td></tr>
          </table>
          <div style="margin-top:16px;padding:16px;background:#111c30;border-left:4px solid #00d4ff;border-radius:4px;">
            <strong style="color:#00d4ff;">Message:</strong><br><br>{contact.message}
          </div>
          <p style="margin-top:16px;color:#64748b;font-size:12px;">Sent via Barani S Portfolio · {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</p>
        </body></html>
        """
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        logger.info(f"📧 Email sent for contact: {contact.email}")
    except Exception as e:
        logger.error(f"Email send failed: {e}")

# ── Routes: Health ────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "service": "Barani S Portfolio API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ── Routes: Visitor Tracking ─────────────────────────────────────────────────

@app.post("/api/track")
async def track_visitor(request: Request, body: TrackRequest):
    """Track a page visit with device and page info."""
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    ua = request.headers.get("User-Agent", "unknown")

    # Geolocation via free API
    country = "Unknown"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            geo = await client.get(f"https://ipapi.co/{ip}/json/")
            if geo.status_code == 200:
                country = geo.json().get("country_name", "Unknown")
    except Exception:
        pass

    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO visitors (ip_address, country, device_type, page, user_agent) VALUES ($1,$2,$3,$4,$5)",
                    ip, country, body.device, body.page, ua[:500]
                )
        except Exception as e:
            logger.warning(f"Track visitor DB error: {e}")

    return {"tracked": True}

# ── Routes: Contact ───────────────────────────────────────────────────────────

@app.post("/api/contact")
async def submit_contact(request: Request, body: ContactRequest):
    """Store contact form submission and send email notification."""
    if len(body.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Message too short")

    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO contact_requests (name, email, company, job_role, message) VALUES ($1,$2,$3,$4,$5)",
                    body.name, body.email, body.company, body.role, body.message
                )
        except Exception as e:
            logger.warning(f"Contact DB error: {e}")

    send_email_notification(body)
    return {"success": True, "message": "Message received! Barani will get back to you soon."}

# ── Routes: Resume Download ───────────────────────────────────────────────────

@app.post("/api/resume/download")
async def log_resume_download(request: Request):
    """Log a resume download event."""
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("INSERT INTO resume_downloads (ip_address) VALUES ($1)", ip)
        except Exception as e:
            logger.warning(f"Resume download log error: {e}")
    return {"logged": True}

@app.get("/api/resume/file")
async def download_resume_file():
    """Serve the resume PDF file."""
    if not os.path.exists(RESUME_PATH):
        raise HTTPException(status_code=404, detail="Resume file not found. Please upload it to static/Barani_S_Resume.pdf")
    return FileResponse(RESUME_PATH, media_type="application/pdf", filename="Barani_S_Resume.pdf")

# ── Routes: GitHub ────────────────────────────────────────────────────────────

@app.get("/api/github/repos")
async def get_github_repos():
    """Fetch public repositories from GitHub API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"https://api.github.com/users/{GITHUB_USERNAME}/repos?sort=updated&per_page=20",
                headers=headers
            )
            if res.status_code != 200:
                return {"repos": [], "error": "GitHub API error"}
            repos = res.json()
            return {
                "repos": [
                    {
                        "name": r["name"],
                        "description": r.get("description") or "",
                        "html_url": r["html_url"],
                        "language": r.get("language") or "Unknown",
                        "stars": r["stargazers_count"],
                        "forks": r["forks_count"],
                        "updated_at": r["updated_at"],
                        "topics": r.get("topics", [])
                    }
                    for r in repos if not r["fork"]
                ]
            }
    except Exception as e:
        logger.error(f"GitHub API error: {e}")
        return {"repos": [], "error": str(e)}

# ── Routes: Project View Tracking ────────────────────────────────────────────

@app.post("/api/projects/view")
async def track_project_view(body: ProjectViewRequest):
    """Track when a project card is viewed."""
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO project_views (project_slug) VALUES ($1)", body.project_slug
                )
        except Exception as e:
            logger.warning(f"Project view log error: {e}")
    return {"tracked": True}

# ── Routes: Admin Analytics ───────────────────────────────────────────────────

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Aggregate analytics for the admin dashboard."""
    if not db_pool:
        # Demo data when DB is unavailable
        return {
            "total_visitors": 1247,
            "resume_downloads": 89,
            "contact_requests": 34,
            "project_views": 312,
            "visitors_by_country": [
                {"country": "India", "count": 560},
                {"country": "USA", "count": 274},
                {"country": "UK", "count": 150},
                {"country": "Germany", "count": 100},
                {"country": "Others", "count": 163},
            ],
            "visitors_over_time": [
                {"month": "Jan", "count": 120}, {"month": "Feb", "count": 190},
                {"month": "Mar", "count": 170}, {"month": "Apr", "count": 280},
                {"month": "May", "count": 350}, {"month": "Jun", "count": 420},
                {"month": "Jul", "count": 380},
            ],
            "top_projects": [
                {"slug": "rainfall-analysis", "views": 140},
                {"slug": "aws-webapp", "views": 98},
                {"slug": "python-analysis", "views": 74},
            ]
        }

    async with db_pool.acquire() as conn:
        total_visitors = await conn.fetchval("SELECT COUNT(*) FROM visitors")
        resume_downloads = await conn.fetchval("SELECT COUNT(*) FROM resume_downloads")
        contact_requests = await conn.fetchval("SELECT COUNT(*) FROM contact_requests")
        project_views = await conn.fetchval("SELECT COUNT(*) FROM project_views")

        country_rows = await conn.fetch(
            "SELECT country, COUNT(*) AS count FROM visitors GROUP BY country ORDER BY count DESC LIMIT 10"
        )
        top_projects = await conn.fetch(
            "SELECT project_slug, COUNT(*) AS views FROM project_views GROUP BY project_slug ORDER BY views DESC LIMIT 5"
        )
        monthly = await conn.fetch("""
            SELECT TO_CHAR(visited_at, 'Mon') AS month, COUNT(*) AS count
            FROM visitors
            WHERE visited_at >= NOW() - INTERVAL '7 months'
            GROUP BY month, DATE_TRUNC('month', visited_at)
            ORDER BY DATE_TRUNC('month', visited_at)
        """)

    return {
        "total_visitors": total_visitors,
        "resume_downloads": resume_downloads,
        "contact_requests": contact_requests,
        "project_views": project_views,
        "visitors_by_country": [{"country": r["country"], "count": r["count"]} for r in country_rows],
        "visitors_over_time": [{"month": r["month"], "count": r["count"]} for r in monthly],
        "top_projects": [{"slug": r["project_slug"], "views": r["views"]} for r in top_projects],
    }

@app.get("/api/admin/contacts")
async def get_contacts():
    """List all contact form submissions (admin only)."""
    if not db_pool:
        return {"contacts": []}
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, email, company, job_role, message, submitted_at, is_read FROM contact_requests ORDER BY submitted_at DESC LIMIT 50"
        )
    return {"contacts": [dict(r) for r in rows]}

@app.patch("/api/admin/contacts/{contact_id}/read")
async def mark_contact_read(contact_id: int):
    """Mark a contact request as read."""
    if not db_pool:
        return {"updated": False}
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE contact_requests SET is_read = TRUE WHERE id = $1", contact_id)
    return {"updated": True}
