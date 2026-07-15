import pytest
from playwright.sync_api import Playwright


pytestmark = [pytest.mark.p0, pytest.mark.e2e]


def test_health_endpoint(playwright: Playwright, qa_base_url: str):
    request = playwright.request.new_context(base_url=qa_base_url)
    try:
        response = request.get("/health")
        assert response.ok
        payload = response.json()
        assert payload["application"] == "ADS ERP"
        assert payload["status"] == "running"
    finally:
        request.dispose()
