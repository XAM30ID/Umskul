import os
import logging
from logging import getLogger, DEBUG
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import FastAPI, Depends, HTTPException

from app.crud.lesson_crud import delete_lesson, get_lessons, get_student_lessons, update_lesson
from crud.student_crud import create_student, delete_student, get_student, update_student
from exceptions import StudentAlreadyExistsException, StudentNotFoundException
from schemas import LessonCreate, StudentCreate
from database import get_db, setup_database

logging.basicConfig(
    level=DEBUG,
    format='%(asctime)s: %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = getLogger(__name__)


app = FastAPI()


@app.post('/setup_database', tags=['Настройка'], summary='Создание базы данных', description='Эндпоинт для создания или перезаписи базы данных')
async def setup_database_url():
    '''
        Создание базы данных
    '''
    try:
        await setup_database()
        logger.info('Таблицы данных успешно созданы')
        return {'message': 'Tables created successful!'}
    except Exception as e:
        logger.error(f'Таблицы данных не были созданы: {e}')


# Ученики
@app.get('/student/{telegram_id}', tags=['Ученики'], summary='Получение информации об ученике', description='Эндпоинт для получения информации об ученике по telegram_id')
async def get_student_url(telegram_id: int, session: AsyncSession = Depends(get_db)):
    '''
        Получение информации об ученике
    '''
    try:
        student = await get_student(telegram_id, session)
        return student
    except StudentNotFoundException as e:
        logger.error('Пользователь не найден')
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Ошибка при получении данных: {e}')
        return None

@app.post('/student', tags=['Ученики'], summary='Создание записи ученика', description='Эндпоинт для создания записи ученика')
async def create_student_url(student_data: StudentCreate, session: AsyncSession = Depends(get_db)):
    '''
        Создание записи ученика
    '''
    try:
        student = await create_student(student_data, session)
        return student
    except StudentAlreadyExistsException as e:
        logger.error('Пользователь уже существует')
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f'Ошибка при создании пользователя: {e}')
        return None
    
@app.delete('/student/{telegram_id}', tags=['Ученики'], summary='Удаление ученика', description='Эндпоинт для удаления ученика')
async def delete_student_url(telegram_id: int, session: AsyncSession = Depends(get_db)):
    '''
        Удаление ученика
    '''
    try:
        result = await delete_student(telegram_id, session)
        return 'Пользователь успешно удалён' if result else 'Не удалось удалить пользователя'
    except StudentNotFoundException as e:
        logger.error('Не удалось удалить пользователя. Пользователь не найден')
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Ошибка при удалении пользователя: {e}')
        return None

@app.put('/student', tags=['Ученики'], summary='Изменение информации ученика', description='Эндпоинт для изменения информации ученика')
async def update_student_url(student_data: StudentCreate, session: AsyncSession = Depends(get_db)):
    '''
        Изменение информации ученика
    '''
    try:
        result = await update_student(student_data, session)
        return result
    except StudentNotFoundException as e:
        logger.error('Пользователь не найден')
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Ошибка при изменении пользователя: {e}')
        return None


# Предметы
@app.get('/lessons', tags=['Предметы'], summary='Получение списка всех предметов', description='Эндпоинт для получения всех предметов всех учеников')
async def get_lessons_url(session: AsyncSession = Depends(get_db)):
    '''
        Получение списка всех предметов
    '''
    try:
        lessons = await get_lessons(session)
        return lessons
    except Exception as e:
        logger.error(f'Ошибка при получении данных: {e}')
        return None
    
@app.get('/lessons/{telegram_id}', tags=['Предметы'], summary='Получение предметов определённого ученика', description='Эндпоинт для получения списка предметов конкретного ученика')
async def get_students_lessons_url(telegram_id: int, session: AsyncSession = Depends(get_db)):
    '''
        Получение списка предметов ученика по telegram_id
    '''
    try:
        lessons = await get_student_lessons(telegram_id, session)
        return lessons
    except Exception as e:
        logger.error(f'Ошибка при получении данных: {e}')
        return None

@app.post('/lessons', tags=['Предметы'], summary='Создание записи предмета', description='Эндпоинт для создания записи предмета')
async def create_student_url(lesson_data: LessonCreate, session: AsyncSession = Depends(get_db)):
    '''
        Создание записи предмета
    '''
    try:
        lesson = await create_student(lesson_data, session)
        return lesson
    except StudentNotFoundException as e:
        logger.error('Пользователь не найден')
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Ошибка при создании предмета: {e}')
        return None
    
@app.delete('/student/{lesson_id}', tags=['Предметы'], summary='Удаление предмета', description='Эндпоинт для удаления предмета')
async def delete_lesson_url(lesson_id: int, session: AsyncSession = Depends(get_db)):
    '''
        Удаление предмета
    '''
    try:
        result = await delete_lesson(lesson_id, session)
        return 'Предмет успешно удалён' if result else 'Не удалось удалить предмет'
    except StudentNotFoundException as e:
        logger.error('Не удалось удалить предмет. Предмет не найден')
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Ошибка при удалении предмета: {e}')
        return None

@app.put('/lesson', tags=['Предметы'], summary='Изменение информации о предмете', description='Эндпоинт для изменения информации о предмете')
async def update_lesson_url(lesson_data: LessonCreate, session: AsyncSession = Depends(get_db)):
    '''
        Изменение информации о предмете
    '''
    try:
        result = await update_lesson(lesson_data, session)
        return result
    except StudentNotFoundException as e:
        logger.error('Пользователь не найден')
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Ошибка при изменении предмета: {e}')
        return None


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,            
        reload=True
        )