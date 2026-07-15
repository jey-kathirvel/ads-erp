from app.auth.security import PasswordSecurity


def test_password_hash_round_trip():
    hashed = PasswordSecurity.hash_password("StrongPassword-2026")
    assert hashed != "StrongPassword-2026"
    assert PasswordSecurity.verify_password("StrongPassword-2026", hashed)
    assert not PasswordSecurity.verify_password("wrong", hashed)
