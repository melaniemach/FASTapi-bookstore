import logging
import uuid
import pprint
from pymongo import MongoClient
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
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
    id: Optional[str]
    title: str
    author: str
    description: str
    price: float
    stock: int
    sold_count: int = 0 

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

books = [
    {
        "id": str(uuid.uuid4()),
        "title": "Book 1",
        "author": "Author 1",
        "description": "Description 1",
        "price": 9.99,
        "stock": 10,
        "sold_count": 0
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Book 2",
        "author": "Author 2",
        "description": "Description 2",
        "price": 19.99,
        "stock": 5,
        "sold_count": 0
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Book 3",
        "author": "Author 3",
        "description": "Description 3",
        "price": 14.99,
        "stock": 6,
        "sold_count": 0
    }
]

pprint.pprint(books)

# Inserts books into db
async def insert_books():
    for book in books:
        book["_id"] = book["id"]
        del book["id"]
    await collection.insert_many(books)

# Indexes
async def create_indexes():
    await collection.create_index("title")
    await collection.create_index("author")
    await collection.create_index("price")
    await collection.create_index("sold_count")

logger = logging.getLogger("uvicorn.error")

# The startup function
@app.on_event("startup")
async def startup():
    logger.info("Starting up...")
    try:
        await create_indexes()
        logger.info("Indexes created.")
        await insert_books()
        logger.info("Books inserted into database.")
    except Exception as e:
        logger.error(f"An error occurred during startup: {e}")
        raise

# Routes

# Get all books
@app.get("/books", response_model=List[Book])
async def get_books():
    books = await collection.find().to_list(1000)
    return [{**book, "id": str(book["_id"])} for book in books]

# Get a specific book by ID
@app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str):
    book = await collection.find_one({"_id": ObjectId(book_id)})
    if book:
        return {**book, "id": str(book["_id"])}
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Add a new book
@app.post("/books")
async def add_book(book: Book):
    book_dict = book.dict()
    book_id = book_dict.get("id")
    
    # Check if a book with the same ID already exists
    existing_book = await collection.find_one({"_id": book_id})
    if existing_book:
        raise HTTPException(status_code=400, detail="Book with the same ID already exists")

    inserted_book = await collection.insert_one(book_dict)
    book_id = str(inserted_book.inserted_id)
    return {"message": "Book added successfully", "book_id": book_id}


# Update book
@app.put("/books/{book_id}")
async def update_book(book_id: str, book: Book):
    print(book.dict())   
    book_dict = book.dict(exclude_unset=True)
    updated_book = await collection.update_one({"_id": ObjectId(book_id)}, {"$set": book_dict})
    if updated_book.modified_count:
        return {"message": "Book updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")
   
# Delete books
@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    deleted_book = await collection.delete_one({"_id": ObjectId(book_id)})
    if deleted_book.deleted_count:
        return {"message": "Book deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")
    
# Search books
@app.get("/search", response_model=List[Book])
async def search_books(title: Optional[str] = None, author: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None):
    query = {}

    if title:
        query["title"] = {"$regex": f".*{title}.*", "$options": "i"}
    if author:
        query["author"] = {"$regex": f".*{author}.*", "$options": "i"}
    if min_price:
        if "price" not in query:
            query["price"] = {}
        query["price"]["$gte"] = min_price
    if max_price:
        if "price" not in query:
            query["price"] = {}
        query["price"]["$lte"] = max_price

    results = await collection.find(query).to_list(1000)
    return results

# Buy books
@app.post("/books/{book_id}/buy")
async def buy_book(book_id: str):
    """
    Buys a book if it is in stock.
    """
    updated_book = await collection.find_one_and_update(
        {"_id": ObjectId(book_id), "stock": {"$gt": 0}},
        {"$inc": {"stock": -1, "sold_count": 1}}
    )
    if updated_book:
        return {"message": "Book bought successfully"}
    else:
        book = await collection.find_one({"_id": ObjectId(book_id)})
        if book:
            raise HTTPException(status_code=400, detail="Book is out of stock")
        else:
            raise HTTPException(status_code=404, detail="Book not found")
        
# Get the total number of books in the store
@app.get("/stats/total_books")
async def get_total_books():
    total_books = await collection.count_documents({})
    return {"total_books": total_books}

# Get the top 5 bestselling books
@app.get("/stats/top_selling_books")
async def get_top_selling_books():
    pipeline = [
        {"$sort": {"sold_count": -1}},
        {"$limit": 5}
    ]
    top_selling_books = await collection.aggregate(pipeline).to_list(length=None)
    return [{**book, "_id": str(book["_id"])} for book in top_selling_books]

# Get the top 5 authors with the most books in the store
@app.get("/stats/top_authors")
async def get_top_authors():
    pipeline = [
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_authors = await collection.aggregate(pipeline).to_list(length=None)
    return top_authors
