import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from core.security import hash_password, verify_password
from models.user import User


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
	result = await db.execute(select(User).where(User.id == user_id))
	return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
	result = await db.execute(select(User).where(User.email == email))
	return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
	result = await db.execute(select(User).where(User.username == username))
	return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, username: str, password: str) -> User:
	user = User(
		email=email,
		username=username,
		password=hash_password(password),
	)
	db.add(user)
	await db.commit()
	await db.refresh(user)
	
	return user


async def update_user_profile(db: AsyncSession, user: User, email: str | None = None, username: str | None = None) -> User:
	if email and email != user.email:
		existing = await get_user_by_email(db, email)
		if existing:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Email already in use",
			)

	if username and username != user.username:
		existing = await get_user_by_username(db, username)
		if existing:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Username already in use",
			)

	if email is not None:
		user.email = email
	if username is not None:
		user.username = username

	await db.commit()
	await db.refresh(user)
	
	return user


async def change_user_password(db: AsyncSession, user: User, old_password: str, new_password: str) -> None:
	if not verify_password(old_password, user.password):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Old password is incorrect",
		)

	user.password = hash_password(new_password)

	await db.commit()


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> User:
	user.password = hash_password(new_password)
	await db.commit()
	await db.refresh(user)
	
	return user
