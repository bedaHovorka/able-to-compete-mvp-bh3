#!/usr/bin/env python3.11
"""
Add monitoring demo data for demonstration
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.utils.database import get_db
from app.models.monitoring import Monitor, MonitorType, MonitorStatus, Check
import uuid


async def add_monitoring_data():
    """Add monitoring demo data"""
    print("🚀 Adding monitoring demo data...")
    print("-" * 50)

    async for db in get_db():
        try:
            # Monitor 1: API Health Check
            print("\n📡 Monitor 1: Creating API health check...")
            api_monitor = Monitor(
                id=uuid.uuid4(),
                name="Backend API Health",
                type=MonitorType.HTTPS,
                url="http://localhost:8005/docs",
                interval=60,
                timeout=5000,
                status=MonitorStatus.UP,
                enabled=True,
                expected_status_code=200
            )
            db.add(api_monitor)

            # Add some checks for this monitor
            for i in range(10):
                check_time = datetime.utcnow() - timedelta(minutes=i*5)
                check = Check(
                    id=uuid.uuid4(),
                    monitor_id=api_monitor.id,
                    status=MonitorStatus.UP if random.random() > 0.1 else MonitorStatus.DOWN,
                    response_time=random.uniform(50, 200),
                    status_code=200 if random.random() > 0.1 else 500,
                    checked_at=check_time
                )
                db.add(check)

            # Monitor 2: Frontend Health
            print("📡 Monitor 2: Creating frontend health check...")
            frontend_monitor = Monitor(
                id=uuid.uuid4(),
                name="Frontend Application",
                type=MonitorType.HTTP,
                url="http://localhost:3000",
                interval=60,
                timeout=5000,
                status=MonitorStatus.UP,
                enabled=True,
                expected_status_code=200
            )
            db.add(frontend_monitor)

            # Add checks
            for i in range(10):
                check_time = datetime.utcnow() - timedelta(minutes=i*5)
                check = Check(
                    id=uuid.uuid4(),
                    monitor_id=frontend_monitor.id,
                    status=MonitorStatus.UP,
                    response_time=random.uniform(20, 100),
                    status_code=200,
                    checked_at=check_time
                )
                db.add(check)

            # Monitor 3: Database Connection
            print("📡 Monitor 3: Creating database monitor...")
            db_monitor = Monitor(
                id=uuid.uuid4(),
                name="PostgreSQL Database",
                type=MonitorType.TCP,
                url="localhost:5432",
                interval=120,
                timeout=3000,
                status=MonitorStatus.UP,
                enabled=True
            )
            db.add(db_monitor)

            # Add checks
            for i in range(8):
                check_time = datetime.utcnow() - timedelta(minutes=i*10)
                check = Check(
                    id=uuid.uuid4(),
                    monitor_id=db_monitor.id,
                    status=MonitorStatus.UP,
                    response_time=random.uniform(5, 20),
                    checked_at=check_time
                )
                db.add(check)

            # Monitor 4: External API (Degraded)
            print("📡 Monitor 4: Creating external API monitor...")
            external_monitor = Monitor(
                id=uuid.uuid4(),
                name="External Weather API",
                type=MonitorType.HTTPS,
                url="https://api.weather.com/v1/health",
                interval=300,
                timeout=10000,
                status=MonitorStatus.DEGRADED,
                enabled=True,
                expected_status_code=200
            )
            db.add(external_monitor)

            # Add checks with some degraded performance
            for i in range(10):
                check_time = datetime.utcnow() - timedelta(minutes=i*20)
                is_slow = random.random() > 0.4
                check = Check(
                    id=uuid.uuid4(),
                    monitor_id=external_monitor.id,
                    status=MonitorStatus.DEGRADED if is_slow else MonitorStatus.UP,
                    response_time=random.uniform(2000, 5000) if is_slow else random.uniform(100, 500),
                    status_code=200,
                    checked_at=check_time
                )
                db.add(check)

            # Monitor 5: Payment Gateway (Down)
            print("📡 Monitor 5: Creating payment gateway monitor...")
            payment_monitor = Monitor(
                id=uuid.uuid4(),
                name="Payment Gateway",
                type=MonitorType.HTTPS,
                url="https://api.payment-gateway.com/status",
                interval=60,
                timeout=5000,
                status=MonitorStatus.DOWN,
                enabled=True,
                expected_status_code=200
            )
            db.add(payment_monitor)

            # Add checks with recent downtime
            for i in range(5):
                check_time = datetime.utcnow() - timedelta(minutes=i*3)
                check = Check(
                    id=uuid.uuid4(),
                    monitor_id=payment_monitor.id,
                    status=MonitorStatus.DOWN,
                    response_time=None,
                    status_code=None,
                    error_message="Connection timeout" if i < 3 else "Service unavailable",
                    checked_at=check_time
                )
                db.add(check)

            # Monitor 6: Redis Cache (Paused)
            print("📡 Monitor 6: Creating Redis monitor...")
            redis_monitor = Monitor(
                id=uuid.uuid4(),
                name="Redis Cache",
                type=MonitorType.TCP,
                url="localhost:6379",
                interval=60,
                timeout=2000,
                status=MonitorStatus.PAUSED,
                enabled=False
            )
            db.add(redis_monitor)

            await db.commit()

            print("\n" + "=" * 50)
            print("✨ Monitoring demo data added successfully!")
            print("=" * 50)
            print("\n📊 Summary:")
            print(f"   • 6 monitors created")
            print(f"   • 4 UP/DEGRADED, 1 DOWN, 1 PAUSED")
            print(f"   • ~50+ health checks in history")
            print(f"   • Real-time monitoring data ready!")
            print("\n🎬 Monitoring dashboard is now ready for demo!")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise
        finally:
            break


if __name__ == "__main__":
    asyncio.run(add_monitoring_data())
