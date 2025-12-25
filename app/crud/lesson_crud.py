from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import LessonModel, StudentModel
from app.schemas import LessonCreate
from app.exceptions import StudentNotFoundException

async def create_lesson(lesson: LessonCreate, session: AsyncSession) -> LessonModel:
    student = await session.execute(select(StudentModel).where(StudentModel.telegram_id == lesson.telegram_id))
    if not student.scalar_one_or_none():
        raise StudentNotFoundException()
    lesson = LessonModel(
        title=lesson.title,
        score=lesson.score,
        telegram_id=lesson.telegram_id
    )
    session.add(lesson)
    await session.commit()
    return lesson


async def get_lessons(session: AsyncSession) -> list[LessonModel]:
    result = await session.execute(select(LessonModel))
    return result.scalars().all()

async def get_student_lessons(telegram_id: int, session: AsyncSession) -> list[LessonModel]:
    result = await session.execute(select(LessonModel).where(LessonModel.telegram_id == telegram_id))
    return result.scalars().all()


async def delete_lesson(lesson_id: int, session: AsyncSession) -> bool:
    result = await session.execute(select(LessonModel).where(LessonModel.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        return False
    
    await session.delete(lesson)
    await session.commit()
    return True


async def update_lesson(lesson_data: LessonCreate, session: AsyncSession) -> LessonModel:
    result = await session.execute(select(LessonModel).where(LessonModel.id == lesson_data.id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        return False
    
    for field, value in lesson_data.items():
        setattr(lesson, field, value)
    
    await session.commit()
    await session.refresh(lesson)
    return lesson