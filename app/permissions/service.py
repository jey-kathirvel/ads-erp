from sqlalchemy.orm import Session

from app.auth.models import Role
from app.auth.models import RolePermission


class PermissionService:

    @staticmethod
    def get_roles(db: Session):

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

        permissions = (

            db.query(RolePermission)

            .filter(

                RolePermission.role_id == role_id

            )

            .all()

        )

        result = {}

        for item in permissions:

            result[item.module_name] = {

                "can_view": item.can_view,

                "can_add": item.can_add,

                "can_edit": item.can_edit,

                "can_delete": item.can_delete

            }

        return result

    @staticmethod
    def save(

        db: Session,

        role_id: int,

        module_name: str,

        can_view: bool,

        can_add: bool,

        can_edit: bool,

        can_delete: bool

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

            permission = RolePermission(

                role_id=role_id,

                module_name=module_name

            )

            db.add(permission)

        permission.can_view = can_view
        permission.can_add = can_add
        permission.can_edit = can_edit
        permission.can_delete = can_delete

        db.commit()