from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    name = State()
    level = State()
    goal = State()


class LessonState(StatesGroup):
    reading = State()
    answering = State()


class PracticeState(StatesGroup):
    answering = State()
    waiting_for_answer = State()
  
