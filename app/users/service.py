from sqlalchemy.orm import Session

from app.users.models import User
from app.auth.security import PasswordSecurity


class UserService:

    @staticmethod
    def get_all(db: Session):

        return db.query(User).order_by(User.full_name).all()

    @staticmethod
    def get_by_id(db: Session, user_id: int):

        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str):

        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def authenticate(db: Session, email: str, password: str):

        user = (
            db.query(User).filter(User.email == email, User.is_active == True).first()
        )

        if user is None:

            return None

        if not PasswordSecurity.verify_password(password, user.password_hash):

            return None

        return user

    @staticmethod
    def create(db: Session, data):

        existing = UserService.get_by_email(db, data.email)

        if existing:

            return None

        user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=PasswordSecurity.hash_password(data.password),
            role_id=data.role_id,
            is_active=data.is_active,
        )

        db.add(user)

        db.commit()

        db.refresh(user)

        return user

    @staticmethod
    def update(db: Session, user_id: int, data):

        user = UserService.get_by_id(db, user_id)

        if not user:

            return None

        duplicate = (
            db.query(User).filter(User.email == data.email, User.id != user_id).first()
        )

        if duplicate:

            return None

        user.full_name = data.full_name

        user.email = data.email

        user.role_id = data.role_id

        user.is_active = data.is_active

        if hasattr(data, "password"):

            if data.password:

                user.password_hash = PasswordSecurity.hash_password(data.password)

        db.commit()

        db.refresh(user)

        return user

    @staticmethod
    def reset_password(db: Session, user_id: int, password: str):

        user = UserService.get_by_id(db, user_id)

        if not user:

            return None

        user.password_hash = PasswordSecurity.hash_password(password)

        db.commit()

        db.refresh(user)

        return user

    @staticmethod
    def toggle_status(db: Session, user_id: int):

        user = UserService.get_by_id(db, user_id)

        if not user:

            return None

        user.is_active = not user.is_active

        db.commit()

        db.refresh(user)

        return user
