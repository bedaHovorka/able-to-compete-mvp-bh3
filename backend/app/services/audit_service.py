from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import select
from app.utils.database import Base
from app.utils.logger import logger
from typing import Optional, Dict, Any, List as ListType
from datetime import datetime, timedelta
import uuid
import json


class AuditLog(Base):
    """Audit log model for compliance tracking"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    method = Column(String(10), nullable=True)  # HTTP method
    endpoint = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_body = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True)
    changes = Column(JSON, nullable=True)  # Before/after values
    details = Column(Text, nullable=True)


class AuditService:
    @staticmethod
    async def log_request(
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_body: Optional[Dict] = None,
        response_status: Optional[int] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """Log an API request for audit trail"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            method=method,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            request_body=request_body,
            response_status=response_status,
            details=details
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        logger.info(f"Audit log created: {action} on {resource_type}")
        return audit_log

    @staticmethod
    async def log_data_change(
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> AuditLog:
        """Log data modifications with before/after values"""
        changes = {
            "before": before,
            "after": after
        }

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            details=f"Data modification: {action}"
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        logger.info(f"Data change logged: {action} on {resource_type}:{resource_id}")
        return audit_log

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> ListType[AuditLog]:
        """Query audit logs with filters"""
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if action:
            query = query.where(AuditLog.action == action)
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)

        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_resource_history(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID
    ) -> ListType[AuditLog]:
        """Get complete audit history for a specific resource"""
        query = select(AuditLog).where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(AuditLog.timestamp.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def cleanup_old_logs(db: AsyncSession, retention_days: int = 90):
        """Clean up audit logs older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        query = select(AuditLog).where(AuditLog.timestamp < cutoff_date)
        result = await db.execute(query)
        old_logs = result.scalars().all()

        count = len(old_logs)
        for log in old_logs:
            await db.delete(log)

        await db.commit()
        logger.info(f"Cleaned up {count} audit logs older than {retention_days} days")

        return count
