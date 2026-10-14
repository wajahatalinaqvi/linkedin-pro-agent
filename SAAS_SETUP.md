# LinkedIn Pro Studio — Milestone 1 (development only)

This is a **multi-user foundation**, not the production SaaS yet. Original GitHub
publication workflows and legacy Python agent remain untouched on `main`.
Milestone 1 does **not** call Gemini or publish LinkedIn content.

## Windows 11 / PowerShell

Prerequisites: Node.js 22+, Python 3.12, Docker Desktop, Git.

```powershell
git clone https://github.com/wajahatalinaqvi/linkedin-pro-agent.git
cd linkedin-pro-agent
git switch saas-development
docker compose -f infra/docker-compose.yml up -d
cd apps/api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set a unique strong JWT_SECRET in your process environment:
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Open a NEW PowerShell terminal (keep the API terminal running):

```powershell
cd linkedin-pro-agent/apps/web
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. Create an account and workspace. From the dashboard,
create a draft and confirm it appears only in that workspace.

API docs: http://localhost:8000/docs
Health: http://localhost:8000/health

## Architecture and security

- Next.js pages and server routes act as the browser-facing BFF. The JWT is
  held in an HttpOnly, SameSite=Lax cookie on the web origin; FastAPI receives
  it through server-side Authorization headers. Avoid storing JWTs in localStorage.
- All workspace draft routes enforce current membership in FastAPI.
- The initial JWT has an 8-hour expiry; production auth needs revocation,
  refresh/session rotation, email verification, MFA, password recovery and
  rate limiting before public registration.
- The LinkedIn credentials model is reserved for future encrypted OAuth
  integration; **never store plaintext access tokens** in the field.
- The sample Docker passwords are LOCAL ONLY; replace them for deployment.
- Neither OAuth nor public publishing is enabled in this milestone.
- The existing PDF renderer remains at `src/carousel/`; don't move it until
  package tests and rendering parity pass.

## Next steps

1. Integrate the existing Python carousel renderer as a reusable service.
2. Store slide JSON and PDF assets in workspace-scoped storage.
3. Add research workers and per-tenant daily priority.
4. Validate LinkedIn OAuth permissions before implementing publishing.
5. Add subscription quotas, logging, audit trails and tenant security tests.
