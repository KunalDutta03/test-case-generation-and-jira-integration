"""
Test cases router: generate, list, approve/reject, edit.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, TestCase, AuditLog
from app.schemas import (
    GenerateRequest, GenerateResponse, TestCaseOut, TestCaseListOut,
    StatusUpdateRequest, GherkinEditRequest
)
from app.services.generator import generate_test_cases

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test-cases", tags=["test-cases"])


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest, db: Session = Depends(get_db)):
    doc = db.get(Document, req.document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status != "ready":
        raise HTTPException(400, f"Document is not ready (status: {doc.status}). Please wait for processing.")

    raw_cases = generate_test_cases(
        document_id=req.document_id,
        domain=req.domain,
        count=req.count,
        document_text=doc.preview_text or "",
        extra_context=req.extra_context or "",
    )

    saved = []
    for case in raw_cases:
        tc = TestCase(
            document_id=req.document_id,
            feature=case.get("feature", "Feature"),
            scenario=case.get("scenario", "Scenario"),
            gherkin_text=case.get("gherkin_text", ""),
            domain=req.domain,
            status="draft",
        )
        db.add(tc)
        db.flush()  # Get ID before committing
        # Audit
        log = AuditLog(
            entity_type="test_case",
            entity_id=tc.id,
            test_case_id=tc.id,
            action="generated",
            actor="system",
            new_status="draft",
        )
        db.add(log)
        saved.append(tc)

    db.commit()
    for tc in saved:
        db.refresh(tc)

    return GenerateResponse(
        test_case_ids=[tc.id for tc in saved],
        test_cases=saved,
    )


@router.get("", response_model=TestCaseListOut)
def list_test_cases(
    document_id: str | None = Query(None),
    status: str | None = Query(None),
    domain: str | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(TestCase)
    if document_id:
        q = q.filter(TestCase.document_id == document_id)
    if status:
        q = q.filter(TestCase.status == status)
    if domain:
        q = q.filter(TestCase.domain == domain)
    total = q.count()
    cases = q.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    return TestCaseListOut(test_cases=cases, total=total)


@router.get("/{tc_id}", response_model=TestCaseOut)
def get_test_case(tc_id: str, db: Session = Depends(get_db)):
    tc = db.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(404, "Test case not found")
    return tc


@router.patch("/{tc_id}/status", response_model=TestCaseOut)
def update_status(tc_id: str, req: StatusUpdateRequest, db: Session = Depends(get_db)):
    tc = db.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(404, "Test case not found")
    previous = tc.status
    tc.status = req.status
    tc.reviewer_comment = req.comment
    tc.updated_at = datetime.utcnow()
    log = AuditLog(
        entity_type="test_case",
        entity_id=tc.id,
        test_case_id=tc.id,
        action=req.status,
        actor="qa_user",
        previous_status=previous,
        new_status=req.status,
        comment=req.comment,
    )
    db.add(log)
    db.commit()
    db.refresh(tc)
    return tc


@router.put("/{tc_id}", response_model=TestCaseOut)
def edit_test_case(tc_id: str, req: GherkinEditRequest, db: Session = Depends(get_db)):
    tc = db.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(404, "Test case not found")
    previous = tc.status
    tc.gherkin_text = req.gherkin_text
    if req.scenario:
        tc.scenario = req.scenario
    tc.status = "pending_edit"
    tc.updated_at = datetime.utcnow()
    log = AuditLog(
        entity_type="test_case",
        entity_id=tc.id,
        test_case_id=tc.id,
        action="edited",
        actor="qa_user",
        previous_status=previous,
        new_status="pending_edit",
    )
    db.add(log)
    db.commit()
    db.refresh(tc)
    return tc


@router.post("/bulk-status")
def bulk_update_status(
    body: dict,
    db: Session = Depends(get_db)
):
    """Bulk approve or reject test cases."""
    tc_ids = body.get("test_case_ids", [])
    status = body.get("status")
    comment = body.get("comment")
    if status not in ["approved", "rejected"]:
        raise HTTPException(400, "Status must be 'approved' or 'rejected'")
    updated = 0
    for tc_id in tc_ids:
        tc = db.get(TestCase, tc_id)
        if tc:
            previous = tc.status
            tc.status = status
            tc.reviewer_comment = comment
            tc.updated_at = datetime.utcnow()
            log = AuditLog(
                entity_type="test_case",
                entity_id=tc.id,
                test_case_id=tc.id,
                action=status,
                actor="qa_user",
                previous_status=previous,
                new_status=status,
                comment=comment,
            )
            db.add(log)
            updated += 1
    db.commit()
    return {"updated": updated, "status": status}


@router.delete("/{tc_id}")
def delete_test_case(tc_id: str, db: Session = Depends(get_db)):
    tc = db.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(404, "Test case not found")
    db.delete(tc)
    db.commit()
    return {"message": "Test case deleted", "id": tc_id}
