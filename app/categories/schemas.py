from pydantic import BaseModel


class CategoryCreate(BaseModel):

    category_name: str

    description: str | None = None
