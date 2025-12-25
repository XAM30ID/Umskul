from database import Base

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship


class StudentModel(Base):
    '''
        Модель ученика
    '''
    __tablename__ = 'Students'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(32), nullable=False)
    surname = Column(String(32), nullable=False)
    telegram_id = Column(Integer, nullable=False, unique=True)

    lessons = relationship('LessonModel', back_populates='student', cascade="all, delete-orphan", passive_deletes=True, lazy="selectin")


class LessonModel(Base):
    '''
        Модель для урока
    '''
    __tablename__ = 'Lessons'

    id = Column(Integer, primary_key=True, unique=True)
    title = Column(String(32), nullable=False)
    score = Column(Integer, nullable=False)
    telegram_id = Column(Integer, ForeignKey('Students.telegram_id', ondelete="CASCADE"))  

    student = relationship('StudentModel', back_populates='lessons', lazy='selectin')