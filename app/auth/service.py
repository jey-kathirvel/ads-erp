from sqlalchemy.orm import Session

from app.users.models import User
from app.auth.models import Role
from app.auth.models import RolePermission

from app.auth.security import PasswordSecurity


class AuthService:

    @staticmethod
    def authenticate(

        db: Session,

        email: str,

        password: str

    ):

        user = (

            db.query(User)

            .filter(

                User.email == email,

                User.is_active == True

            )

            .first()

        )

        if user is None:

            return None

        if not PasswordSecurity.verify_password(

            password,

            user.password_hash

        ):

            return None

        return user

    @staticmethod
    def get_user(

        db: Session,

        user_id: int

    ):

        return (

            db.query(User)

            .filter(

                User.id == user_id

            )

            .first()

        )

    @staticmethod
    def get_role(

        db: Session,

        role_id: int

    ):

        return (

            db.query(Role)

            .filter(

                Role.id == role_id

            )

            .first()

        )
    @staticmethod
    def get_all_roles(

        db: Session

    ):

        return (

            db.query(Role)

            .filter(

                Role.is_active == True

            )

            .order_by(

                Role.role_name

            )

            .all()

        )
    @staticmethod
    def get_permissions(

        db: Session,

        role_id: int

    ):

        return (

            db.query(RolePermission)

            .filter(

                RolePermission.role_id == role_id

            )

            .all()

        )

    @staticmethod
    def has_permission(

        db: Session,

        role_id: int,

        module_name: str,

        action: str = "can_view"

    ):

        permission = (

            db.query(RolePermission)

            .filter(

                RolePermission.role_id == role_id,

                RolePermission.module_name == module_name

            )

            .first()

        )

        if permission is None:

            return False

        if action == "can_view":

            return permission.can_view

        if action == "can_add":

            return permission.can_add

        if action == "can_edit":

            return permission.can_edit

        if action == "can_delete":

            return permission.can_delete

        return False