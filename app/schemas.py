from pydantic import BaseModel, Field

class StudentBase(BaseModel):
    name: str = Field(max_length=32)
    surname: str = Field(max_length=32)

class StudentCreate(StudentBase):
    telegram_id: int = Field()


class LessonBase(BaseModel):
    title: str = Field(max_length=32)
    score: int = Field()

class LessonCreate(LessonBase):
    telegram_id: int = Field()