from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import StudentModel
from schemas import StudentCreate
from exceptions import StudentAlreadyExistsException, StudentNotFoundException

async def create_student(student: StudentCreate, session: AsyncSession) -> StudentModel:
    is_student = await session.execute(select(StudentModel).where(StudentModel.telegram_id == student.telegram_id))
    if is_student.scalar_one_or_none():
        raise StudentAlreadyExistsException()
    
    new_student = StudentModel(
        name=student.name,
        surname=student.surname,
        telegram_id=student.telegram_id
    )
    session.add(new_student)
    await session.commit()
    return new_student


async def get_student(telegram_id: int, session: AsyncSession) -> StudentModel | None:
    result = await session.execute(select(StudentModel).where(StudentModel.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if not student:
        raise StudentNotFoundException()
    return student


async def delete_student(telegram_id: int, session: AsyncSession) -> bool:
    result = await session.execute(select(StudentModel).where(StudentModel.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if not student:
        return False
    
    await session.delete(student)
    await session.commit()
    return True


async def update_student(student_data: StudentCreate, session: AsyncSession) -> StudentModel:
    result = await session.execute(select(StudentModel).where(StudentModel.telegram_id == student_data.telegram_id))
    student = result.scalar_one_or_none()
    if not student:
        raise StudentNotFoundException()
    
    student.name = student_data.name
    student.surname = student_data.surname
    student.telegram_id = student_data.telegram_id
    
    await session.commit()
    await session.refresh(student)
    return student