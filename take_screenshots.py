#!/usr/bin/env python3.11
"""
Take screenshots of the AbleToCompete MVP demo flow
"""
import subprocess
import time
import os

# Create screenshots directory
os.makedirs("screenshots", exist_ok=True)

print("🎬 Taking Screenshots of AbleToCompete MVP Demo")
print("=" * 50)

# Screenshots to take
screenshots = [
    {
        "url": "http://localhost:3000/login",
        "name": "01_login_page.png",
        "desc": "Login page with beautiful gradient background"
    },
    {
        "url": "http://localhost:3000/",
        "name": "02_dashboard.png",
        "desc": "Dashboard overview"
    },
    {
        "url": "http://localhost:3000/tasks",
        "name": "03_task_boards.png",
        "desc": "Task boards listing"
    },
    {
        "url": "http://localhost:3000/monitoring",
        "name": "04_monitoring.png",
        "desc": "Monitoring dashboard"
    }
]

for i, shot in enumerate(screenshots, 1):
    print(f"\n📸 {i}/{len(screenshots)}: {shot['desc']}")
    print(f"   URL: {shot['url']}")

    # Use Chrome headless mode to take screenshot
    cmd = [
        "google-chrome",
        "--headless",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--screenshot=screenshots/" + shot['name'],
        shot['url']
    ]

    try:
        subprocess.run(cmd, timeout=10, check=True, capture_output=True)
        print(f"   ✅ Saved: screenshots/{shot['name']}")
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  Timeout - page may still be loading")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

    time.sleep(2)  # Wait between screenshots

print("\n" + "=" * 50)
print("✨ Screenshots complete!")
print(f"📁 Check the screenshots/ directory")
print("\nScreenshots taken:")
for shot in screenshots:
    print(f"  • {shot['name']}")
