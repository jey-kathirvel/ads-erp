from sqlalchemy.orm import Session

from app.categories.models import Category
from app.categories.schemas import CategoryCreate


class CategoryService:

    @staticmethod
    def get_all(db: Session):

        return (
            db.query(Category)
            .order_by(Category.category_name)
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        data: CategoryCreate
    ):

        count = db.query(Category).count() + 1

        category = Category(

            category_code=f"CAT{count:03}",

            category_name=data.category_name,

            description=data.description

        )

        db.add(category)

        db.commit()

        db.refresh(category)

        return category
