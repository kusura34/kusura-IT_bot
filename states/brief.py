from aiogram.fsm.state import State, StatesGroup


class BriefStates(StatesGroup):
    project_type = State()
    payment = State()
    design = State()
    admin_panel = State()
    budget = State()
    contact = State()
