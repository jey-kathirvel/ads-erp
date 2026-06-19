from pydantic import BaseModel


class AccountCreate(BaseModel):

    account_name: str

    account_group: str

    opening_balance: float = 0
