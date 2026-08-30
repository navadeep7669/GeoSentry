from __future__ import annotations
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy import select, func

from app.database import get_db
from app.models.report import Report, ReportStatus
from app.models.user import UserRole
from app.schemas.report import ReportResponse, ReportUpdate, ReportListResponse
from app.dependencies import DB, CurrentUser, CitizenOrAbove, ValidatorOrAbove
from app.services import storage_service

router = APIRouter()


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    db: DB,
    current_user: CitizenOrAbove,
    latitude: float = Form(..., description="WGS84 latitude"),
    longitude: float = Form(..., description="WGS84 longitude"),
    elevation_m: float | None = Form(None),
    description: str | None = Form(None),
    files: List[UploadFile] = File(default=[]),
):
    """
    Citizen submits a geo-tagged report with optional photos/videos.
    Files are uploaded to S3/MinIO; URLs stored in media_urls.
    """
    if not -90 <= latitude <= 90:
        raise HTTPException(400, "latitude must be in [-90, 90]")
    if not -180 <= longitude <= 180:
        raise HTTPException(400, "longitude must be in [-180, 180]")

    # Create report first to get id for S3 key namespacing
    report = Report(
        user_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation_m,
        description=description,
        location=f"SRID=4326;POINT({longitude} {latitude})",
        media_urls=[],
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    # Upload files
    urls: list[str] = []
    for f in files:
        if f.filename:
            url = await storage_service.upload_file(f, report.id)
            urls.append(url)

    report.media_urls = urls
    await db.flush()
    await db.refresh(report)
    return ReportResponse.model_validate(report)


@router.get("", response_model=ReportListResponse)
async def list_reports(
    db: DB,
    current_user: CitizenOrAbove,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ReportStatus | None = Query(None, alias="status"),
):
    """
    List reports.
    - Citizens see only their own.
    - Validators/Authority see all.
    """
    stmt = select(Report)
    if current_user.role == UserRole.citizen:
        stmt = stmt.where(Report.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Report.status == status_filter)

    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()

    stmt = stmt.order_by(Report.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return ReportListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ReportResponse.model_validate(r) for r in items],
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: DB, current_user: CitizenOrAbove):
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your report")
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    payload: ReportUpdate,
    db: DB,
    current_user: ValidatorOrAbove,
):
    """
    Validator reviews a report:
    - Set status to validated | rejected
    - Optionally edit description / add notes
    - Approving triggers async risk recompute via Celery
    """
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    if payload.status is not None:
        report.status = payload.status
        report.validated_by_id = current_user.id
    if payload.validator_notes is not None:
        report.validator_notes = payload.validator_notes
    if payload.description is not None:
        report.description = payload.description

    await db.flush()
    await db.refresh(report)

    # Trigger async risk computation only when report is approved
    if payload.status == ReportStatus.validated:
        from app.tasks.risk_tasks import recompute_risk
        recompute_risk.apply_async(args=[report.id], queue="risk")

    return ReportResponse.model_validate(report)
