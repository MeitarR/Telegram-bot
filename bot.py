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
import plugins

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
def restart(bot, update, user_data, args):
    """
    Restarts the bot.
    (admin only)
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: user's data
    :type user_data: dict
    :param args: the args of the command
    :type args: list
    :return:
    """
    stop(bot, update)
    bot.send_message(update.message.chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


@restricted
def stop(bot, update, user_data, args):
    """
    Stops the bot.
    (admins only)
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: user's data
    :type user_data: dict
    :param args: the args of the command
    :type args: list
    :return:
    """
    bot.send_message(chat_id=update.message.chat_id, text="Nooooooooooooooooooooo!")
    os.kill(os.getpid(), 2)


def get_help(bot, update, user_data, args):
    """
    Sends a 'help' message
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: user's data
    :type user_data: dict
    :param args: the args of the command
    :type args: list
    :return:
    """
    message = update.message  # type: telegram.Message

    help_msg = ""
    for cmd_name, cmd_func in commands.items():
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


core_commands = {'help': get_help, 'stop': stop, 'restart': restart}
core_callbacks = dict()

commands = tools.merge_dicts(*([core_commands] +
                               [getattr(plugins, plugin_name).__commands__
                                for plugin_name in plugins.__all__
                                if hasattr(getattr(plugins, plugin_name), '__commands__')]))

callbacks = tools.merge_dicts(*([core_callbacks] +
                                [getattr(plugins, plugin_name).__callbacks__
                                 for plugin_name in plugins.__all__
                                 if hasattr(getattr(plugins, plugin_name), '__callbacks__')]))

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_error_handler(error_handler)

    for cmd_name, cmd_func in commands.items():
        dispatcher.add_handler(CommandHandler(cmd_name, cmd_func, pass_user_data=True, pass_args=True))

    for callback_start_str, callback_func in callbacks.items():
        dispatcher.add_handler(CallbackQueryHandler(callback_func, pattern='^%s .*' % callback_start_str))

    updater.start_polling()
    updater.idle()
