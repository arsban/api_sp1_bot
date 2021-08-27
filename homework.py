import logging
from logging.handlers import RotatingFileHandler
import os
import time
import requests
import telegram


from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    filename='telegram_bot.log',
    datefmt='%Y-%m-%d, %H:%M:%S',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'telegram_bot.log',
    maxBytes=50_000_000,
    backupCount=5,
)
logger.addHandler(handler)


load_dotenv()


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
        logging.error('Работа не найдена.')
        return 'Работа не найдена'
    if homework_status in statuses:
        verdict = statuses[homework_status]
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    logging.error('Неизвестный статус')
    return 'Неизвестный статус'


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=payload)
    except requests.RequestException as error:
        logging.error(f'Ошибка {error}', exc_info=True)
        return {}
    except ValueError:
        logging.exception('Невалидный формат')
        return {}
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def main():
    send_message('Бот запущен')
    logging.info('Бот запущен')
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
                send_message(f'Бот упал с ошибкой: {e}')
                logging.exception(f'Бот упал с ошибкой: {e}')
                time.sleep(SLEEP_TIME_EXP)
                continue
        except KeyboardInterrupt:
            break

    logging.info('Бот отключён')


if __name__ == '__main__':
    main()
