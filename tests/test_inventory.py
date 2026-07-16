from unittest.mock import MagicMock

from app.inventory.service import InventoryService


def test_low_stock_returns_filtered_products():
    db = MagicMock()
    expected = [object(), object()]
    db.query.return_value.filter.return_value.all.return_value = expected
    assert InventoryService.get_low_stock(db) == expected
    db.query.return_value.filter.assert_called_once()
