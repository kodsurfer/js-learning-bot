from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    name = State()
    level = State()
    goal = State()
  
