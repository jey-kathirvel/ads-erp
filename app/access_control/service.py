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

        if pattern.endswith("/*"):
            prefix = pattern[:-2]

            return (
                path == prefix
                or path.startswith(
                    prefix + "/"
                )
            )

        return path == pattern

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
    def is_blocked(
        cls,
        db: Session,
        user_id: int,
        request_path: str,
    ) -> bool:

        blocks = cls.get_active_blocks(
            db,
            user_id,
        )

        return any(
            cls.matches(
                block.url_pattern,
                request_path,
            )
            for block in blocks
        )
