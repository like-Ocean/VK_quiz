import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import require_admin
from schemas.category import CategoryCreate, CategoryResponse
from schemas.auth import MessageResponse
from services.category_service import list_categories, create_category, delete_category

category_router = APIRouter(prefix="/categories", tags=["categories"])


@category_router.get("", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryResponse]:
    return await list_categories(db)


@category_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def add_category(
    payload: CategoryCreate, db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
) -> CategoryResponse:
    return await create_category(db, payload.name)


@category_router.delete("/{category_id}", response_model=MessageResponse)
async def remove_category(
    category_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin)
) -> MessageResponse:
    await delete_category(db, category_id)
    
    return MessageResponse(message="Category deleted")
