from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.sample_data import SAMPLE_QUIZZES
from core.security import hash_password
from core.config import settings
from models.answer_option import AnswerOption
from models.question import Question, QuestionType
from models.quiz import Quiz
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


async def create_sample_quizzes(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
    admin = result.scalar_one_or_none()
    if not admin:
        return

    for quiz_data in SAMPLE_QUIZZES:
        result = await db.execute(
            select(Quiz).where(Quiz.title == quiz_data["title"], Quiz.owner_id == admin.id)
        )
        if result.scalar_one_or_none():
            continue

        result = await db.execute(
            select(Category).where(Category.name == quiz_data["category"])
        )
        category = result.scalar_one_or_none()
        quiz = Quiz(
            owner_id=admin.id,
            category_id=category.id if category else None,
            title=quiz_data["title"],
            description=quiz_data["description"],
            time_per_question=quiz_data["time_per_question"],
            is_public=True,
        )
        db.add(quiz)
        await db.flush()

        for q_data in quiz_data["questions"]:
            question = Question(
                quiz_id=quiz.id,
                order=q_data["order"],
                text=q_data["text"],
                question_type=QuestionType.text,
                answer_type=q_data["answer_type"],
                points=q_data["points"],
            )
            db.add(question)
            await db.flush()

            for text, is_correct in q_data["options"]:
                db.add(AnswerOption(
                    question_id=question.id,
                    text=text,
                    is_correct=is_correct,
                ))

        print(f"[init_db] Quiz created: {quiz_data['title']}")


async def init_db(db: AsyncSession) -> None:
    await create_admin(db)
    await create_categories(db)
    await create_kick_reasons(db)
    await create_sample_quizzes(db)
    await db.commit()