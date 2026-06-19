from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.users.models import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class UserService:

    @staticmethod
    def authenticate(

        db: Session,

        email: str,

        password: str

    ):

        user = (

            db.query(User)

            .filter(

                User.email == email

            )

            .first()

        )

        if user is None:

            return None

        if not pwd_context.verify(

            password,

            user.password_hash

        ):

            return None

        return user

    @staticmethod
    def hash_password(password: str):

        return pwd_context.hash(password)