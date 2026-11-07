import os
import time
from playwright.sync_api import sync_playwright

output_dir = r"C:\Users\MY PC\Desktop\project medicine\screenshots"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 850})
    page = context.new_page()

    # 1. Index Page
    page.goto("http://127.0.0.1:8000/index.html")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(output_dir, "01_home_page.png"))
    print("Captured 01_home_page.png")

    # 2. Register Page
    page.goto("http://127.0.0.1:8000/register.html")
    page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(output_dir, "02_register_page.png"))
    print("Captured 02_register_page.png")

    # 3. Login Page
    page.goto("http://127.0.0.1:8000/login.html")
    page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(output_dir, "03_login_page.png"))
    print("Captured 03_login_page.png")

    # Log in as test user
    page.fill("#email", "sarah.jenkins@example.com")
    page.fill("#password", "password123")
    page.click("#loginBtn")
    page.wait_for_url("**/dashboard.html", timeout=6000)
    page.wait_for_timeout(1500)

    # 4. Dashboard Page
    page.screenshot(path=os.path.join(output_dir, "04_dashboard_page.png"))
    print("Captured 04_dashboard_page.png")

    # 5. Add Medicine Page
    page.goto("http://127.0.0.1:8000/add_medicine.html")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(output_dir, "05_add_medicine_page.png"))
    print("Captured 05_add_medicine_page.png")

    # 6. Medicine List Page
    page.goto("http://127.0.0.1:8000/medicine_list.html")
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(output_dir, "06_medicine_list_page.png"))
    print("Captured 06_medicine_list_page.png")

    # 7. Schedule Page
    page.goto("http://127.0.0.1:8000/schedule.html")
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(output_dir, "07_schedule_page.png"))
    print("Captured 07_schedule_page.png")

    # 8. Reminders Page
    page.goto("http://127.0.0.1:8000/reminders.html")
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(output_dir, "08_reminders_page.png"))
    print("Captured 08_reminders_page.png")

    # 9. History Page
    page.goto("http://127.0.0.1:8000/history.html")
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(output_dir, "09_history_page.png"))
    print("Captured 09_history_page.png")

    # 10. Profile Page
    page.goto("http://127.0.0.1:8000/profile.html")
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(output_dir, "10_profile_page.png"))
    print("Captured 10_profile_page.png")

    # 11. Logout Page
    page.goto("http://127.0.0.1:8000/logout.html")
    page.wait_for_timeout(600)
    page.screenshot(path=os.path.join(output_dir, "11_logout_page.png"))
    print("Captured 11_logout_page.png")

    browser.close()
    print("All screenshots captured successfully!")
