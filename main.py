import json
import os
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId

app = FastAPI()

# MongoDB connection setup
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["bookstore"]
collection = db["books"]

# Book model
class Book(BaseModel):
    title: str
    author: str
    description: str
    price: float
    stock: int

# Loads data from a JSON file and inserts into db
async def load_data_from_file(file_path: str):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    absolute_file_path = os.path.join(script_directory, file_path)
    with open(absolute_file_path, "r") as file:
        data = json.load(file)
        await collection.insert_many(data)

@app.on_event("startup")
async def startup():
    await create_indexes()
    await load_data_from_file("books.json")

# Indexes
async def create_indexes():
    await collection.create_index("title")
    await collection.create_index("author")
    await collection.create_index("price")

@app.on_event("startup")
async def startup():
    await create_indexes()

# Routes

# Get all books
@app.get("/books")
async def get_books():
    """
    Retrieves a list of all books in the store.
    """
    books = await collection.find().to_list(length=None)
    return books

# Get a specific book by ID
@app.get("/books/{book_id}")
async def get_book(book_id: str):
    """
    Retrieves a specific book by its ID from the database.
    """
    book = await collection.find_one({"_id": ObjectId(book_id)})
    if book:
        return book
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Add a new book
@app.post("/books")
async def add_book(book: Book):
    """
    Adds a new book to the store.
    """
    book_dict = book.dict()
    inserted_book = await collection.insert_one(book_dict)
    book_id = str(inserted_book.inserted_id)
    return {"message": "Book added successfully", "book_id": book_id}

# Update a book by ID
@app.put("/books/{book_id}")
async def update_book(book_id: str, book: Book):
    """
    Updates an existing book by its ID.
    """
    book_dict = book.dict(exclude_unset=True)
    updated_book = await collection.update_one({"_id": ObjectId(book_id)}, {"$set": book_dict})
    if updated_book.modified_count:
        return {"message": "Book updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Delete a book by ID
@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    """
    Deletes a book from the store by its ID.
    """
    deleted_book = await collection.delete_one({"_id": ObjectId(book_id)})
    if deleted_book.deleted_count:
        return {"message": "Book deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Search for books by title, author, and price range
@app.get("/search")
async def search_books(title: str = None, author: str = None, min_price: float = None, max_price: float = None):
    """
    Searches for books by title, author, and price range.
    """
    query = {}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if author:
        query["author"] = {"$regex": author, "$options": "i"}
    if min_price is not None and max_price is not None:
        query["price"] = {"$gte": min_price, "$lte": max_price}
    elif min_price is not None:
        query["price"] = {"$gte": min_price}
    elif max_price is not None:
        query["price"] = {"$lte": max_price}

    books = await collection.find(query).to_list(length=None)
    return books

# Get the total number of books in the store
@app.get("/stats/total_books")
async def get_total_books():
    """
    Retrieves the total number of books in the store.
    """
    total_books = await collection.count_documents({})
    return {"total_books": total_books}

# Get the top 5 bestselling books
@app.get("/stats/top_selling_books")
async def get_top_selling_books():
    """
    Retrieves the top 5 bestselling books.
    """
    top_selling_books = await collection.find().sort("stock", -1).limit(5).to_list(length=None)
    return top_selling_books

# Get the top 5 authors with the most books in the store
@app.get("/stats/top_authors")
async def get_top_authors():
    """
    Retrieves the top 5 authors with the most books in the store.
    """
    pipeline = [
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_authors = await collection.aggregate(pipeline).to_list(length=None)
    return top_authors


