from src.auth_service import AuthError, AuthService
from src.database.json_storage import JsonStorage


def test_register_login_and_verify_token(tmp_path):
    service = AuthService(JsonStorage(tmp_path / "state.json"))
    user, token = service.register("user@example.com", "secret123", "Test User")

    assert user["email"] == "user@example.com"
    assert service.verify(token)["id"] == user["id"]
    logged_in, second_token = service.login("USER@example.com", "secret123")
    assert logged_in["id"] == user["id"]
    assert service.verify(second_token)["email"] == "user@example.com"


def test_auth_rejects_duplicate_and_wrong_password(tmp_path):
    service = AuthService(JsonStorage(tmp_path / "state.json"))
    service.register("user@example.com", "secret123", "Test User")

    try:
        service.register("user@example.com", "secret123", "Other")
        assert False, "duplicate email should fail"
    except AuthError as error:
        assert "đăng ký" in str(error)

    try:
        service.login("user@example.com", "wrongpass")
        assert False, "wrong password should fail"
    except AuthError as error:
        assert "không đúng" in str(error)
