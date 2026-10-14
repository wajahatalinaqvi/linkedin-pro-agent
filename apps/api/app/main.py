"""Milestone 1: isolated workspaces, authentication and draft CRUD foundation."""
from __future__ import annotations
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import get_db
from .models import User, Workspace, WorkspaceMember, Draft
from .schemas import RegisterInput, LoginInput, AuthToken, UserOut, WorkspaceOut, DraftInput, DraftOut
from .security import password_hash, issue_token, current_user

app = FastAPI(title="LinkedIn Pro SaaS API", version="0.1.0",
              description="Multi-tenant foundation. Publication deliberately disabled in milestone 1.")

@app.get("/health")
def health():
    return {"status": "ok", "service": "linkedin-pro-saas-api"}

@app.post("/api/v1/auth/register", response_model=AuthToken, status_code=201)
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, password_hash=password_hash.hash(payload.password))
    workspace = Workspace(name=payload.workspace_name)
    db.add_all([user, workspace])
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Account already exists")
    return AuthToken(access_token=issue_token(user.id))

@app.post("/api/v1/auth/login", response_model=AuthToken)
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).strip().lower()))
    if not user or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return AuthToken(access_token=issue_token(user.id))

def user_workspaces(db: Session, user_id: str) -> list[Workspace]:
    return db.scalars(
        select(Workspace).join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
    ).all()

@app.get("/api/v1/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return UserOut(id=user.id, email=user.email, workspaces=user_workspaces(db, user.id))

@app.get("/api/v1/workspaces", response_model=list[WorkspaceOut])
def workspaces(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_workspaces(db, user.id)

def require_workspace(workspace_id: str, user: User, db: Session, *, write: bool = False) -> Workspace:
    role = db.scalar(
        select(WorkspaceMember.role)
        .where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user.id)
    )
    if role is None or (write and role not in ("owner", "admin", "editor")):
        raise HTTPException(status_code=404, detail="Workspace not found")
    workspace = db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@app.get("/api/v1/workspaces/{workspace_id}/drafts", response_model=list[DraftOut])
def drafts(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace(workspace_id, user, db)
    return db.scalars(
        select(Draft).where(Draft.workspace_id == workspace_id)
        .order_by(Draft.created_at.desc()).limit(100)
    ).all()

@app.post("/api/v1/workspaces/{workspace_id}/drafts", response_model=DraftOut, status_code=201)
def create_draft(workspace_id: str, payload: DraftInput,
                 user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace(workspace_id, user, db, write=True)
    draft = Draft(workspace_id=workspace_id, created_by_id=user.id,
                  title=payload.title, caption=payload.caption, source_url=str(payload.source_url))
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

@app.get("/api/v1/workspaces/{workspace_id}/drafts/{draft_id}", response_model=DraftOut)
def get_draft(workspace_id: str, draft_id: str,
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace(workspace_id, user, db)
    draft = db.scalar(select(Draft).where(Draft.id == draft_id, Draft.workspace_id == workspace_id))
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft
