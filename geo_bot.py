import config
from jobs import update_json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from handlers import say_hello, full_reply
from datetime import time


def main():
    bot = Updater(config.API_TOKEN)

    dp = bot.dispatcher
    dp.add_handler(CommandHandler('start', say_hello))
    # dp.add_handler(MessageHandler(Filters.regex('^(Добавить слой)$'), say_hello))

    dp.add_handler(MessageHandler(Filters.text, full_reply))

    jq = bot.job_queue
    # # jq.run_daily(update_json, time=time(3, 0))
    # # jq.run_repeating(update_json, interval=3, first=5)

    bot.start_polling()
    bot.idle()

if __name__ == '__main__':
    main()