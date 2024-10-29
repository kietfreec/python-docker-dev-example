from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from config import settings


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)

class HeroCreate(Hero):
    pass

class HeroPublic(Hero):
    id: int

class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})

def get_session():
    with Session(engine) as session:
        yield session

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# @app.get("/")
# def hello():
#     return 'Hello, Docker!!!'


# @app.post("/heroes/")
# def create_hero(hero: Hero):
#     with Session(engine) as session:
#         db_hero = Hero.model_validate(hero)
#         if not db_hero:
#             raise HTTPException(status_code=404, detail="Hero already exists")
#         session.add(hero)
#         session.commit()
#         session.refresh(hero)
#         return hero

@app.post("/heroes/")
def create_hero(*, session: Session = Depends(get_session), hero: HeroCreate):
    checkHero = session.get(Hero, hero.id)
    if checkHero:
        raise HTTPException(status_code=404, detail="Hero already exists")
    else:    
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return hero


@app.get("/heroes/", response_model=list[Hero])
def read_heroes():
    with Session(engine) as session:
        heroes = session.exec(select(Hero)).all()
        return heroes

# @app.get("/heroes/", response_model=list[Hero])
# def read_heroes(
#     *,
#     session: Session = Depends(get_session),
#     offset: int = 0,
#     limit: int = Query(default=100, le=100),
# ):
#     heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
#     return heroes

@app.get("/heroes/{hero_id}", response_model=Hero)
def read_heroes(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate):
    with Session(engine) as session:
        db_hero = session.get(Hero, hero_id)
        if not db_hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        hero_data = hero.model_dump(exclude_unset=True)
        db_hero.sqlmodel_update(hero_data)
        session.add(db_hero)
        session.commit()
        session.refresh(db_hero)
        return db_hero

@app.delete("/heroes/{hero_id}")
def delete_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"Deleted": hero_id}