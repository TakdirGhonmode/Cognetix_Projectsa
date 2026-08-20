import os
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from report_generator import (
    generate_daily_report_data,
    generate_weekly_report_data,
    generate_comparison_report_data,
    export_report_to_json,
    export_report_to_csv,
    export_report_to_pdf
)

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"])


@router.get("/daily", summary="Generate Daily System Health Report")
def get_daily_report(db: Session = Depends(get_db)):
    """Returns the daily 24h health monitoring report."""
    return generate_daily_report_data(db)


@router.get("/weekly", summary="Generate Weekly Monitoring Summary")
def get_weekly_report(db: Session = Depends(get_db)):
    """Returns the weekly 7-day monitoring summary with trend evaluation."""
    return generate_weekly_report_data(db)


@router.get("/compare", summary="Generate Service Performance Comparison")
def get_performance_comparison(db: Session = Depends(get_db)):
    """Returns ranked comparative performance metrics across all services."""
    return generate_comparison_report_data(db)


@router.get("/export/json", summary="Export monitoring report as JSON file")
def export_json_report(
    report_type: str = Query("daily", pattern="^(daily|weekly|compare)$"),
    db: Session = Depends(get_db)
):
    """Generates and exports the requested report to a JSON file in reports/."""
    if report_type == "daily":
        data = generate_daily_report_data(db)
        prefix = "daily_health_report"
    elif report_type == "weekly":
        data = generate_weekly_report_data(db)
        prefix = "weekly_monitoring_summary"
    else:
        data = generate_comparison_report_data(db)
        prefix = "service_comparison_report"

    filepath = export_report_to_json(data=data, filename_prefix=prefix)
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/json"
    )


@router.get("/export/csv", summary="Export monitoring report as CSV file")
def export_csv_report(
    report_type: str = Query("compare", pattern="^(daily|weekly|compare)$"),
    db: Session = Depends(get_db)
):
    """Generates and exports the requested report to a CSV file in reports/."""
    if report_type == "daily":
        data = generate_daily_report_data(db)
        prefix = "daily_health_report"
    elif report_type == "weekly":
        data = generate_weekly_report_data(db)
        prefix = "weekly_monitoring_summary"
    else:
        data = generate_comparison_report_data(db)
        prefix = "service_comparison_report"

    filepath = export_report_to_csv(data=data, filename_prefix=prefix)
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="text/csv"
    )


@router.get("/export/pdf", summary="Export monitoring report as PDF document")
def export_pdf_report(
    report_type: str = Query("daily", pattern="^(daily|weekly|compare)$"),
    db: Session = Depends(get_db)
):
    """Generates and exports the requested report to a PDF document in reports/."""
    if report_type == "daily":
        data = generate_daily_report_data(db)
        prefix = "daily_health_report"
    elif report_type == "weekly":
        data = generate_weekly_report_data(db)
        prefix = "weekly_monitoring_summary"
    else:
        data = generate_comparison_report_data(db)
        prefix = "service_comparison_report"

    filepath = export_report_to_pdf(data=data, filename_prefix=prefix)
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/pdf"
    )
