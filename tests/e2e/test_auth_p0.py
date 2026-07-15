import pytest
from playwright.sync_api import Page, expect


pytestmark = [pytest.mark.p0, pytest.mark.e2e]


def test_login_page_and_password_toggle(app_page: Page, qa_base_url: str):
    app_page.goto(f"{qa_base_url}/login")
    expect(app_page.get_by_role("heading", name="Welcome back")).to_be_visible()
    password = app_page.get_by_label("Password", exact=True)
    expect(password).to_have_attribute("type", "password")
    app_page.get_by_role("button", name="Show password").click()
    expect(password).to_have_attribute("type", "text")


def test_invalid_login_is_rejected(app_page: Page, qa_base_url: str):
    app_page.goto(f"{qa_base_url}/login")
    app_page.get_by_label("Email address").fill("p0-invalid@ads-ai.in")
    app_page.get_by_label("Password", exact=True).fill("definitely-invalid")
    app_page.get_by_role("button", name="Sign in securely").click()
    expect(app_page.get_by_role("alert")).to_contain_text("Invalid Email or Password")
    expect(app_page).to_have_url(f"{qa_base_url}/login")


@pytest.mark.parametrize(
    "path",
    ["/dashboard", "/billing/list", "/booking", "/inventory/dashboard", "/settings/backup", "/users"],
)
def test_protected_pages_redirect_to_login(app_page: Page, qa_base_url: str, path: str):
    app_page.goto(f"{qa_base_url}{path}")
    expect(app_page).to_have_url(f"{qa_base_url}/login")


def test_authenticated_session_can_logout(authenticated_page: Page, qa_base_url: str):
    authenticated_page.goto("/dashboard")
    authenticated_page.goto("/logout")
    expect(authenticated_page).to_have_url(f"{qa_base_url}/login")
