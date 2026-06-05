import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from core.security import hash_password, verify_password
from models.question import Question
from models.quiz import Quiz
from models.room import Room, RoomStatus
from models.category import Category
from models.room_participant import RoomParticipant
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


async def list_user_quizzes(db: AsyncSession, user: User) -> list[dict]:
    result = await db.execute(select(Quiz).where(Quiz.owner_id == user.id))
    quizzes = list(result.scalars().all())
    items: list[dict] = []
    for quiz in quizzes:
        count_result = await db.execute(
            select(func.count(Question.id)).where(Question.quiz_id == quiz.id)
        )
        questions_count = count_result.scalar_one() or 0
        rooms_result = await db.execute(
            select(Room).where(Room.quiz_id == quiz.id)
        )
        rooms = list(rooms_result.scalars().all())
        active_room = next(
            (r for r in rooms if r.status != RoomStatus.finished), None
        )

        room_status = active_room.status if active_room else None
        active_room_id = active_room.id if active_room else None
        max_participants = 0
        for room in rooms:
            p_result = await db.execute(
                select(func.count(RoomParticipant.id))
                .where(RoomParticipant.room_id == room.id)
            )
            count = p_result.scalar_one() or 0
            if count > max_participants:
                max_participants = count

        category_name = None
        if quiz.category_id:
            cat_result = await db.execute(
                select(Category).where(Category.id == quiz.category_id)
            )
            cat = cat_result.scalar_one_or_none()
            category_name = cat.name if cat else None

        items.append({
            "id": quiz.id,
            "owner_id": quiz.owner_id,
            "category_id": quiz.category_id,
            "category_name": category_name,
            "title": quiz.title,
            "description": quiz.description,
            "time_per_question": quiz.time_per_question,
            "is_public": quiz.is_public,
            "created_at": quiz.created_at,
            "updated_at": quiz.updated_at,
            "questions_count": questions_count,
            "participants_count": max_participants,
            "room_status": room_status,
            "active_room_id": active_room_id,
        })

    return items


async def get_participation_history(db: AsyncSession, user: User) -> list[dict]:
    result = await db.execute(
        select(RoomParticipant, Room, Quiz)
        .join(Room, RoomParticipant.room_id == Room.id)
        .join(Quiz, Room.quiz_id == Quiz.id)
        .where(RoomParticipant.user_id == user.id)
    )
    rows = result.all()

    history: list[dict] = []
    for participant, room, quiz in rows:
        participants_result = await db.execute(
            select(RoomParticipant)
            .where(RoomParticipant.room_id == room.id)
            .order_by(RoomParticipant.score.desc())
        )
        participants = list(participants_result.scalars().all())
        position = next(
            (idx + 1 for idx, item in enumerate(participants) if item.id == participant.id),
            None,
        )

        total_result = await db.execute(
            select(func.sum(Question.points)).where(Question.quiz_id == quiz.id)
        )
        total_points = total_result.scalar_one() or 0
        count_result = await db.execute(
            select(func.count(Question.id)).where(Question.quiz_id == quiz.id)
        )
        questions_count = count_result.scalar_one() or 0

        category_name = None
        if quiz.category_id:
            cat_result = await db.execute(
                select(Category).where(Category.id == quiz.category_id)
            )
            cat = cat_result.scalar_one_or_none()
            category_name = cat.name if cat else None

        history.append({
            "room_id": room.id,
            "quiz_title": quiz.title,
            "score": participant.score,
            "total_points": total_points,
            "finished_at": room.finished_at,
            "leaderboard_position": position,
            "total_participants": len(participants),
            "questions_count": questions_count,
            "time_per_question": quiz.time_per_question,
            "category": category_name,
        })

    return history
