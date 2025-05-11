from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlmodel import select

from models import *
from endpoints.base_models import *
from settings import SessionDep, settings

auth_router = APIRouter(tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(session, username: str):
    user = session.exec(select(User).where(User.username == username)).one_or_none()
    return user


def authenticate_user(session, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


@auth_router.post("/register/")
def register(userModel: UserModel, session: SessionDep) -> User:
    user = User(username=userModel.username, email=userModel.email)
    user.set_password(userModel.password)  # Set the password
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"username": user.username, "email": user.email}


@auth_router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@auth_router.get("/users/me/", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user
