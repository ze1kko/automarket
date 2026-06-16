import database
from sqlalchemy.orm import Session

def seed_data():
    db = database.SessionLocal()
    # Проверяем, есть ли уже машины, чтобы не дублировать
    if db.query(database.Car).count() > 0:
        print("База уже заполнена")
        return

    cars = [
        database.Car(brand="BMW", model="M5", price=5000000, year=2020, mileage=30000, description="Идеальное состояние", image_url="/static/images/m5.jpg", owner_id=1),
        database.Car(brand="Audi", model="RS6", price=8000000, year=2021, mileage=30000, description="Пушка-гонка", image_url="/static/images/rs6.jpg", owner_id=1),
        database.Car(brand="Tesla", model="Model 3", price=3500000, year=2019, mileage=30000, description="Автопилот есть", image_url="/static/images/tesla3.jpg", owner_id=1),
        # Добавь сюда еще хоть 50 штук...
    ]
    
    db.add_all(cars)
    db.commit()
    print("База успешно наполнена!")

if __name__ == "__main__":
    seed_data()