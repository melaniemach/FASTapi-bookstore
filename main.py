import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

app = FastAPI()

# MongoDB connection setup
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["bookstore"]
collection = db["books"]

# Book model
class Book(BaseModel):
    id: int
    title: str
    author: str
    description: str
    price: float
    stock: int
    sold_count: int = 0 

books = [
    {
        "id": 1,
        "title": "Book 1",
        "author": "Author 1",
        "description": "Description 1",
        "price": 9.99,
        "stock": 10,
        "sold_count": 0
    },
    {
        "id": 2,
        "title": "Book 2",
        "author": "Author 2",
        "description": "Description 2",
        "price": 19.99,
        "stock": 5,
        "sold_count": 0
    },
    {
        "id": 3,
        "title": "Book 3",
        "author": "Author 3",
        "description": "Description 3",
        "price": 14.99,
        "stock": 6,
        "sold_count": 0
    }
]

# Inserts books into db
async def insert_books():
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
@app.get("/books")
async def get_books():
    books = await collection.find().to_list(1000)
    return books

# Get a specific book by ID
@app.get("/books/{book_id}")
async def get_book(book_id: int):
    book = await collection.find_one({"id": book_id})
    if book:
        return book
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Add a new book
@app.post("/books")
async def add_book(book: Book):
    book_dict = book.dict()
    inserted_book = await collection.insert_one(book_dict)
    book_id = inserted_book.inserted_id
    return {"message": "Book added successfully", "book_id": book_id}

@app.put("/books/{book_id}")
async def update_book(book_id: int, book: Book):
    book_dict = book.dict(exclude_unset=True)
    updated_book = await collection.update_one({"id": book_id}, {"$set": book_dict})
    if updated_book.modified_count:
        return {"message": "Book updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")
    
# Delete books
@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    deleted_book = await collection.delete_one({"id": book_id})
    if deleted_book.deleted_count:
        return {"message": "Book deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Search books
@app.get("/search", response_model=List[Book])
async def search_books(title: Optional[str] = None, author: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None):
    results = []
    for book in books:
        if title and title.lower() not in book["title"].lower():
            continue
        if author and author.lower() not in book["author"].lower():
            continue
        if min_price and book["price"] < min_price:
            continue
        if max_price and book["price"] > max_price:
            continue
        results.append(book)
        return results
    
# Get the total number of books in the store
@app.get("/stats/total_books")
async def get_total_books():
    total_books = await collection.count_documents({})
    return {"total_books": total_books}

# Buy books
@app.post("/books/{book_id}/buy")
async def buy_book(book_id: str):
    """
    Buys a book if it is in stock.
    """
    book = await collection.find_one({"id": book_id})
    if book:
        if book["stock"] <= 0:
            raise HTTPException(status_code=400, detail="Book is out of stock")

        book["stock"] -= 1
        book["sold_count"] += 1

        updated_book = await collection.update_one({"id": book_id}, {"$set": book})
        if updated_book.modified_count:
            return {"message": "Book bought successfully"}
        else:
            raise HTTPException(status_code=404, detail="Book not found")
    else:
        raise HTTPException(status_code=404, detail="Book not found")


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
