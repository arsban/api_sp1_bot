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
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'telegram_bot.log',
    maxBytes=50000000,
    backupCount=5,
)
logger.addHandler(handler)


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get("homework_name")
    if homework.get('status') == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=payload)
        return homework_statuses.json()
    except requests.RequestException as error:
        return logging.error(error, exc_info=True)


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
                time.sleep(5 * 60)
            except Exception as e:
                send_message(f'Бот упал с ошибкой: {e}')
                logging.exception(f'Бот упал с ошибкой: {e}')
                time.sleep(5)
                continue
        except KeyboardInterrupt:
            break

    logging.info('Бот отключён')


if __name__ == '__main__':
    main()
