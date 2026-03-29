from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Document Schemas ─────────────────────────────────────────────────────────
class DocumentOut(BaseModel):
    id: str
    name: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    preview_text: Optional[str] = None
    error_message: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListOut(BaseModel):
    documents: List[DocumentOut]
    total: int


# ─── Test Case Schemas ────────────────────────────────────────────────────────
class TestCaseOut(BaseModel):
    id: str
    document_id: str
    feature: str
    scenario: str
    gherkin_text: str
    domain: str
    status: str
    jira_url: Optional[str] = None
    jira_key: Optional[str] = None
    reviewer_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    document_id: str
    domain: str = Field("Web", pattern="^(Web|API|Mobile|Database|Security)$")
    count: int = Field(5, ge=1, le=50)
    extra_context: Optional[str] = None


class GenerateResponse(BaseModel):
    test_case_ids: List[str]
    test_cases: List[TestCaseOut]


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|pending_edit)$")
    comment: Optional[str] = None


class GherkinEditRequest(BaseModel):
    gherkin_text: str
    scenario: Optional[str] = None


class TestCaseListOut(BaseModel):
    test_cases: List[TestCaseOut]
    total: int


# ─── Jira Schemas ─────────────────────────────────────────────────────────────
class JiraConfigCreate(BaseModel):
    base_url: str
    project_key: str
    issue_type: str = "Task"
    email: str
    api_token: str
    labels: List[str] = ["auto-generated"]


class JiraConfigOut(BaseModel):
    id: str
    base_url: str
    project_key: str
    issue_type: str
    email: str
    labels: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JiraInjectRequest(BaseModel):
    test_case_ids: List[str]
    jira_config_id: str


class JiraInjectedItem(BaseModel):
    id: str
    jira_key: str
    url: str


class JiraInjectResponse(BaseModel):
    injected: List[JiraInjectedItem]
    failed: List[dict]


class JiraTestConnectionResponse(BaseModel):
    success: bool
    message: str
    projects: Optional[List[str]] = None


# ─── Audit Log Schema ─────────────────────────────────────────────────────────
class AuditLogOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor: str
    previous_status: Optional[str]
    new_status: Optional[str]
    comment: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# ─── Health ───────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
