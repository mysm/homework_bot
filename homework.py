import os
import sys
import time
import requests
import json
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
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Удачная отправка сообщения: {message}')
    except telegram.error.TelegramError as e:
        logger.error(e)


def get_api_answer(current_timestamp: int) -> [dict, None]:
    """Делает запрос к единственному эндпоинту API-сервиса.

    В качестве параметра функция получает временную метку. В случае
    успешного запроса должна вернуть ответ API, преобразовав его из
    формата JSON к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return None
    if response.status_code != requests.codes.ok:
        error = f'Ошибка при получении ответа от API: {response.status_code}'
        logger.error(error)
        raise requests.exceptions.HTTPError(error)
    try:
        result = response.json()
    except json.decoder.JSONDecodeError as e:
        logger.error(e)
        return None
    return result


def check_response(response: [dict, list]) -> list:
    """Проверяет ответ API на корректность.

    В качестве параметра функция получает ответ API, приведенный к типам
    данных Python. Если ответ API соответствует ожиданиям, то функция
    должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    if not isinstance(response, dict):
        if isinstance(response, list):
            result = next(
                (x for x in response if x is dict and 'homeworks' in x), None)
        else:
            raise TypeError('Ответ API не является ни словарем, ни списком')
    else:
        result = response.get('homeworks', None)

    if not result:
        raise ValueError('Ответ API не содержит домашних работ')
    if 'homeworks' not in result:
        raise ValueError('Словарь с ответом не содержит ключа "homeworks"')
    if result is not list:
        raise TypeError('Словарь с ответом не содержит списка')
    return result


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.

    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_STATUSES.
    """
    homework_name = homework.get('homework_name', '')
    homework_status = homework.get('status', '')
    if homework_status not in HOMEWORK_STATUSES:
        raise ValueError(f'Неизвестный статус работы: {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения.

    Если отсутствует хотя бы одна переменная окружения — функция
    возвращает False, иначе — True.
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
    logger.info('Начало работы')

    if not check_tokens():
        logger.error('Отсутствуют необходимые переменные окружения')
        return

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if not response:
                continue
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
