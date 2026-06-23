from sqlalchemy.orm import Session

from app.auth.models import Role
from app.auth.models import RolePermission

from app.roles.schemas import RoleCreate
from app.roles.schemas import RoleUpdate


class RoleService:

    # ----------------------------------------------------
    # Get All Roles
    # ----------------------------------------------------

    @staticmethod
    def get_all(db: Session):

        return db.query(Role).order_by(Role.role_name).all()

    # ----------------------------------------------------
    # Get Role
    # ----------------------------------------------------

    @staticmethod
    def get_by_id(db: Session, role_id: int):

        return db.query(Role).filter(Role.id == role_id).first()

    # ----------------------------------------------------
    # Create Role
    # ----------------------------------------------------

    @staticmethod
    def create(db: Session, data: RoleCreate):

        existing = db.query(Role).filter(Role.role_code == data.role_code).first()

        if existing:

            return None

        role = Role(
            role_code=data.role_code,
            role_name=data.role_name,
            description=data.description,
            is_active=data.is_active,
        )

        db.add(role)

        db.commit()

        db.refresh(role)

        return role

    # ----------------------------------------------------
    # Update Role
    # ----------------------------------------------------

    @staticmethod
    def update(db: Session, role_id: int, data: RoleUpdate):

        role = RoleService.get_by_id(db, role_id)

        if role is None:

            return None

        role.role_code = data.role_code

        role.role_name = data.role_name

        role.description = data.description

        role.is_active = data.is_active

        db.commit()

        db.refresh(role)

        return role

    # ----------------------------------------------------
    # Enable / Disable
    # ----------------------------------------------------

    @staticmethod
    def toggle_status(db: Session, role_id: int):

        role = RoleService.get_by_id(db, role_id)

        if role is None:

            return None

        role.is_active = not role.is_active

        db.commit()

        db.refresh(role)

        return role

    # ----------------------------------------------------
    # Permissions
    # ----------------------------------------------------

    @staticmethod
    def get_permissions(db: Session, role_id: int):

        return (
            db.query(RolePermission)
            .filter(RolePermission.role_id == role_id)
            .order_by(RolePermission.module_name)
            .all()
        )

    # ----------------------------------------------------
    # Save Permissions
    # ----------------------------------------------------

    @staticmethod
    def save_permission(
        db: Session,
        role_id: int,
        module_name: str,
        can_view: bool,
        can_add: bool,
        can_edit: bool,
        can_delete: bool,
    ):

        permission = (
            db.query(RolePermission)
            .filter(
                RolePermission.role_id == role_id,
                RolePermission.module_name == module_name,
            )
            .first()
        )

        if permission is None:

            permission = RolePermission(
                role_id=role_id,
                module_name=module_name,
                can_view=can_view,
                can_add=can_add,
                can_edit=can_edit,
                can_delete=can_delete,
            )

            db.add(permission)

        else:

            permission.can_view = can_view

            permission.can_add = can_add

            permission.can_edit = can_edit

            permission.can_delete = can_delete

        db.commit()

        return permission
