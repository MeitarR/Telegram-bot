import logging
import os
import sys
import time
from pprint import pprint

import telegram

from functools import wraps
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import ParseMode

import tools
from plugins import *
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


@tools.register_command('restart')
@restricted
def restart(bot, update):
    """
    Restarts the bot.
    (admin only)
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    stop(bot, update)
    bot.send_message(update.message.chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


@tools.register_command('stop')
@restricted
def stop(bot, update):
    """
    Stops the bot.
    (admins only)
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    bot.send_message(chat_id=update.message.chat_id, text="Nooooooooooooooooooooo!")
    os.kill(os.getpid(), 2)


@tools.register_command('help')
def get_help(bot, update):
    """
    Sends a 'help' message
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    message = update.message  # type: telegram.Message

    help_msg = ""
    for cmd_name, cmd_func, args in tools.register_command.functions_list:
        help_msg += "*/%s* - %s\n" % (cmd_name, cmd_func.__doc__.split("***----***")[0])
    message.reply_text(help_msg, parse_mode='Markdown')


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

    for cmd_name, cmd_func, args in tools.register_command.functions_list:
        dispatcher.add_handler(CommandHandler(cmd_name, cmd_func, **args))

    for callback_start_str, callback_func, args in tools.register_callback.functions_list:
        dispatcher.add_handler(CallbackQueryHandler(callback_func, pattern='^/%s .*' % callback_start_str, **args))

    updater.start_polling()
    updater.idle()
