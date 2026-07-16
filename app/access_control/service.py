from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.access_control.models import UserUrlBlock


class UrlAccessService:

    @staticmethod
    def normalize_pattern(value: str) -> str:
        value = (value or "").strip()

        if not value:
            raise ValueError(
                "URL pattern cannot be empty"
            )

        wildcard = value.endswith("/*")

        base_value = (
            value[:-2]
            if wildcard
            else value
        )

        parsed = urlsplit(base_value)

        if parsed.scheme or parsed.netloc:
            path = parsed.path or "/"
        else:
            path = base_value

        if not path.startswith("/"):
            path = "/" + path

        if len(path) > 1:
            path = path.rstrip("/")

        if wildcard:
            if path == "/":
                return "/*"

            return path + "/*"

        return path

    @staticmethod
    def normalize_request_path(
        value: str,
    ) -> str:
        value = (value or "").strip()

        if not value:
            return "/"

        parsed = urlsplit(value)

        if parsed.scheme or parsed.netloc:
            path = parsed.path or "/"
        else:
            path = value.split("?", 1)[0]
            path = path.split("#", 1)[0]

        if not path.startswith("/"):
            path = "/" + path

        if len(path) > 1:
            path = path.rstrip("/")

        return path

    @classmethod
    def matches(
        cls,
        url_pattern: str,
        request_path: str,
    ) -> bool:

        pattern = cls.normalize_pattern(
            url_pattern
        )

        path = cls.normalize_request_path(
            request_path
        )

        if pattern == "/*":
            return True

        # A block is a route subtree by default. Blocking `/billing` therefore
        # protects `/billing`, `/billing/list`, `/billing/barcode`, etc. The
        # legacy `/*` suffix remains supported for existing records.
        prefix = pattern[:-2] if pattern.endswith("/*") else pattern

        return path == prefix or path.startswith(prefix + "/")

    @classmethod
    def path_is_allowed(cls, patterns: list[str], request_path: str) -> bool:
        return not any(cls.matches(pattern, request_path) for pattern in patterns)

    @staticmethod
    def get_active_blocks(
        db: Session,
        user_id: int,
    ):
        return (
            db.query(UserUrlBlock)
            .filter(
                UserUrlBlock.user_id
                == user_id,
                UserUrlBlock.is_active
                == True,
            )
            .order_by(
                UserUrlBlock.id.asc()
            )
            .all()
        )

    @classmethod
    def get_active_patterns(cls, db: Session, user_id: int) -> list[str]:
        return [block.url_pattern for block in cls.get_active_blocks(db, user_id)]

    @classmethod
    def is_blocked(
        cls,
        db: Session,
        user_id: int,
        request_path: str,
    ) -> bool:

        patterns = cls.get_active_patterns(db, user_id)
        return not cls.path_is_allowed(patterns, request_path)
