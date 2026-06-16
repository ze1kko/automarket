from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import shutil
import os
import database

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

if not os.path.exists("static/images"):
    os.makedirs("static/images")

app.mount("/static", StaticFiles(directory="static"), name="static")

database.create_db()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    username: str
    password: str
    phone: str

class ReviewCreate(BaseModel):
    text: str
    rating: int
    seller_id: int
    author_id: int

@app.get("/")
def home():
    return FileResponse("templates/index.html")

@app.get("/login")
def login_page():
    return FileResponse("templates/login.html")

@app.get("/car/{car_id}")
def get_car_page(car_id: int):
    return FileResponse("templates/car_detail.html")

@app.get("/admin")
def admin_page():
    return FileResponse("templates/admin.html")

@app.get("/profile")
def profile_page():
    return FileResponse("templates/profile.html")

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(database.User).filter(database.User.username == user.username).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    new_user = database.User(
        username=user.username,
        password=user.password,
        phone=user.phone
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Успешная регистрация",
        "user_id": new_user.id,
        "username": new_user.username
    }

@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.username == username).first()
    if user and user.password == password:
        return {"user_id": user.id, "username": user.username}
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")

@app.get("/cars")
def get_cars(brand: str = None, min_price: int = None, max_price: int = None, sort_by: str = "newest", db: Session = Depends(get_db)):
    query = db.query(database.Car)
    if brand:
        query = query.filter(database.Car.brand.ilike(f"%{brand}%"))
    if min_price:
        query = query.filter(database.Car.price >= min_price)
    if max_price:
        query = query.filter(database.Car.price <= max_price)
    
    if sort_by == "price_asc":
        query = query.order_by(database.Car.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(database.Car.price.desc())
    else:
        query = query.order_by(database.Car.id.desc())
        
    cars = query.all()
    return [{
        "id": c.id,
        "brand": c.brand,
        "model": c.model,
        "price": c.price,
        "year": c.year,
        "image_url": c.image_url,
        "owner_name": c.owner.username if c.owner else "Аноним",
        "owner_rating": c.owner.rating if c.owner else 5
    } for c in cars]

@app.get("/api/cars/{car_id}")
def get_car_info(car_id: int, db: Session = Depends(get_db)):
    car = db.query(database.Car).filter(database.Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Машина не найдена")
    return {
        "brand": car.brand,
        "model": car.model,
        "price": car.price,
        "year": car.year,
        "description": car.description,
        "image": car.image_url,
        "mileage": car.mileage,
        "owner_id": car.owner_id,
        "owner_name": car.owner.username if car.owner else "Аноним",
        "owner_phone": car.owner.phone if car.owner else "",
        "owner_rating": car.owner.rating if car.owner else 5
    }

@app.post("/upload-car")
async def upload_car(
    brand: str = Form(...), model: str = Form(...), price: int = Form(...),
    year: int = Form(...),  mileage: int = Form(...), description: str = Form(...),
    owner_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)
):
    file_path = f"static/images/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    new_car = database.Car(
        brand=brand, model=model, price=price, year=year,
        mileage=mileage, description=description,
        owner_id=owner_id, image_url=f"/{file_path}"
    )
    db.add(new_car)
    db.commit()
    return {"status": "success"}

@app.get("/api/related/{car_id}")
def get_related_cars(car_id: int, db: Session = Depends(get_db)):
    current_car = db.query(database.Car).filter(database.Car.id == car_id).first()
    if not current_car:
        return []
    related = db.query(database.Car).filter(
        database.Car.brand == current_car.brand,
        database.Car.id != car_id
    ).limit(4).all()
    return [{
        "id": c.id,
        "brand": c.brand,
        "model": c.model,
        "price": c.price,
        "image_url": c.image_url
    } for c in related]

@app.post("/api/reviews")
def add_review(review: ReviewCreate, db: Session = Depends(get_db)):
    new_review = database.Review(
        text=review.text,
        rating=review.rating,
        seller_id=review.seller_id,
        author_id=review.author_id
    )
    db.add(new_review)
    
    seller = db.query(database.User).filter(database.User.id == review.seller_id).first()
    if seller:
        all_reviews = db.query(database.Review).filter(database.Review.seller_id == review.seller_id).all()
        ratings = [r.rating for r in all_reviews] + [review.rating]
        seller.rating = round(sum(ratings) / len(ratings), 1)
    
    db.commit()
    return {"status": "success"}

@app.get("/api/reviews/{seller_id}")
def get_reviews(seller_id: int, db: Session = Depends(get_db)):
    reviews = db.query(database.Review).filter(database.Review.seller_id == seller_id).all()
    return [{
        "text": r.text,
        "rating": r.rating,
        "author_name": r.author.username if r.author else "Аноним"
    } for r in reviews]

@app.post("/upload-avatar")
async def upload_avatar(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    file_path = f"static/images/avatar_{user_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.avatar_url = f"/{file_path}"
    db.commit()

    return {"avatar_url": user.avatar_url}

@app.get("/api/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Юзер не найден")
    return {
        "username": user.username,
        "phone": user.phone,
        "rating": user.rating,
        "reg_date": user.created_at.strftime("%d.%m.%Y") if hasattr(user, 'created_at') else "н/д",
        "cars": [{"id": c.id, "brand": c.brand, "model": c.model, "price": c.price} for c in user.cars],
        "avatar_url": user.avatar_url
    }

@app.delete("/api/cars/{car_id}")
def delete_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(database.Car).filter(database.Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Машина не найдена")
    db.delete(car)
    db.commit()
    return {"message": "Удалено"}

@app.get("/profile/{user_id}", response_class=HTMLResponse)
def get_profile_page(request: Request, user_id: int):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/register")
def register_page():
    return FileResponse("templates/register.html")

