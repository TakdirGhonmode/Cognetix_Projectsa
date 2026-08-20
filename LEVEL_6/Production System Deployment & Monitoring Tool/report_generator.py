import os
import json
import csv
from datetime import timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.models import (
    Service,
    HealthCheck,
    ErrorLog,
    Alert,
    DailyBreakdown,
    ServiceMetrics,
    SystemMetricsSummary,
    utc_now
)
from logger import logger

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def calculate_service_metrics(service: Service, db: Session, days: int = 7) -> ServiceMetrics:
    """
    Computes daily & weekly uptime percentages, latency, error count, and daily breakdown for a service.
    Formula: Uptime % = (Healthy Checks / Total Checks) * 100
    """
    now_utc = utc_now()
    day_ago = now_utc - timedelta(days=1)
    week_ago = now_utc - timedelta(days=days)

    # 24h stats
    checks_24h = db.query(HealthCheck).filter(
        HealthCheck.service_id == service.id,
        HealthCheck.checked_at >= day_ago
    ).all()

    total_24h = len(checks_24h)
    healthy_24h = sum(1 for c in checks_24h if c.is_healthy)
    daily_uptime = round((healthy_24h / total_24h * 100.0), 2) if total_24h > 0 else 100.0
    avg_latency = round(sum(c.response_time_ms for c in checks_24h) / total_24h, 2) if total_24h > 0 else 0.0

    errors_24h = db.query(func.count(ErrorLog.id)).filter(
        ErrorLog.service_id == service.id,
        ErrorLog.timestamp >= day_ago
    ).scalar() or 0

    alerts_24h = db.query(func.count(Alert.id)).filter(
        Alert.service_id == service.id,
        Alert.triggered_at >= day_ago
    ).scalar() or 0

    active_alerts = db.query(func.count(Alert.id)).filter(
        Alert.service_id == service.id,
        Alert.is_resolved == False
    ).scalar() or 0

    # 7-day stats
    checks_week = db.query(HealthCheck).filter(
        HealthCheck.service_id == service.id,
        HealthCheck.checked_at >= week_ago
    ).all()

    total_week = len(checks_week)
    healthy_week = sum(1 for c in checks_week if c.is_healthy)
    weekly_uptime = round((healthy_week / total_week * 100.0), 2) if total_week > 0 else 100.0

    # Daily breakdown for last 7 days
    breakdown: List[DailyBreakdown] = []
    for i in range(days):
        day_start = (now_utc - timedelta(days=i+1)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_str = day_start.strftime("%Y-%m-%d")

        day_checks = [c for c in checks_week if day_start <= c.checked_at < day_end]
        tot = len(day_checks)
        hlth = sum(1 for c in day_checks if c.is_healthy)
        upt = round((hlth / tot * 100.0), 2) if tot > 0 else 100.0
        lat = round(sum(c.response_time_ms for c in day_checks) / tot, 2) if tot > 0 else 0.0

        err_cnt = db.query(func.count(ErrorLog.id)).filter(
            ErrorLog.service_id == service.id,
            ErrorLog.timestamp >= day_start,
            ErrorLog.timestamp < day_end
        ).scalar() or 0

        breakdown.append(DailyBreakdown(
            date=day_str,
            total_checks=tot,
            healthy_checks=hlth,
            uptime_percentage=upt,
            avg_response_time_ms=lat,
            error_count=err_cnt
        ))

    return ServiceMetrics(
        service_id=service.id,
        service_name=service.name,
        url=service.url,
        current_status=service.current_status,
        daily_uptime_percentage=daily_uptime,
        weekly_uptime_percentage=weekly_uptime,
        avg_response_time_ms=avg_latency,
        total_checks_24h=total_24h,
        healthy_checks_24h=healthy_24h,
        error_count_24h=errors_24h,
        alert_count_24h=alerts_24h,
        active_alerts_count=active_alerts,
        consecutive_failures=service.consecutive_failures,
        weekly_breakdown=breakdown
    )


def generate_daily_report_data(db: Session) -> Dict[str, Any]:
    """Generates 24-hour operational health report data."""
    services = db.query(Service).all()
    metrics_list = [calculate_service_metrics(s, db, days=1) for s in services]

    total_services = len(services)
    active_count = sum(1 for s in services if s.is_active)
    healthy_count = sum(1 for s in services if s.current_status == "HEALTHY")
    degraded_count = sum(1 for s in services if s.current_status == "DEGRADED")
    down_count = sum(1 for s in services if s.current_status == "DOWN")

    avg_daily_uptime = round(sum(m.daily_uptime_percentage for m in metrics_list) / total_services, 2) if total_services > 0 else 100.0
    total_errors = sum(m.error_count_24h for m in metrics_list)
    total_alerts = sum(m.alert_count_24h for m in metrics_list)

    return {
        "report_type": "Daily System Health Report",
        "generated_at": utc_now().isoformat() + "Z",
        "period": "Last 24 Hours",
        "system_summary": {
            "total_services": total_services,
            "active_services": active_count,
            "healthy_services": healthy_count,
            "degraded_services": degraded_count,
            "down_services": down_count,
            "overall_uptime_percentage": avg_daily_uptime,
            "total_errors_24h": total_errors,
            "total_alerts_24h": total_alerts
        },
        "services": [m.model_dump() for m in metrics_list]
    }


def generate_weekly_report_data(db: Session) -> Dict[str, Any]:
    """Generates 7-day weekly monitoring summary data with trend evaluation."""
    services = db.query(Service).all()
    metrics_list = [calculate_service_metrics(s, db, days=7) for s in services]

    total_services = len(services)
    avg_weekly_uptime = round(sum(m.weekly_uptime_percentage for m in metrics_list) / total_services, 2) if total_services > 0 else 100.0
    total_errors_week = sum(sum(b.error_count for b in m.weekly_breakdown) for m in metrics_list)

    trend = "STABLE"
    if avg_weekly_uptime < 95.0 or total_errors_week > 50:
        trend = "DEGRADING"
    elif avg_weekly_uptime >= 99.0 and total_errors_week == 0:
        trend = "EXCELLENT"

    return {
        "report_type": "Weekly Monitoring Summary",
        "generated_at": utc_now().isoformat() + "Z",
        "period": "Last 7 Days",
        "weekly_summary": {
            "total_services": total_services,
            "overall_weekly_uptime_percentage": avg_weekly_uptime,
            "total_errors_7d": total_errors_week,
            "trend": trend
        },
        "services": [m.model_dump() for m in metrics_list]
    }


def generate_comparison_report_data(db: Session) -> Dict[str, Any]:
    """Generates service performance comparison data."""
    services = db.query(Service).all()
    metrics_list = [calculate_service_metrics(s, db, days=7) for s in services]

    ranked = sorted(
        metrics_list,
        key=lambda x: (-x.weekly_uptime_percentage, x.avg_response_time_ms)
    )

    comparison_table = []
    for rank, m in enumerate(ranked, 1):
        comparison_table.append({
            "rank": rank,
            "service_id": m.service_id,
            "service_name": m.service_name,
            "current_status": m.current_status,
            "daily_uptime_pct": m.daily_uptime_percentage,
            "weekly_uptime_pct": m.weekly_uptime_percentage,
            "avg_response_time_ms": m.avg_response_time_ms,
            "error_count_24h": m.error_count_24h,
            "active_alerts": m.active_alerts_count
        })

    return {
        "report_type": "Service Performance Comparison",
        "generated_at": utc_now().isoformat() + "Z",
        "total_services_compared": len(services),
        "comparison": comparison_table
    }


def export_report_to_json(data: Dict[str, Any], filename_prefix: str = "monitoring_report") -> str:
    """Exports report dictionary to a JSON file in reports/."""
    timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"JSON report exported to: {filepath}")
    return filepath


