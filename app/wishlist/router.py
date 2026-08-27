from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db

from . import schemas
from .service import WishService

router = APIRouter()

@router.post("/", response_model=schemas.WishResponse, status_code=status.HTTP_201_CREATED)
async def add_wish(
    wish_data: schemas.WishCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await WishService.create_wish(db, wish_data, current_user.id)


@router.get("/", response_model=List[schemas.WishResponse])
async def my_wishes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await WishService.get_user_wishes(db, current_user.id)
