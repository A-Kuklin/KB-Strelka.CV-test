import datetime as dt

import pytz
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from asyncpg import Connection
from asyncpg.exceptions import UniqueViolationError
from validate_email import validate_email

from load_all import db, dp
from utils import get_keyboard


class DBCommands:
    pool: Connection = db
    ADD_NEW_USER = ("INSERT INTO users(chat_id, surname, name, middle_name) "
                    "VALUES ($1, $2, $3, $4) RETURNING id")
    ADD_POSITION = "UPDATE users SET position_=$1 WHERE chat_id = $2"
    ADD_EMAIL = "UPDATE users SET email=$1 WHERE chat_id=$2"

    GET_ID = "SELECT id FROM users WHERE chat_id = $1"
    CHECK_ID = "SELECT chat_id FROM users"

    ADD_PROJECT_TITLE = ("INSERT INTO project(project_id, title) "
                         "VALUES ($1, $2) RETURNING id")
    ADD_PROJECT_DATE = "UPDATE project SET project_date=$1 WHERE title=$2"

    SAY_HI = ("SELECT (name, surname, middle_name, email) FROM users "
              "ORDER BY RANDOM() LIMIT 1")

    ADD_MEETING = ("INSERT INTO meeting(meeting_id, meeting_email, "
                   "meeting_date) VALUES ($1, $2, $3) RETURNING id")

    GET_STATUS_MEETING = ("SELECT meeting_email, meeting_date FROM meeting "
                          "WHERE meeting_id=$1")
    GET_STATUS_PROJECT = ("SELECT title, project_date FROM project "
                          "WHERE project_id=$1")

    async def get_id(self):
        command = self.GET_ID
        user_id = types.User.get_current().id
        return await self.pool.fetchval(command, user_id)

    async def add_new_user(self, name, surname, middle_name=None):
        user = types.User.get_current()
        chat_id = user.id
        args = chat_id, surname, name, middle_name
        command = self.ADD_NEW_USER
        try:
            record_id = await self.pool.fetchval(command, *args)
            return record_id
        except UniqueViolationError:
            pass

    async def update_position(self, position):
        user = types.User.get_current()
        chat_id = user.id
        args = position, chat_id
        command = self.ADD_POSITION
        record_id = await self.pool.fetchval(command, *args)
        return record_id

    async def update_email(self, email):
        user = types.User.get_current()
        chat_id = user.id
        args = email, chat_id
        command = self.ADD_EMAIL
        record_id = await self.pool.fetchval(command, *args)
        return record_id

    async def check_ids(self):
        command = self.CHECK_ID
        rows = await self.pool.fetch(command)
        return ", ".join([
            f"{num + 1}. "
            for num, user in enumerate(rows)
        ])

    async def add_project_title(self, title):
        user = types.User.get_current()
        chat_id = user.id
        args = chat_id, title
        command = self.ADD_PROJECT_TITLE
        record_id = await self.pool.fetchval(command, *args)
        return record_id

    async def add_project_date(self, project_date, title):
        args = project_date, title
        command = self.ADD_PROJECT_DATE
        record_id = await self.pool.fetchval(command, *args)
        return record_id

    async def say_hi(self):
        command = self.SAY_HI
        record_id = await self.pool.fetchval(command)
        return record_id

    async def add_meeting(self, meeting_email):
        user = types.User.get_current()
        chat_id = user.id
        meeting_date = dt.datetime.now() + dt.timedelta(1)
        meeting_date = meeting_date.strftime('%y.%m.%d') + ' 12:00:00'
        meeting_date = dt.datetime.strptime(meeting_date, '%y.%m.%d %H:%M:%S')
        meeting_date = pytz.utc.localize(meeting_date)

        args = chat_id, meeting_email, meeting_date
        command = self.ADD_MEETING
        record_id = await self.pool.fetchval(command, *args)
        return record_id

    async def get_status(self):
        user = types.User.get_current()
        chat_id = user.id
        command_meeting = self.GET_STATUS_MEETING
        command_project = self.GET_STATUS_PROJECT
        record_id = await self.pool.fetch(command_meeting, chat_id)
        rec_dict = {'meetings': [], 'projects': []}
        for item in record_id:
            rec_dict['meetings'].append((item[0], item[1]))
        record_id = await self.pool.fetch(command_project, chat_id)
        for item in record_id:
            rec_dict['projects'].append((item[0], item[1]))
        return rec_dict


class FIO(StatesGroup):
    Q1 = State()
    Q2 = State()
    Q3 = State()


class Project(StatesGroup):
    Q1 = State()
    Q2 = State()
    Q3 = State()


class Meeting(StatesGroup):
    Q1 = State()


db = DBCommands()


