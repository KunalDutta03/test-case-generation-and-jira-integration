"""
Jira router: config management, connection test, inject test cases.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JiraConfig, TestCase
from app.schemas import (
    JiraConfigCreate, JiraConfigOut, JiraInjectRequest,
    JiraInjectResponse, JiraTestConnectionResponse
)
from app.services import jira_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jira", tags=["jira"])


@router.post("/config", response_model=JiraConfigOut)
def save_jira_config(req: JiraConfigCreate, db: Session = Depends(get_db)):
    # Deactivate existing configs
    db.query(JiraConfig).filter(JiraConfig.is_active == True).update({"is_active": False})
    config = JiraConfig(
        base_url=req.base_url,
        project_key=req.project_key,
        issue_type=req.issue_type,
        email=req.email,
        api_token_encrypted=req.api_token,  # In prod: encrypt with Key Vault
        labels=req.labels,
        is_active=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/config", response_model=list[JiraConfigOut])
def list_jira_configs(db: Session = Depends(get_db)):
    return db.query(JiraConfig).order_by(JiraConfig.created_at.desc()).all()


@router.post("/test-connection", response_model=JiraTestConnectionResponse)
def test_connection(req: JiraConfigCreate):
    result = jira_service.test_connection(req.base_url, req.email, req.api_token)
    return JiraTestConnectionResponse(**result)


@router.post("/inject", response_model=JiraInjectResponse)
def inject_to_jira(req: JiraInjectRequest, db: Session = Depends(get_db)):
    config = db.get(JiraConfig, req.jira_config_id)
    if not config:
        raise HTTPException(404, "Jira config not found")

    # Fetch approved test cases
    test_cases = (
        db.query(TestCase)
        .filter(TestCase.id.in_(req.test_case_ids))
        .filter(TestCase.status == "approved")
        .all()
    )
    if not test_cases:
        raise HTTPException(400, "No approved test cases found for the provided IDs")

    tc_dicts = [
        {
            "id": tc.id,
            "feature": tc.feature,
            "scenario": tc.scenario,
            "gherkin_text": tc.gherkin_text,
            "domain": tc.domain,
        }
        for tc in test_cases
    ]

    result = jira_service.inject_test_cases(
        test_cases=tc_dicts,
        base_url=config.base_url,
        email=config.email,
        api_token=config.api_token_encrypted,
        project_key=config.project_key,
        issue_type=config.issue_type,
        labels=config.labels or ["auto-generated"],
    )

    # Update jira_url in DB for successfully injected cases
    for item in result["injected"]:
        tc = db.get(TestCase, item["id"])
        if tc:
            tc.jira_url = item["url"]
            tc.jira_key = item["jira_key"]
    db.commit()

    return JiraInjectResponse(**result)


@router.get("/defaults")
def get_jira_defaults():
    """Return default Jira settings from environment."""
    return {
        "jira_base_url": settings.jira_base_url,
        "jira_email": settings.jira_email,
        "jira_default_project_key": settings.jira_default_project_key,
        "jira_default_issue_type": settings.jira_default_issue_type,
    }
