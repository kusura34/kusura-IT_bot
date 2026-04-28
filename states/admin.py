from aiogram.fsm.state import State, StatesGroup


class AddProjectStates(StatesGroup):
    title = State()
    description = State()
    stack = State()
    image = State()
    demo_url = State()
    github_url = State()


class EditProjectStates(StatesGroup):
    project_id = State()
    field = State()
    value = State()


class FaqStates(StatesGroup):
    question = State()
    answer = State()
    faq_id = State()


class TextEditStates(StatesGroup):
    key = State()
    value = State()


class ContactEditStates(StatesGroup):
    key = State()
    value = State()


class SettingEditStates(StatesGroup):
    key = State()
    value = State()


class ReadySolutionStates(StatesGroup):
    title = State()
    description = State()
    benefits = State()
    use_case = State()


class ReadySolutionEditStates(StatesGroup):
    solution_id = State()
    field = State()
    value = State()


class ProjectOrderStates(StatesGroup):
    project_id = State()
    value = State()
