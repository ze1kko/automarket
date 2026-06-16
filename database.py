from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

DATABASE_URL = "sqlite:///./cars_shop.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)
    rating = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    avatar_url = Column(String, nullable=True)
    
    cars = relationship("Car", back_populates="owner")

class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String)
    model = Column(String)
    price = Column(Integer)
    year = Column(Integer)
    mileage = Column(Integer) # Пробег возвращен на место
    description = Column(String)
    image_url = Column(String)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="cars")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    rating = Column(Integer)  
    seller_id = Column(Integer, ForeignKey("users.id")) 
    author_id = Column(Integer, ForeignKey("users.id")) 
    
    author = relationship("User", foreign_keys=[author_id])

def create_db():
    Base.metadata.create_all(bind=engine)

