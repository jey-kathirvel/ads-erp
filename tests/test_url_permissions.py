from app.access_control.service import UrlAccessService


def test_module_path_blocks_root_and_children():
    assert UrlAccessService.matches("/billing", "/billing")
    assert UrlAccessService.matches("/billing", "/billing/list")
    assert UrlAccessService.matches("/billing", "/billing/barcode/product")
    assert not UrlAccessService.matches("/billing", "/billing-old")
    assert not UrlAccessService.matches("/billing", "/inventory")


def test_full_url_and_legacy_wildcard_are_normalized():
    assert UrlAccessService.matches("https://erp.ads-ai.in/inventory/*", "/inventory/current-stock")
    assert UrlAccessService.normalize_pattern("billing/") == "/billing"


def test_path_is_allowed_uses_same_rules_as_sidebar():
    patterns = ["/billing", "/incidents"]
    assert not UrlAccessService.path_is_allowed(patterns, "/billing/list")
    assert not UrlAccessService.path_is_allowed(patterns, "/incidents/new")
    assert UrlAccessService.path_is_allowed(patterns, "/booking")
