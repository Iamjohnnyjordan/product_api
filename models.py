#what are DB tables look like 

from database import Base
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String, unique=True)
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer)
    part_number: Mapped[str] = mapped_column(String, unique=True)








