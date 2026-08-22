# Client Magnet - Production Readiness Checklist

This document tracks all critical requirements, compliance gatekeepers, and verification criteria for deploying **Client Magnet** to production on Render.

---

## 1. Application & Code Quality

- [x] **Zero TypeScript Errors**: `npm run build` runs cleanly without typing errors.
- [x] **Zero Python Syntax/Import Errors**: All modules, routers, and dependencies cleanly resolve.
- [x] **Automated Test Suite**: 100% test pass rate across unit, integration, and E2E suites.
- [x] **Tenant Isolation**: Every database query scopes access strictly by `user_id == current_user.id`.
- [x] **Safe Error Handling**: Unhandled exceptions return generic, non-leaking JSON error messages in production.

---

## 2. Database & PostgreSQL Architecture

- [x] **Single Database**: Pure PostgreSQL schema with zero secondary database dependencies.
- [x] **Safe Connection Strings**: Supports `DATABASE_URL` with automatic async normalization (`postgresql+asyncpg://`).
- [x] **Connection Pooling**: `pool_size=10, max_overflow=20, pool_recycle=300, pool_pre_ping=True`.
- [x] **Alembic Migrations**: Fully versioned migrations (`001` through `008`) executing automatically upon deployment.
- [x] **Backup Strategy**: Documented in `docs/DATABASE_BACKUP_AND_RECOVERY.md`.

---

## 3. Security & Secrets Management

- [x] **No Committed Secrets**: `.env` is ignored by Git; `.env.example` documents variable names only.
- [x] **Password Hashing**: Argon2id with memory cost and time cost tuned for production security.
- [x] **Credential Encryption**: AES-256 Fernet encryption for OAuth refresh tokens and WhatsApp system tokens.
- [x] **Rate Limiting**: IP and user-based throttling on login and AI endpoints.
- [x] **Zero Unauthorized Automation**: Zero scraping, CAPTCHA bypass, session theft, or headless browser workarounds.

---

## 4. External Integrations & Official APIs

- [x] **Google Cloud / Gmail**: Google OAuth 2.0 with human approval on every email dispatch.
- [x] **Meta WhatsApp Cloud API**: Webhook verification, HMAC-SHA256 signature checking, and 24-hour compliance window.
- [x] **Social Platforms (Meta, X, LinkedIn, TikTok)**: Official OAuth token exchange and direct publishing capabilities where supported.
- [x] **Google Gemini AI**: Consultative advisory outputs with fallback support when API keys are absent.

---

## 5. Render Deployment Configuration

- [x] **Blueprint (`render.yaml`)**: Declares Web Service, Worker Service, and Managed PostgreSQL.
- [x] **Health Checks**: `/health` and `/api/v1/health` respond with `{ "status": "healthy", "database": "connected" }`.
- [x] **Build Script**: `backend/render_build.sh` automatically installs packages and executes `alembic upgrade head`.
