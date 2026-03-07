-- ============================================================
-- Barani S Portfolio – PostgreSQL Schema
-- Run this manually or it's auto-created on backend startup
-- ============================================================

-- ── Visitor Tracking ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS visitors (
    id          SERIAL PRIMARY KEY,
    ip_address  TEXT,
    country     TEXT DEFAULT 'Unknown',
    device_type TEXT DEFAULT 'desktop',  -- 'mobile' | 'desktop' | 'tablet'
    page        TEXT DEFAULT '/',
    user_agent  TEXT,
    visited_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visitors_country    ON visitors(country);
CREATE INDEX IF NOT EXISTS idx_visitors_visited_at ON visitors(visited_at);

-- ── Resume Downloads ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS resume_downloads (
    id              SERIAL PRIMARY KEY,
    ip_address      TEXT,
    downloaded_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resume_downloaded_at ON resume_downloads(downloaded_at);

-- ── Contact Form Submissions ──────────────────────────────────
CREATE TABLE IF NOT EXISTS contact_requests (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL,
    company         TEXT,
    job_role        TEXT,
    message         TEXT NOT NULL,
    submitted_at    TIMESTAMPTZ DEFAULT NOW(),
    is_read         BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_contacts_submitted_at ON contact_requests(submitted_at);
CREATE INDEX IF NOT EXISTS idx_contacts_is_read       ON contact_requests(is_read);

-- ── Project View Tracking ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_views (
    id              SERIAL PRIMARY KEY,
    project_slug    TEXT NOT NULL,
    viewed_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_views_slug     ON project_views(project_slug);
CREATE INDEX IF NOT EXISTS idx_project_views_viewed   ON project_views(viewed_at);

-- ── Useful Views ──────────────────────────────────────────────

CREATE OR REPLACE VIEW dashboard_summary AS
SELECT
    (SELECT COUNT(*) FROM visitors)          AS total_visitors,
    (SELECT COUNT(*) FROM resume_downloads)  AS resume_downloads,
    (SELECT COUNT(*) FROM contact_requests)  AS contact_requests,
    (SELECT COUNT(*) FROM project_views)     AS project_views,
    (SELECT COUNT(*) FROM contact_requests WHERE is_read = FALSE) AS unread_contacts;

CREATE OR REPLACE VIEW visitors_by_country AS
SELECT country, COUNT(*) AS visit_count
FROM visitors
GROUP BY country
ORDER BY visit_count DESC;

CREATE OR REPLACE VIEW monthly_visitors AS
SELECT
    DATE_TRUNC('month', visited_at) AS month,
    TO_CHAR(visited_at, 'Mon YYYY') AS label,
    COUNT(*) AS visits
FROM visitors
GROUP BY DATE_TRUNC('month', visited_at), TO_CHAR(visited_at, 'Mon YYYY')
ORDER BY month;
