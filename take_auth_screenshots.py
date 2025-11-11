#!/usr/bin/env python3.11
"""
Take authenticated screenshots of AbleToCompete MVP
"""
from playwright.sync_api import sync_playwright
import time
import os

# Create screenshots directory
os.makedirs("screenshots", exist_ok=True)

print("🎬 Taking Authenticated Screenshots of AbleToCompete MVP")
print("=" * 60)

with sync_playwright() as p:
    # Launch browser
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    try:
        # Step 1: Login page
        print("\n📸 1/6: Taking Login Page screenshot...")
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path="screenshots/01_login_page.png")
        print("   ✅ Saved: screenshots/01_login_page.png")

        # Step 2: Perform login
        print("\n🔐 Logging in...")
        page.fill('input[type="email"]', "test@example.com")
        page.fill('input[type="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_url("http://localhost:3000/", timeout=5000)
        time.sleep(2)  # Wait for data to load

        # Step 3: Dashboard
        print("\n📸 2/6: Taking Dashboard screenshot...")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="screenshots/02_dashboard.png")
        print("   ✅ Saved: screenshots/02_dashboard.png")

        # Step 4: Task Boards List
        print("\n📸 3/6: Taking Task Boards List screenshot...")
        page.click('a[href="/tasks"]')
        page.wait_for_url("**/tasks")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path="screenshots/03_task_boards_list.png")
        print("   ✅ Saved: screenshots/03_task_boards_list.png")

        # Step 5: Open Mobile App Board
        print("\n📸 4/6: Taking Mobile App Board screenshot...")
        # Click the second board (Mobile App Development)
        page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.card');
                if (cards.length >= 2) {
                    cards[1].click();
                }
            }
        """)
        time.sleep(3)  # Wait for board to load
        page.screenshot(path="screenshots/04_mobile_app_board.png", full_page=False)
        print("   ✅ Saved: screenshots/04_mobile_app_board.png")

        # Step 6: Monitoring
        print("\n📸 5/6: Taking Monitoring Dashboard screenshot...")
        page.click('a[href="/monitoring"]')
        page.wait_for_url("**/monitoring")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path="screenshots/05_monitoring.png")
        print("   ✅ Saved: screenshots/05_monitoring.png")

        # Step 7: Back to task boards for final shot
        print("\n📸 6/6: Taking Final Overview screenshot...")
        page.click('a[href="/tasks"]')
        page.wait_for_url("**/tasks")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path="screenshots/06_boards_overview.png")
        print("   ✅ Saved: screenshots/06_boards_overview.png")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

print("\n" + "=" * 60)
print("✨ Screenshot session complete!")
print(f"📁 All screenshots saved in: screenshots/")
print("\n📸 Screenshots taken:")
print("  1. Login page")
print("  2. Dashboard")
print("  3. Task boards list")
print("  4. Mobile App Development board")
print("  5. Monitoring dashboard")
print("  6. Boards overview")