@dp.message_handler(commands=["ids"])
async def check_id(message: types.Message):
    ids = await db.check_ids()
    text = f"ID's: {ids}"

    await message.answer(text)


@dp.message_handler(Command('start'), state=None)
async def enter_info(message: types.Message):
    await message.answer('Привет, я бот — личный помощник.\n'
                         'Укажите, пожалуйста, свои ФИО')
    await FIO.Q1.set()


@dp.message_handler(state=FIO.Q1)
async def answer_fio(message: types.Message, state: FSMContext):
    full_name = message.text.split()
    surname, name, middle_name = full_name[0], full_name[1], full_name[2]
    await state.update_data(
        name=name,
        surname=surname,
        middle_name=middle_name
    )
    await db.add_new_user(
        name=name,
        surname=surname,
        middle_name=middle_name
    )

    await message.answer(f'Спасибо, {name}!\n'
                         f'Укажите, пожалуйста, свою должность')
    await FIO.next()


@dp.message_handler(state=FIO.Q2)
async def answer_position(message: types.Message, state: FSMContext):
    position = message.text
    await state.update_data(position=position)
    await db.update_position(position=position)
    data = await state.get_data()
    name = data.get('name')

    await message.answer(f'Принято, {name}!\n'
                         f'Укажите, пожалуйста, свой email.')
    await FIO.next()


@dp.message_handler(state=FIO.Q3)
async def answer_email(message: types.Message, state: FSMContext):
    email = message.text
    if validate_email(email):
        await message.answer(f'Спасибо!')
        await state.update_data(email=email)
        await db.update_email(email=email)
        await message.answer('Выберите опцию из списка ниже',
                             reply_markup=get_keyboard())
        await state.finish()
    else:
        await message.answer(f'Ошибка в адресе: {email}.\n'
                             f'Попробуйте ещё раз, пожалуйста.')
        await FIO.Q3.set()


@dp.message_handler(Text(equals=['Текущий проект']), state=None)
async def add_project_start(message: types.Message):
    await message.answer('Название проекта',
                         reply_markup=types.ReplyKeyboardRemove())
    await Project.Q1.set()


@dp.message_handler(state=Project.Q1)
async def add_project_title(message: types.Message, state: FSMContext):
    title = message.text
    await state.update_data(title=title)
    await db.add_project_title(title=title)

    await message.answer('Принято!\n'
                         'Укажите, пожалуйста, дату окончания (yyyy.mm.dd)')
    await Project.next()


@dp.message_handler(state=Project.Q2)
async def add_project_date(message: types.Message, state: FSMContext):
    project_date = message.text

    try:
        project_date = dt.datetime.strptime(project_date, '%Y.%m.%d').date()
        await state.update_data(project_date=project_date)
        user_data = await state.get_data()
        title = user_data['title']
        await db.add_project_date(project_date=project_date, title=title)
        await message.answer('Принято!\n'
                             'Выберите опцию из списка ниже',
                             reply_markup=get_keyboard())
        await state.finish()
    except ValueError:
        await message.answer(
            f'Ошибка в дате: {project_date} != (yyyy.mm.dd).\n'
            f'Попробуйте ещё раз, пожалуйста.')
        await Project.Q2.set()


@dp.message_handler(Text(equals=['Познакомиться']))
async def say_hi(message: types.Message):
    data = await db.say_hi()
    await message.answer(f'{data[0]} {data[2]} {data[1]}\n'
                         f'Будет рад пообщаться, email:\n'
                         f'{data[3]}',
                         reply_markup=get_keyboard())


@dp.message_handler(Text(equals=['Назначить встречу']), state=None)
async def start_meeting(message: types.Message):
    await message.answer('Введите email сотрудника',
                         reply_markup=types.ReplyKeyboardRemove())
    await Meeting.Q1.set()


@dp.message_handler(state=Meeting.Q1)
async def add_meeting(message: types.Message, state: FSMContext):
    meeting_email = message.text
    await state.update_data(meeting_email=meeting_email)
    await db.add_meeting(meeting_email=meeting_email)

    await message.answer('Принято!', reply_markup=get_keyboard())
    await state.finish()


@dp.message_handler(Text(equals=['Мой статус']))
async def get_status(message: types.Message):
    data = await db.get_status()
    meet_text = ''
    project_text = ''
    for item in data['meetings']:
        date = item[1].strftime("%Y.%m.%d | %H:%M:%S")
        meet_text += f'{item[0]} — {date}\n'
    for item in data['projects']:
        project_text += f'{item[0]} — {item[1]}\n'
    await message.answer('Встречи:\n' + meet_text + 'Проекты:\n' +
                         project_text, reply_markup=get_keyboard())
