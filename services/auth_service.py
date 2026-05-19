from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.security import (
	create_access_token, generate_refresh_token,
	hash_refresh_token, verify_password
)
from models.refresh_token import RefreshToken
from models.user import User
from services.user_service import get_user_by_email, get_user_by_username, create_user


async def register_user(db: AsyncSession, email: str, username: str, password: str) -> User:
	existing_email = await get_user_by_email(db, email)
	if existing_email:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Email already in use",
		)

	existing_username = await get_user_by_username(db, username)
	if existing_username:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Username already in use",
		)

	return await create_user(db, email=email, username=username, password=password)



async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
	user = await get_user_by_email(db, email)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid credentials",
		)
	if not verify_password(password, user.password):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid credentials",
		)
	return user


async def issue_tokens(db: AsyncSession, user_id: uuid.UUID):
	access_token = create_access_token(user_id)
	refresh_token = generate_refresh_token()
	refresh_hash = hash_refresh_token(refresh_token)
	expires_at = datetime.now(timezone.utc) + timedelta(
		days=settings.REFRESH_TOKEN_EXPIRE_DAYS
	)

	db.add(
		RefreshToken(
			user_id=user_id,
			token_hash=refresh_hash,
			expires_at=expires_at,
			revoked=False,
		)
	)
	await db.commit()
	return access_token, refresh_token


async def get_refresh_token(db: AsyncSession, token_hash: str) -> RefreshToken | None:
	result = await db.execute(
		select(RefreshToken).where(RefreshToken.token_hash == token_hash)
	)
	return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, refresh: RefreshToken) -> None:
	refresh.revoked = True
	await db.commit()


async def rotate_refresh_token(db: AsyncSession, *, refresh: RefreshToken):
	refresh.revoked = True
	await db.commit()
	return await issue_tokens(db, refresh.user_id)


async def refresh_tokens(db: AsyncSession, refresh_token: str):
	token_hash = hash_refresh_token(refresh_token)
	refresh_record = await get_refresh_token(db, token_hash)

	if not refresh_record or refresh_record.revoked:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid refresh token",
		)

	if refresh_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
		await revoke_refresh_token(db, refresh_record)
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Refresh token expired",
		)

	return await rotate_refresh_token(db, refresh=refresh_record)


async def logout_user(db: AsyncSession, refresh_token: str) -> None:
	token_hash = hash_refresh_token(refresh_token)
	refresh_record = await get_refresh_token(db, token_hash)
	if refresh_record and not refresh_record.revoked:
		await revoke_refresh_token(db, refresh_record)
