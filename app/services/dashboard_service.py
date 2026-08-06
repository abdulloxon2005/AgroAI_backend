from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models import Scan as ScanResult


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(self, user_id: int) -> dict:
        # Total scans
        total = await self.db.scalar(
            select(func.count(ScanResult.id)).where(ScanResult.user_id == user_id)
        )

        # Healthy count
        healthy = await self.db.scalar(
            select(func.count(ScanResult.id)).where(
                ScanResult.user_id == user_id, ScanResult.is_healthy.is_(True)
            )
        )

        diseased = (total or 0) - (healthy or 0)

        # Recent scans
        recent_result = await self.db.execute(
            select(ScanResult)
            .where(ScanResult.user_id == user_id)
            .order_by(ScanResult.created_at.desc())
            .limit(5)
        )
        recent = recent_result.scalars().all()

        # Disease stats
        disease_result = await self.db.execute(
            select(ScanResult.disease_name, func.count(ScanResult.id))
            .where(ScanResult.user_id == user_id, ScanResult.is_healthy.is_(False))
            .group_by(ScanResult.disease_name)
        )
        disease_stats = {name: count for name, count in disease_result.all() if name}

        return {
            "total_scans": total or 0,
            "healthy_plants": healthy or 0,
            "diseased_plants": diseased,
            "recent_scans": recent,
            "disease_stats": disease_stats,
        }
