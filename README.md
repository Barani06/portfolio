# 🚀 Barani S — Personal Portfolio

**Data Analyst | Cloud & DevOps | DevSecOps Enthusiast**

Full-stack portfolio with React frontend, FastAPI backend, PostgreSQL database, visitor analytics, admin dashboard, and Docker deployment.

---

## 📁 Project Structure

```
portfolio/
├── index.html              ← Complete self-contained React frontend
├── docker-compose.yml      ← Full-stack orchestration
├── nginx.conf              ← Nginx reverse proxy config
├── schema.sql              ← PostgreSQL schema (auto-applied)
├── README.md               ← This file
└── backend/
    ├── main.py             ← FastAPI app (all routes)
    ├── requirements.txt    ← Python dependencies
    └── Dockerfile          ← Backend container
```

---

## ⚡ Quick Start (Docker – Recommended)

### Prerequisites
- Docker Desktop (or Docker Engine + Compose)
- Git

### 1. Clone / Download the project
```bash
git clone <your-repo> portfolio
cd portfolio
```

### 2. Configure environment (optional)
```bash
cp .env.example .env
# Edit .env with your values:
# GITHUB_TOKEN=ghp_xxxx
# SMTP_USER=you@gmail.com
# SMTP_PASS=your_app_password
# EMAIL_TO=barani@email.com
```

### 3. Add your resume PDF
```bash
mkdir -p backend/static
cp ~/Barani_S_Resume.pdf backend/static/
```

### 4. Launch everything
```bash
docker-compose up --build
```

### 5. Open in browser
| URL | Service |
|-----|---------|
| http://localhost | Portfolio frontend |
| http://localhost/api/docs | FastAPI Swagger UI |
| http://localhost:8000 | Backend direct access |

---

## 🛠️ Local Development (Without Docker)

### Frontend
The frontend is a single `index.html` — open it directly:
```bash
# Any static server works:
npx serve .
# or
python -m http.server 8080
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set env vars
export DATABASE_URL="postgresql://user:pass@localhost:5432/portfolio_db"
export GITHUB_USERNAME="barani-s"

uvicorn main:app --reload --port 8000
```

### Database (Local PostgreSQL)
```bash
# Install PostgreSQL, then:
createdb portfolio_db
psql portfolio_db < schema.sql
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check |
| `POST` | `/api/track` | Track page visit |
| `POST` | `/api/contact` | Submit contact form |
| `POST` | `/api/resume/download` | Log resume download |
| `GET`  | `/api/resume/file` | Download resume PDF |
| `GET`  | `/api/github/repos` | Fetch GitHub repos |
| `POST` | `/api/projects/view` | Track project view |
| `GET`  | `/api/admin/stats` | Admin analytics |
| `GET`  | `/api/admin/contacts` | List all contacts |
| `PATCH`| `/api/admin/contacts/{id}/read` | Mark contact read |

**Full Swagger docs:** http://localhost:8000/docs

---

## ☁️ AWS Deployment

### Option A — EC2 + Docker

```bash
# 1. Launch EC2 (Ubuntu 22.04, t3.small or larger)
# 2. SSH in and install Docker
ssh -i key.pem ubuntu@<ec2-ip>
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker ubuntu && newgrp docker

# 3. Upload project
scp -r portfolio/ ubuntu@<ec2-ip>:~/

# 4. Run
cd ~/portfolio
docker compose up -d --build

# 5. Configure Security Group: open ports 80, 443, 22
```

### Option B — AWS Amplify (Frontend Only)
```bash
# In Amplify Console:
# 1. Connect GitHub repo
# 2. Set build output to: /
# 3. Deploy index.html
# Backend still needs EC2 or ECS
```

### Option C — ECS + RDS (Production)
1. Push Docker images to ECR
2. Create ECS cluster with Fargate
3. Use RDS PostgreSQL (Free tier eligible)
4. Set environment variables in ECS task definition
5. Use ALB for HTTPS termination

---

## 🔒 Security Notes

1. **Change default DB credentials** in `docker-compose.yml`
2. **Set CORS origins** to your domain in `backend/main.py`
3. **Add admin authentication** to `/api/admin/*` endpoints before production
4. **Use HTTPS** — get a free cert via Let's Encrypt / Certbot
5. **Store secrets** in AWS Secrets Manager or `.env` (never commit `.env`)

### Add Admin Auth (Quick)
```python
# In main.py, add to admin routes:
from fastapi.security import HTTPBasic, HTTPBasicCredentials
security = HTTPBasic()

@app.get("/api/admin/stats")
async def get_admin_stats(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != os.getenv("ADMIN_PASS"):
        raise HTTPException(status_code=401)
    # ... rest of function
```

---

## 📊 Admin Dashboard

Access the hidden admin panel on the portfolio site:
1. Click the `⚙ admin` link in the navbar (desktop)
2. Or append `#admin` to the URL
3. Dashboard shows: Total Visitors · Resume Downloads · Contacts · Visitors by Country

---

## 🔧 Customization

### Update personal info
Edit `index.html`:
- Search `"Barani S"` and update name
- Update social links (LinkedIn, GitHub, Email)
- Replace project descriptions in `PROJECTS` array
- Update certifications in `CERTS` array

### Add real resume
```bash
# Place PDF in backend/static/
cp your_resume.pdf backend/static/Barani_S_Resume.pdf
```

### Connect GitHub
```bash
# In .env or docker-compose.yml:
GITHUB_USERNAME=your-github-username
GITHUB_TOKEN=your_personal_access_token  # For private repos / higher rate limits
```

---

## 🧑‍💻 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 (CDN), Tailwind CSS, Chart.js |
| Backend | Python 3.12, FastAPI, asyncpg |
| Database | PostgreSQL 16 |
| Proxy | Nginx |
| Containerization | Docker, Docker Compose |
| Deployment | AWS EC2 / Amplify / ECS |

---

## 📄 License
MIT — Free to use and customize.

---

*Built with ❤️ by Barani S · Chennai, India 🇮🇳*
