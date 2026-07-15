import os
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect


def pytest_collection_modifyitems(items):
    if os.getenv("QA_ALLOW_MUTATIONS", "false").lower() == "true":
        return
    blocked = pytest.mark.skip(reason="Set QA_ALLOW_MUTATIONS=true on an isolated QA database")
    for item in items:
        if "mutation" in item.keywords:
            item.add_marker(blocked)


def pytest_addoption(parser):
    parser.addoption(
        "--qa-base-url",
        action="store",
        default=os.getenv("QA_BASE_URL", "http://127.0.0.1:8000"),
        help="ADS ERP environment used by browser tests",
    )


@pytest.fixture(scope="session")
def qa_base_url(pytestconfig) -> str:
    return pytestconfig.getoption("--qa-base-url").rstrip("/")


@pytest.fixture
def app_page(page: Page, qa_base_url: str) -> Page:
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def authenticated_context(browser: Browser, qa_base_url: str) -> Generator[BrowserContext, None, None]:
    email = os.getenv("QA_ADMIN_EMAIL")
    password = os.getenv("QA_ADMIN_PASSWORD")
    if not email or not password:
        pytest.skip("QA_ADMIN_EMAIL and QA_ADMIN_PASSWORD are required for authenticated P0 tests")

    context = browser.new_context(base_url=qa_base_url)
    page = context.new_page()
    page.goto("/login")
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Sign in securely").click()
    expect(page).to_have_url(f"{qa_base_url}/dashboard")
    yield context
    context.close()


@pytest.fixture
def authenticated_page(authenticated_context: BrowserContext) -> Generator[Page, None, None]:
    page = authenticated_context.new_page()
    page.set_default_timeout(10_000)
    yield page
    page.close()
