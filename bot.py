import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
import re

TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН")
ADMIN_IDS = [559631622, 521773805]

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

user_states = {}

def kb_start():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Начать", color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

def kb_position():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Стажёр", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Junior", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Другое", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def kb_date():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Сразу", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("Через неделю", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Через месяц", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def kb_empty():
    keyboard = VkKeyboard(one_time=True)
    return keyboard.get_empty_keyboard()

def send_message(user_id, message, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            keyboard=keyboard,
            random_id=random.randint(0, 100000)
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки пользователю {user_id}: {e}")
        return False

def is_valid_salary(text):
    cleaned = re.sub(r"[\s₽руб.,]", "", text.lower())
    return cleaned.isdigit()

def is_valid_contact(text):
    phone_pattern = r"^\+7[\s\-\(\)]?\d{3}[\s\-\(\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$"
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(phone_pattern, text.strip())) or bool(re.match(email_pattern, text.strip()))

Q_NAME = "Как вас зовут? Напишите ФИО полностью."

Q_POSITION = (
    "На какую позицию вы претендуете?\n"
    "Выберите один из вариантов ниже или напишите свой."
)

Q_POSITION_OTHER = "Напишите, на какую позицию вы претендуете."

Q_EXPERIENCE = (
    "Опишите ваш опыт в 2-3 предложениях.\n\n"
    "Например: где работали или стажировались, какие задачи выполняли, "
    "какими инструментами владеете (программы, языки, методики).\n"
    "Если опыта нет — напишите «Без опыта»."
)

Q_SALARY = (
    "Какие у вас зарплатные ожидания?\n"
    "Напишите числом, в рублях (например, 50000)."
)

Q_SALARY_ERROR = "Пожалуйста, напишите только число. Например: 50000"

Q_DATE = "Когда вы готовы приступить к работе? Выберите вариант ниже."

Q_CONTACT = (
    "Оставьте контакт для связи.\n\n"
    "Телефон должен начинаться с +7 (например, +7 999 999-99-99)\n"
    "Или укажите email (например, ivan@mail.ru)."
)

Q_CONTACT_ERROR = (
    "Не похоже на телефон или email. Попробуйте ещё раз.\n\n"
    "Телефон должен начинаться с +7 (например, +7 999 999-99-99)\n"
    "Пример email: ivan@mail.ru"
)

print("Бот запущен и слушает сообщения...")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        raw = event.text.strip()
        text = raw.lower()

        if user_id not in user_states:
            user_states[user_id] = {"step": 1, "data": {}, "await_other": False}
            send_message(
                user_id,
                "Здравствуйте! Я бот для первичного отбора кандидатов.\n"
                "Отвечу на несколько вопросов — это займёт 2-3 минуты.\n\n"
                "Нажмите кнопку «Начать» ниже.",
                keyboard=kb_start()
            )
            continue

        state = user_states[user_id]
        step = state["step"]

        if step == 1:
            if text == "начать":
                state["step"] = 2
                send_message(user_id, Q_NAME, keyboard=kb_empty())
            else:
                send_message(
                    user_id,
                    "Пожалуйста, нажмите кнопку «Начать» ниже, чтобы продолжить.",
                    keyboard=kb_start()
                )
            continue

        if step == 2:
            state["data"]["name"] = raw
            state["step"] = 3
            send_message(user_id, Q_POSITION, keyboard=kb_position())
            continue

        if step == 3:
            if state.get("await_other"):
                state["data"]["position"] = raw
                state["await_other"] = False
                state["step"] = 4
                send_message(user_id, Q_EXPERIENCE, keyboard=kb_empty())
                continue
            if text == "другое":
                state["await_other"] = True
                send_message(user_id, Q_POSITION_OTHER, keyboard=kb_empty())
                continue
            state["data"]["position"] = raw
            state["step"] = 4
            send_message(user_id, Q_EXPERIENCE, keyboard=kb_empty())
            continue

        if step == 4:
            state["data"]["experience"] = raw
            state["step"] = 5
            send_message(user_id, Q_SALARY, keyboard=kb_empty())
            continue

        if step == 5:
            if not is_valid_salary(raw):
                send_message(user_id, Q_SALARY_ERROR, keyboard=kb_empty())
                continue
            state["data"]["salary"] = raw
            state["step"] = 6
            send_message(user_id, Q_DATE, keyboard=kb_date())
            continue

        if step == 6:
            state["data"]["start_date"] = raw
            state["step"] = 7
            send_message(user_id, Q_CONTACT, keyboard=kb_empty())
            continue

        if step == 7:
            if not is_valid_contact(raw):
                send_message(user_id, Q_CONTACT_ERROR, keyboard=kb_empty())
                continue
            state["data"]["contact"] = raw
            state["step"] = 8
            send_message(
                user_id,
                "Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.",
                keyboard=kb_empty()
            )

            d = state["data"]
            report = (
                f"🔔 НОВАЯ ЗАЯВКА!\n\n"
                f"👤 Имя: {d.get('name')}\n"
                f"💼 Позиция: {d.get('position')}\n"
                f"📝 Опыт: {d.get('experience')}\n"
                f"💰 Зарплата: {d.get('salary')} руб.\n"
                f"📅 Выход: {d.get('start_date')}\n"
                f"📞 Контакт: {d.get('contact')}\n"
                f"🆔 Ссылка: https://vk.com/id{user_id}"
            )

            for admin_id in ADMIN_IDS:
                send_message(admin_id, report)
                print(f"Заявка от {user_id} отправлена админу {admin_id}.")

            del user_states[user_id]
            continue
