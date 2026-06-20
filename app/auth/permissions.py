from sqlalchemy.orm import Session

from app.auth.service import AuthService


class Permission:

    @staticmethod
    def can_view(

        db: Session,

        role_id: int,

        module: str

    ):

        return AuthService.has_permission(

            db,

            role_id,

            module,

            "can_view"

        )

    @staticmethod
    def can_add(

        db,

        role_id,

        module

    ):

        return AuthService.has_permission(

            db,

            role_id,

            module,

            "can_add"

        )

    @staticmethod
    def can_edit(

        db,

        role_id,

        module

    ):

        return AuthService.has_permission(

            db,

            role_id,

            module,

            "can_edit"

        )

    @staticmethod
    def can_delete(

        db,

        role_id,

        module

    ):

        return AuthService.has_permission(

            db,

            role_id,

            module,

            "can_delete"

        )