def export_report_to_csv(data: Dict[str, Any], filename_prefix: str = "service_comparison") -> str:
    """Exports comparison or health data to a CSV file in reports/."""
    timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)

    rows = data.get("comparison") or data.get("services") or []
    if not rows:
        rows = [{"info": "No services available"}]

    keys = list(rows[0].keys())

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            clean_row = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items()}
            writer.writerow(clean_row)

    logger.info(f"CSV report exported to: {filepath}")
    return filepath


def export_report_to_pdf(data: Dict[str, Any], filename_prefix: str = "system_report") -> str:
    """Exports report to a formatted PDF file using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            name="SubtitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        )

        # Title and Header
        report_title = data.get("report_type", "System Health Report")
        story.append(Paragraph(f"<b>{report_title}</b>", title_style))
        story.append(Paragraph(f"Generated at: {data.get('generated_at', '')} UTC | Period: {data.get('period', 'N/A')}", subtitle_style))
        story.append(Spacer(1, 10))

        # Summary box if present
        summary = data.get("system_summary") or data.get("weekly_summary")
        if summary:
            summary_data = [[Paragraph("<b>Metric</b>", styles["Normal"]), Paragraph("<b>Value</b>", styles["Normal"])]]
            for k, v in summary.items():
                label = k.replace("_", " ").title()
                summary_data.append([label, str(v)])

            sum_table = Table(summary_data, colWidths=[200, 300])
            sum_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(sum_table)
            story.append(Spacer(1, 15))

        # Services Table
        services = data.get("services") or data.get("comparison") or []
        if services:
            story.append(Paragraph("<b>Service Breakdown</b>", styles["Heading2"]))
            story.append(Spacer(1, 6))

            table_data = [["Service Name", "Status", "Daily Uptime", "Weekly Uptime", "Avg Latency", "Errors (24h)"]]
            for s in services:
                s_name = s.get("service_name", "N/A")
                status = s.get("current_status", "N/A")
                d_upt = f"{s.get('daily_uptime_percentage', s.get('daily_uptime_pct', 0))}%"
                w_upt = f"{s.get('weekly_uptime_percentage', s.get('weekly_uptime_pct', 0))}%"
                lat = f"{s.get('avg_response_time_ms', 0)} ms"
                errs = str(s.get("error_count_24h", 0))
                table_data.append([s_name, status, d_upt, w_upt, lat, errs])

            svc_table = Table(table_data, colWidths=[130, 75, 80, 80, 90, 75])
            svc_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(svc_table)

        doc.build(story)
        logger.info(f"PDF report exported to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {str(e)}")
        raise e
