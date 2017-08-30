import logging
import os
import sys
import time
import telegram

from functools import wraps
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

token_path = 'token.txt'
if len(sys.argv) > 1:
    token_path = sys.argv[1]

TOKEN = open(token_path).read().strip('\n')

LIST_OF_ADMINS = [224780381]


def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            update.message.reply_text("*Access denied.*\nYou do not have permission to proceed.",
                                      parse_mode=ParseMode.MARKDOWN)
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(bot, update, *args, **kwargs)
    return wrapped


@restricted
def restart(bot, update):
    """
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return: None
    """
    stop(bot, update)
    bot.send_message(update.message.chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


@restricted
def stop(bot, update):
    """
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return: None
    """
    bot.send_message(chat_id=update.message.chat_id, text="Nooooooooooooooooooooo!")
    os.kill(os.getpid(), 2)


def error_handler(bot, update, error):
    """
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param error:
    :return:
    """
    logging.warning('Update "%s" caused error "%s"' % (update, error))

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_error_handler(error_handler)

    dispatcher.add_handler(CommandHandler('restart', restart))
    dispatcher.add_handler(CommandHandler('stop', stop))

    updater.start_polling()
    updater.idle()
