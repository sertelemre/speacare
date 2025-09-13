import re
import time
from playwright.sync_api import sync_playwright, Page, expect

def run(page: Page):
    # Give the dev server time to start
    time.sleep(10)
    """
    This script verifies the full bot management workflow.
    """
    # 1. Start at the login page
    page.goto("http://localhost:3000/login")

    # 2. Log in
    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("testpassword")
    page.get_by_role("button", name="Login").click()

    # 3. Navigate to the Bot Management page
    # Expect the main page to load, then click the link.
    expect(page.get_by_role("heading", name="Channels")).to_be_visible()
    page.get_by_role("link", name="My Bots").click()

    # 4. Verify we are on the bots page and click "Create New Bot"
    expect(page.get_by_role("heading", name="My Bots")).to_be_visible()
    page.get_by_role("button", name="Create New Bot").click()

    # 5. Fill out the form to create a new bot
    expect(page.get_by_role("heading", name="Create a New Bot")).to_be_visible()

    bot_name = "Test Playwright Bot"
    page.get_by_label("Bot Name").fill(bot_name)
    page.get_by_label("Bot Title / Persona").fill("A bot created by a Playwright script")

    # Select provider
    page.get_by_label("LLM Provider").click()
    page.get_by_role("option", name="Groq").click()

    # Select model (wait for it to be enabled)
    model_select = page.get_by_label("Model")
    expect(model_select).to_be_enabled()
    model_select.click()
    page.get_by_role("option", name="llama3-8b-8192").click()

    # Submit the form
    page.get_by_role("button", name="Create Bot").click()

    # 6. Verify the new bot appears in the list
    # The dialog should close, and the new bot card should be visible.
    expect(page.get_by_role("heading", name=bot_name)).to_be_visible()

    print("Bot created successfully and visible on the page.")

    # 7. Take a screenshot
    page.screenshot(path="jules-scratch/verification/bot_management.png")
    print("Screenshot taken.")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run(page)
        browser.close()

if __name__ == "__main__":
    main()
