from fastapi import FastAPI, Response, Depends, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
# import requests
from jose import jwt
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, String, Integer,Float, DateTime
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from index import query

load_dotenv()
app = FastAPI()

DB = os.getenv("DB")
PORT = os.getenv("PORT")
SERVER = os.getenv("SERVER")
PASSWORD = os.getenv("PASSWORD")
USER = os.getenv("USER")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

API_URL=os.getenv("API_URL")
HF_TOKEN=os.getenv("HF_TOKEN")


DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{SERVER}:{PORT}/{DB}"
engine = create_engine(DATABASE_URL)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# ------------------- CORS -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Models -------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True) 
    fullname = Column(String)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # plaintext password now


class Prediction(Base):
    __tablename__="predictions"
    id = Column(Integer, primary_key=True, index=True) 
    commentaire= Column(String)
    label=Column(String)
    score= Column(Float)
    

Base.metadata.create_all(bind=engine)

# ------------------- Pydantic Schemas -------------------
class UserInDB(BaseModel):
    username: str
    password: str  



class PredictionInDB(BaseModel):
    commentaire: str

# ------------------- Dependency -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- Login Route -------------------
@app.post('/login')
def auth(data: UserInDB, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Plaintext check, no hashing
    if data.password != user.password:
        raise HTTPException(status_code=401, detail="Wrong password")
    
    payload = {
        "sub": user.username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    response.set_cookie(
        "jwt",
        token,
        httponly=True,
        samesite="lax"
    )
    
    return {"message": "khdam"}



@app.post("/predict")
def predict(data:PredictionInDB,db:Session=Depends(get_db)):
    result= query(data.commentaire)
    prediction=Prediction(
        commentaire=data.commentaire,
        label= result['label'],
        score=result['score']
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    return result

@app.get("/history")
def history(db:Session=Depends(get_db)):
    data=db.query(Prediction).all()
    history=[]
    for d in data:
        history.append(
          {"commentaire" : d.commentaire,
           "label" :d.label,
            "score" : d.score}
        )
  
    return {"history": history}

