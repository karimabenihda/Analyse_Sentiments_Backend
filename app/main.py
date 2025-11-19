from fastapi import FastAPI,Depends,HTTPException,status,Header
from pydantic import BaseModel
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine,Column,String,Integer
from passlib.context import CryptContext
import jwt
from datetime import datetime,timedelta
from jose import JWTError

app=FastAPI()

load_dotenv()

DB=os.getenv("DB")
PORT=os.getenv("PORT")
SERVER=os.getenv("SERVER")
PASSWORD=os.getenv("PASSWORD")
USER=os.getenv("USER")
ACCESS_TOKEN_EXPIRE_MINUTES =os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")


DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{SERVER}:{PORT}/{DB}"
 
engine=create_engine(DATABASE_URL)

with engine.connect() as conn:
    print('connected')

Base=declarative_base()


pwd_context=CryptContext(schemes=['bcrypt'],deprecated="auto")

password="$2b$12$R.S.Y2z4tG7W6fI8l7hI0O0yL0P"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fake_users={
    "karimabenihda@gmail.com":{
        "fullname":"Karima BENIHDA",
        "username":"karimabenihda@gmail.com",
        "password":"wllh la3rftih"
    }
}


class User(Base):
    __tablename__="users"
    id = Column(Integer, primary_key=True, index=True) 
    fullname=Column(String)
    username=Column(String,unique=True, index=True)
    password=Column(String)

Base.metadata.create_all(bind=engine)

class UserInDB(BaseModel):
    fullname: str
    # username: str
    hashed_password: str 


# class UserInDB(User):
#     password:str

 
def verify_password(plain_password,password):
    return pwd_context.verify(plain_password,password)

def create_access_token(data:dict,expires_delta:timedelta | None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.utcnow()+expires_delta
    else:
        expire=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp":expire})
        encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM) 
        return encoded_jwt

def get_current_user_from_header(
    authorization: Annotated[str | None, Header()] = None):
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
        )
    if not authorization or not authorization.startswith("Bearer"):
        raise credentials_exception
    token=authorization.split(" ")[1]
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str=payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user=fake_users.get(username)
    if user is None:
        raise credentials_exception
    return user




@app.post('/login')
def auth(form_data:Annotated[OAuth2PasswordRequestForm,Depends()]):
    user_dict=fake_users.get(form_data.username)
    
    if not user_dict:
        raise HTTPException(status_code=400,detail="Incorrect username")
    
    user=UserInDB(**user_dict)
    password = form_data.password
    
    if password != user.password:
        raise HTTPException(status_code=400, detail="Incorrect password")
        

    return {
        "access_token":user.username,
        "token_type":"bearer"
    }

# class History(BaseModel):
#     commentaire:str
#     sentiment:str
#     score:float

        # raise HTTPException(status_code=400)
    # if not hashed_password==user.hashed_password:
    #     raise HTTPException(status_code=400,detail="Incorrect password")
# @app.post('/predict')
# def predict_sentiment():
#     return{'jj':'hh'}
