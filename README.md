# homework_bot
python telegram bot

 Телеграм бот Мыслицкого Михаила mysm_assist. Бот отслеживает статус выполнения домашнего задания в Яндекс.практикум через API Яндекс
 и отправляет уведомдение студенту. Бот уменьшает время реакции на правки ревьера: быстрее можно сдать домашее задание и успеть до дедлайна, сократив издержки времени.

Зависимости
===========

   * python-dotenv==0.19.0
   * python-telegram-bot==13.7
   * requests==2.26.0

Установка
=========

    $ git clone https://github.com/mysm/homework_bot.git
    $ cd homework_bot
    $ pip install -r requirements.txt

Настройка
==========
Для работы бота необхоходимо создать файл .env с параметрами доступа к API Telegram и Яндекс.практикума.

Пример файла .env:

```
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'
PRACTICUM_TOKEN = 'YOUR_PRACTICUM_TOKEN'
```
