from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
#import the router from products_api.py where the 
from users import router as users_router, get_current_user, require_admin


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
def get_products(current_user = Depends(get_current_user)):
    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()

    cursor.execute("SELECT product_name, price, quantity, part_number FROM products")
    products = cursor.fetchall()

    connection.close()
       #shows return info from python more structured
    product_list = []

    for product in products:
        product_list.append({
            "product_name": product[0],
            "price": product[1],
            "quantity": product[2],
            "part_number": product[3]
            })
        

    return product_list



    

@app.get("/products/{product_name}")
def get_single_product(product_name: str, current_user = Depends(get_current_user)):
    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT product_name, price, quantity, part_number FROM products WHERE LOWER(product_name) = ?", 
        (product_name.lower(),)

    )

    product = cursor.fetchone()
    connection.close()

    if product is None:
        return {"error": "Product not found"}

    return {
        "product_name": product[0],
        "price": product[1],
        "quantity": product[2],
        "part_number": product[3]
    
    }



@app.post("/products/")
def post_products(product: Product,current_user = Depends(get_current_user)):
    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()
    if product.part_number is None:
        cursor.execute("SELECT MAX(id) FROM products")
        highest_id = cursor.fetchone()[0]

        if highest_id is None:
            next_id = 1
        else:
            next_id = highest_id + 1

        part_number = f"AP-{next_id:05d}"
    else: part_number = product.part_number
    try:
        cursor.execute(
        "INSERT INTO products (product_name, price, quantity, part_number) VALUES (?, ?, ?, ?)",
        (product.product_name, product.price, product.quantity, part_number)
        )

        connection.commit()
        connection.close()

        return product
 
    
    except sqlite3.IntegrityError:
        connection.close()
        return {"error": "Product already exists"}

#Edit an existing product in the database
@app.put("/products/{product_name}")
def edit_product(product_name: str, product: Product, current_user = Depends(get_current_user)):
    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT product_name, price, quantity, part_number FROM products WHERE LOWER(product_name) = ?",
        (product_name.lower(),)
    )

    existing_product = cursor.fetchone()


    if existing_product is None:
        connection.close()
        return {"error": "Product not found"}

    

    cursor.execute(
        "UPDATE products SET product_name = ?, price = ?, quantity = ?, part_number =? WHERE LOWER(product_name) =?", 
        (product.product_name, product.price, product.quantity, product.part_number, product_name.lower())
    )

    connection.commit()
    connection.close()

    return product


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

    








