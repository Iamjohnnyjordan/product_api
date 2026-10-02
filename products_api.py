from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
#import the router from products_api.py where the 
from users import router as users_router, get_current_user, require_admin
import models
from database import engine, Base, get_db
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError


Base.metadata.create_all(bind=engine)

class Product(BaseModel):
    product_name: str
    price: float
    quantity: int
    part_number: Optional[str] = None



app = FastAPI()
app.include_router(users_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
### old list to hold products ****products = []
connection = sqlite3.connect("products.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT UNIQUE,
    price REAL,
    quantity INTEGER,
    part_number TEXT UNIQUE
) 
""")
connection.commit()
connection.close()




@app.get("/products/")
def get_products(db = Depends(get_db), current_user = Depends(get_current_user)):
    products = db.query(models.Product).all()
    return products




    

@app.get("/products/{product_name}")
def get_single_product(product_name: str, db = Depends(get_db), current_user = Depends(get_current_user)):
    
    product = db.query(models.Product).filter(
        func.lower(models.Product.product_name) == product_name.lower()
    ).first()


    if product is None:
        return {"error": "Product not found"}

    return {
        
        "product_name": product.product_name,
        "price": product.price,
        "quantity": product.quantity,
        "part_number": product.part_number
        
    
    }



@app.post("/products/")
#def post_products(product: Product,current_user = Depends(get_current_user)): old sqlite code
def post_products(product: Product, db = Depends(get_db), current_user = Depends(get_current_user)):

    new_product = models.Product(
        product_name=product.product_name,
        price=product.price,
        quantity=product.quantity,
        part_number=product.part_number
    )

    if product.part_number is None:
        highest_id = db.query(func.max(models.Product.id)).scalar()

        if highest_id is None:
            next_id = 1
        else:
            next_id = highest_id + 1

        part_number = f"AP-{next_id:05d}"
    else: part_number = product.part_number
    new_product.part_number = part_number


    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return new_product

    except IntegrityError:
        db.rollback()
        return {"error": "product already exists"}
    

#Edit an existing product in the database
@app.put("/products/{product_name}")
def edit_product(product_name: str, product: Product, db=Depends(get_db), current_user = Depends(get_current_user)):
#def edit_product(product_name: str, product: Product, current_user = Depends(get_current_user)):
    existing_product = db.query(models.Product).filter(
        func.lower(models.Product.product_name) == product_name.lower()
    ).first()


    if existing_product is None:
        return {"error": "Product not found"}

    try:

        existing_product.product_name = product.product_name
        existing_product.price = product.price
        existing_product.quantity = product.quantity
        existing_product.part_number = product.part_number
        db.commit()
        db.refresh(existing_product)

        return existing_product

    except IntegrityError:
        db.rollback()
        return {"error": "Product name or part number already exists"}

@app.delete("/products/{product_name}")
def delete_product(product_name: str, current_user = Depends(require_admin)):
    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT product_name FROM products WHERE LOWER(product_name) = ?",
        (product_name.lower(),)
    )

    existing_product = cursor.fetchone()

    if existing_product is None:
        connection.close()
        return{"error": f"{product_name} is not is data base or is mispelled."}

    cursor.execute(
        "DELETE FROM products WHERE LOWER(product_name) = ?",
        (product_name.lower(),)
    )

    connection.commit()
    connection.close()

    return{"complete": f"{product_name} was deleted from the database."}

    








