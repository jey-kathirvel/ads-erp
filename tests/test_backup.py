from pathlib import Path

import pytest

from app.settings import routes


def test_backup_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(routes, "BACKUP_FOLDER", str(tmp_path))
    assert routes.backup_path("safe.dump") == str(tmp_path / "safe.dump")
    with pytest.raises(ValueError):
        routes.backup_path("../outside.dump")
