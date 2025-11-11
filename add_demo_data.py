#!/usr/bin/env python3.11
"""
Add demo data to the database for a compelling video demonstration
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.utils.database import get_db
from app.services.task_service import TaskService


async def add_demo_data():
    """Add comprehensive demo data"""
    print("🚀 Adding demo data to database...")
    print("-" * 50)

    async for db in get_db():
        try:
            # Board 1: Web Development Project (already exists - pokus)
            print("\n📋 Board 1: Using existing 'pokus' board")
            # We'll keep the existing board and add to it

            # Board 2: Mobile App Development
            print("\n📋 Board 2: Creating 'Mobile App Development' board...")
            mobile_board = await TaskService.create_board(
                db,
                name="Mobile App Development",
                description="React Native mobile application for iOS and Android",
                user_id=None
            )

            # Lists for Mobile App
            backlog_list = await TaskService.create_list(db, mobile_board.id, "Backlog", 0)
            design_list = await TaskService.create_list(db, mobile_board.id, "Design", 1)
            development_list = await TaskService.create_list(db, mobile_board.id, "Development", 2)
            testing_list = await TaskService.create_list(db, mobile_board.id, "Testing", 3)
            done_list = await TaskService.create_list(db, mobile_board.id, "Done", 4)

            # Cards for Backlog
            await TaskService.create_card(
                db, backlog_list.id,
                "User authentication flow",
                "Implement OAuth2 and JWT authentication with social login options",
                0
            )
            await TaskService.create_card(
                db, backlog_list.id,
                "Push notifications",
                "Setup Firebase Cloud Messaging for push notifications",
                1
            )
            await TaskService.create_card(
                db, backlog_list.id,
                "Offline mode support",
                "Implement local storage and sync mechanism for offline usage",
                2
            )

            # Cards for Design
            await TaskService.create_card(
                db, design_list.id,
                "Onboarding screens",
                "Design intuitive onboarding flow with animations",
                0
            )
            await TaskService.create_card(
                db, design_list.id,
                "Dark mode theme",
                "Create dark mode color palette and components",
                1
            )

            # Cards for Development
            await TaskService.create_card(
                db, development_list.id,
                "Navigation setup",
                "Configure React Navigation with tab and stack navigators",
                0
            )
            await TaskService.create_card(
                db, development_list.id,
                "API integration",
                "Connect to REST API endpoints with error handling",
                1
            )

            # Cards for Testing
            await TaskService.create_card(
                db, testing_list.id,
                "Unit tests for auth module",
                "Write comprehensive Jest tests for authentication logic",
                0
            )

            # Cards for Done
            await TaskService.create_card(
                db, done_list.id,
                "Project setup",
                "Initialize React Native project with TypeScript",
                0
            )
            await TaskService.create_card(
                db, done_list.id,
                "CI/CD pipeline",
                "Setup GitHub Actions for automated builds and deployments",
                1
            )

            print(f"   ✅ Created 5 lists and 11 cards")

            # Board 3: Marketing Campaign
            print("\n📋 Board 3: Creating 'Q1 Marketing Campaign' board...")
            marketing_board = await TaskService.create_board(
                db,
                name="Q1 Marketing Campaign",
                description="Launch campaign for new product release",
                user_id=None
            )

            # Lists for Marketing
            planning_list = await TaskService.create_list(db, marketing_board.id, "Planning", 0)
            in_progress_list = await TaskService.create_list(db, marketing_board.id, "In Progress", 1)
            review_list = await TaskService.create_list(db, marketing_board.id, "Review", 2)
            published_list = await TaskService.create_list(db, marketing_board.id, "Published", 3)

            # Cards for Planning
            await TaskService.create_card(
                db, planning_list.id,
                "Social media strategy",
                "Plan Instagram, Twitter, and LinkedIn content calendar",
                0
            )
            await TaskService.create_card(
                db, planning_list.id,
                "Email campaign design",
                "Create 3 email templates for product launch sequence",
                1
            )
            await TaskService.create_card(
                db, planning_list.id,
                "Influencer partnerships",
                "Reach out to 10 tech influencers for collaboration",
                2
            )

            # Cards for In Progress
            await TaskService.create_card(
                db, in_progress_list.id,
                "Blog post series",
                "Write 5 technical blog posts about product features",
                0
            )
            await TaskService.create_card(
                db, in_progress_list.id,
                "Video tutorials",
                "Record 3 demo videos for YouTube channel",
                1
            )

            # Cards for Review
            await TaskService.create_card(
                db, review_list.id,
                "Landing page copy",
                "Review and approve landing page content and CTAs",
                0
            )

            # Cards for Published
            await TaskService.create_card(
                db, published_list.id,
                "Press release",
                "Published on TechCrunch and Product Hunt",
                0
            )

            print(f"   ✅ Created 4 lists and 7 cards")

            # Board 4: Infrastructure & DevOps
            print("\n📋 Board 4: Creating 'Infrastructure & DevOps' board...")
            devops_board = await TaskService.create_board(
                db,
                name="Infrastructure & DevOps",
                description="Cloud infrastructure and deployment automation",
                user_id=None
            )

            # Lists for DevOps
            todo_list = await TaskService.create_list(db, devops_board.id, "To Do", 0)
            doing_list = await TaskService.create_list(db, devops_board.id, "Doing", 1)
            completed_list = await TaskService.create_list(db, devops_board.id, "Completed", 2)

            # Cards for To Do
            await TaskService.create_card(
                db, todo_list.id,
                "Kubernetes cluster setup",
                "Setup production-ready K8s cluster on AWS EKS",
                0
            )
            await TaskService.create_card(
                db, todo_list.id,
                "Database backups automation",
                "Configure automated daily backups with 30-day retention",
                1
            )
            await TaskService.create_card(
                db, todo_list.id,
                "Monitoring & alerting",
                "Setup Prometheus and Grafana for system monitoring",
                2
            )

            # Cards for Doing
            await TaskService.create_card(
                db, doing_list.id,
                "Load balancer configuration",
                "Configure Application Load Balancer with SSL termination",
                0
            )
            await TaskService.create_card(
                db, doing_list.id,
                "Security audit",
                "Run security scan and fix vulnerabilities",
                1
            )

            # Cards for Completed
            await TaskService.create_card(
                db, completed_list.id,
                "Docker images optimization",
                "Reduced image sizes by 60% using multi-stage builds",
                0
            )
            await TaskService.create_card(
                db, completed_list.id,
                "CI/CD pipeline setup",
                "Implemented GitOps workflow with ArgoCD",
                1
            )

            print(f"   ✅ Created 3 lists and 7 cards")

            await db.commit()

            print("\n" + "=" * 50)
            print("✨ Demo data added successfully!")
            print("=" * 50)
            print("\n📊 Summary:")
            print(f"   • 4 boards created/updated")
            print(f"   • Multiple lists per board (3-5 lists each)")
            print(f"   • Total: ~30+ cards with descriptions")
            print("\n🎬 Your database is now ready for an impressive demo!")
            print("\n💡 Login with: test@example.com / password123")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            await db.rollback()
            raise
        finally:
            break  # Only iterate once


if __name__ == "__main__":
    asyncio.run(add_demo_data())
