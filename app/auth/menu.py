from sqlalchemy.orm import Session

from app.auth.service import AuthService


class MenuService:

    @staticmethod
    def can_view(db: Session, request, module: str):

        user = request.session.get("user")

        if not user:

            return False

        return AuthService.has_permission(
            db=db, role_id=user["role_id"], module_name=module, action="can_view"
        )
