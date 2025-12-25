class StudentAlreadyExistsException(Exception):
    def __init__(self, *args):
        super().__init__("Student is already exists")


class StudentNotFoundException(Exception):
    def __init__(self, *args):
        super().__init__("Student is not found")


class LessonNotFoundException(Exception):
    def __init__(self, *args):
        super().__init__("Lesson is not found")