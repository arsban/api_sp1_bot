import logging
import os
import time
from logging.handlers import RotatingFileHandler


import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    filename='telegram_bot.log',
    datefmt='%Y-%m-%d, %H:%M:%S',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler_rotate = RotatingFileHandler(
    'telegram_bot.log',
    maxBytes=50_000_000,
    backupCount=5,
)
handler_stream = logging.StreamHandler()
logger.addHandler(handler_rotate)
logger.addHandler(handler_stream)


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


SLEEP_TIME = (60 * 5)
SLEEP_TIME_EXP = (5)


bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get("homework_name")
    homework_status = homework.get('status')
    statuses = {
        'reviewing': 'Проект на ревью.',
        'rejected': 'К сожалению, в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось, работа зачтена!'
    }
    if homework_name is None:
        message: str = 'Работа не найдена.'
        # Альтернативный путь для бесстрашных --
        # поддержать Телеграм в своем логгере. © Алексей Пак
        # не уверен, что это то что вы имели ввиду,
        # но я всю ночь просидел и лучше не смог придумать. (дайте подсказку)
        logging.error(message)
        send_message(message)
    if homework_status in statuses:
        verdict = statuses[homework_status]
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    message: str = 'Неизвестный статус'
    logging.error(message)
    send_message(message)


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=payload)
    except requests.RequestException as error:
        message: str = f'Ошибка {error}'
        logging.error(message, exc_info=True)
        send_message(message)
        return {}
    except TypeError as error:
        # тут тоже есть подозрение что ошибся,
        # не смог найти сломанный json чтобы проверить, все гуглил
        message: str = f'Невалидный формат {error}'
        logging.exception(message)
        send_message(message)
        return {}
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(CHAT_ID, text=message)


def main():
    message: str = 'Бот запущен'
    logging.info(message)
    send_message(message)
    current_timestamp = int(time.time())  # Начальное значение timestamp

    while True:
        try:
            try:
                new_homework = get_homeworks(current_timestamp)
                if new_homework.get('homeworks'):
                    send_message(
                        parse_homework_status(new_homework.get('homeworks')[0])
                    )
                current_timestamp = new_homework.get('current_date')
                time.sleep(SLEEP_TIME)
            except Exception as e:
                message: str = f'Бот упал с ошибкой: {e}'
                send_message(message)
                logging.exception(message)
                time.sleep(SLEEP_TIME_EXP)
                continue
        except KeyboardInterrupt:
            break
    message: str = 'Бот отключён'
    send_message(message)
    logging.info(message)


if __name__ == '__main__':
    main()
