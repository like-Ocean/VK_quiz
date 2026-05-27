from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.security import hash_password
from core.config import settings
from models.user import User
from models.category import Category
from models.kick_reason import KickReason


CATEGORIES = [
    "Кино",
    "Наука",
    "Общее",
    "История",
    "География",
    "Спорт",
    "Музыка",
    "Технологии",
    "Природа",
    "Литература"
]

KICK_REASONS = [
    "Оскорбительный никнейм",
    "Нарушение правил",
    "Другое",
]


async def create_admin(db: AsyncSession) -> None:
    result = await db.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    )
    admin = result.scalar_one_or_none()

    if admin:
        return

    admin = User(
        email=settings.ADMIN_EMAIL,
        username="admin",
        password=hash_password(settings.ADMIN_PASSWORD),
        is_admin=True,
    )
    db.add(admin)
    await db.flush()
    print(f"[init_db] Admin created: {settings.ADMIN_EMAIL}")


async def create_categories(db: AsyncSession) -> None:
    for name in CATEGORIES:
        result = await db.execute(
            select(Category).where(Category.name == name)
        )
        exists = result.scalar_one_or_none()

        if not exists:
            db.add(Category(name=name))
            print(f"[init_db] Category added: {name}")


async def create_kick_reasons(db: AsyncSession) -> None:
    for label in KICK_REASONS:
        result = await db.execute(
            select(KickReason).where(KickReason.label == label)
        )
        exists = result.scalar_one_or_none()

        if not exists:
            db.add(KickReason(label=label))
            print(f"[init_db] Kick reason added: {label}")


async def init_db(db: AsyncSession) -> None:
    await create_admin(db)
    await create_categories(db)
    await create_kick_reasons(db)
    await db.commit()