import pytest
from playwright.sync_api import Page, expect


pytestmark = [pytest.mark.p0, pytest.mark.e2e]


@pytest.mark.parametrize(
    "path",
    [
        "/dashboard",
        "/billing/list",
        "/booking",
        "/reports/booking",
        "/inventory/dashboard",
        "/inventory/current-stock",
        "/settings/backup",
        "/users",
    ],
)
def test_admin_critical_page_smoke(authenticated_page: Page, qa_base_url: str, path: str):
    response = authenticated_page.goto(path, wait_until="domcontentloaded")
    assert response is not None and response.ok, f"{path} returned {response.status if response else 'no response'}"
    expect(authenticated_page).not_to_have_url(f"{qa_base_url}/login")
    expect(authenticated_page.locator("body")).to_be_visible()
    expect(authenticated_page.locator("body")).not_to_contain_text("Internal Server Error")
