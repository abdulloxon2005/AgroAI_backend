"""
AgroAI — Dashboard Endpoints
User statistics and chart data from real database queries.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case, literal_column

from app.db.database import get_db
from app.db.models import User, Scan
from app.domain.schemas import DashboardStatsResponse, DashboardChartsResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get total_scans, diseases_found, healthy_count, last_scan_date."""
    # Total scans
    result = await db.execute(
        select(func.count(Scan.id)).filter(Scan.user_id == current_user.id)
    )
    total_scans = result.scalar() or 0

    # Healthy vs Diseased count
    health_res = await db.execute(
        select(
            func.sum(case((Scan.is_healthy.is_(True), 1), else_=0)),
            func.sum(case((Scan.is_healthy.is_(False), 1), else_=0)),
        ).filter(Scan.user_id == current_user.id)
    )
    healthy_count, diseases_found = health_res.first()

    # Last scan date
    last_scan_res = await db.execute(
        select(Scan.scanned_at)
        .filter(Scan.user_id == current_user.id)
        .order_by(Scan.scanned_at.desc())
        .limit(1)
    )
    last_scan = last_scan_res.scalar()

    return {
        "total_scans": total_scans,
        "diseases_found": diseases_found or 0,
        "healthy_count": healthy_count or 0,
        "last_scan_date": last_scan,
    }


@router.get("/charts", response_model=DashboardChartsResponse)
async def get_charts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chart data from real DB queries (SQLite strftime)."""
    user_filter = Scan.user_id == current_user.id

    # ---- Monthly scans (last 6 months) ----
    monthly_result = await db.execute(
        select(
            func.strftime("%Y-%m", Scan.scanned_at).label("month"),
            func.count(Scan.id).label("count"),
        )
        .filter(user_filter)
        .group_by(literal_column("month"))
        .order_by(literal_column("month").desc())
        .limit(6)
    )
    monthly_scans = [
        {"month": row.month, "count": row.count}
        for row in monthly_result.all()
    ]
    monthly_scans.reverse()  # chronological order

    # ---- Disease distribution ----
    disease_result = await db.execute(
        select(
            Scan.disease_name.label("disease"),
            func.count(Scan.id).label("count"),
        )
        .filter(user_filter, Scan.is_healthy.is_(False), Scan.disease_name.isnot(None))
        .group_by(Scan.disease_name)
        .order_by(func.count(Scan.id).desc())
        .limit(10)
    )
    disease_distribution = [
        {"disease": row.disease, "count": row.count}
        for row in disease_result.all()
    ]

    # ---- Health trend (last 6 months) ----
    trend_result = await db.execute(
        select(
            func.strftime("%Y-%m", Scan.scanned_at).label("date"),
            func.sum(case((Scan.is_healthy.is_(True), 1), else_=0)).label("healthy"),
            func.sum(case((Scan.is_healthy.is_(False), 1), else_=0)).label("diseased"),
        )
        .filter(user_filter)
        .group_by(literal_column("date"))
        .order_by(literal_column("date").desc())
        .limit(6)
    )
    health_trend = [
        {"date": row.date, "healthy": row.healthy or 0, "diseased": row.diseased or 0}
        for row in trend_result.all()
    ]
    health_trend.reverse()

    return {
        "monthly_scans": monthly_scans,
        "disease_distribution": disease_distribution,
        "health_trend": health_trend,
    }
