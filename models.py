from datetime import datetime
from typing import Optional

import bcrypt
from pydantic import EmailStr
from sqlmodel import Field, SQLModel

metadata = SQLModel.metadata


class Products(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    detail: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Attributes(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    value: str
    product_id: int | None = Field(foreign_key="products.id")


class Regions(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    code: str


class RentalPeriods(SQLModel, table=True):
    id: int = Field(primary_key=True)
    month: int


class ProductPricings(SQLModel, table=True):
    id: int = Field(primary_key=True)
    region_id: int = Field(foreign_key="regions.id")
    rental_period_id: int = Field(foreign_key="rentalperiods.id")
    product_id: int = Field(foreign_key="products.id")
    price: int


class User(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    username: str
    email: EmailStr
    hashed_password: str

    def set_password(self, password: str):
        """Hash the password and store it."""
        self.hashed_password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        """Verify the provided password against the stored hashed password."""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )
