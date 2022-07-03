import os
import sys
import requests
import time
import telegram
from dotenv import load_dotenv
import logging
from logging import StreamHandler, Formatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(
    Formatter(
        fmt='%(asctime)s, %(levelname)s, %(name)s, %(message)s'))
logger.addHandler(handler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logger.info(f'Удачная отправка сообщения: {message}')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.

    В качестве параметра функция получает временную метку. В случае
    успешного запроса должна вернуть ответ API, преобразовав его из
    формата JSON к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise Exception(f'Ошибка при запросе к API: {response.status_code}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность.

    В качестве параметра функция получает ответ API, приведенный к типам
    данных Python. Если ответ API соответствует ожиданиям, то функция
    должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    if not isinstance(response, dict):
        if isinstance(response, list):
            result = next(
                (x for x in response if isinstance(
                    x, dict) and 'homeworks' in x), None)
            if not result:
                raise ValueError('Ответ API не содержит домашних работ')
            return result['homeworks']
        raise TypeError(
            'Ответ API не является ни списком ни словарем')
    if 'homeworks' not in response:
        raise ValueError('Словарь с ответом не содержит')
    return response['homeworks']


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.

    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_STATUSES.
    """
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_STATUSES:
        raise Exception(f'Неизвестный статус {status}')
    verdict = HOMEWORK_STATUSES[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения.
    Которые необходимых для работы программы.

    Если отсутствует хотя бы одна переменная окружения — функция должна
    вернуть False, иначе — True.
    """
    if not PRACTICUM_TOKEN:
        logger.error('Не задан практикум-токен')
        return False
    if not TELEGRAM_TOKEN:
        logger.error('Не задан токен для телеграма')
        return False
    if not TELEGRAM_CHAT_ID:
        logger.error('Не задан идентификатор чата для телеграма')
        return False
    return True


def main():
    """Основная логика работы бота."""
    logging.info('Начало работы')

    if not check_tokens():
        return

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            for homework in homeworks:
                send_message(bot, parse_status(homework))

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
