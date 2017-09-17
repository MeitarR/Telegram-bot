import pprint
import datetime

import telegram
from telegram import ForceReply
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import RegexHandler

import tools

MESSAGE, CONFIRM_MESSAGE, DATE, CUSTOM_DATE, HOUR, CONFIRM_TIME, REPEAT, CUSTOM_DAYS, CONFIRM_REPEAT = range(9)

REMIND_CANCEL_MSG = '\n(Remember, if you regret, just use /cancel to cancel)'
START_MSG = 'What should I remind you?\n'
CONF_TEXT_MSG = 'Are you sure that what you want me to remind you is: "{0}"?\n'
GET_DATE_MSG = 'tell me when\n'
GET_C_DATE_MSG = 'Tell me exactly when \nwith a date as d.m.yyyy (exa: 1.1.1970)\nor with a day name (exa: sunday)'
GET_HOUR_MSG = ''
CONF_TIME_MSG = ''
GET_REP_MSG = ''
GET_C_REP_MSG = ''
CONF_REP_MSG = ''
END_MSG = ''


def remind(bot, update, user_data):
    """
    sets a remainder
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :return:
    """
    user_data['remind'] = dict()
    update.message.reply_text(
        START_MSG + REMIND_CANCEL_MSG,
        reply_markup=ForceReply(selective=True))

    return MESSAGE


def get_message(bot, update, user_data):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :return:
    """

    reply_keyboard = [['Yes!', 'No!']]

    message = update.message  # type: telegram.Message
    data = user_data['remind']  # type: dict
    data['message'] = message.text
    message.reply_text(CONF_TEXT_MSG.format(message.text),
                       reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
    return CONFIRM_MESSAGE


def is_message_good(bot, update, user_data):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :return:
    """
    message = update.message  # type: telegram.Message
    if message.text == "Yes!":
        reply_keyboard = tools.build_menu(['Today', 'Tomorrow', 'Further'], 2)

        message.reply_text('Good!\n\nNow ' + GET_DATE_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return DATE
    else:
        message.reply_text('Well...\nlets fix it.\n\n' + START_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ForceReply(selective=True))
        return MESSAGE


def select_date_type(bot, update, user_data):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :return:
    """
    message = update.message  # type: telegram.Message
    data = user_data['remind']  # type: dict

    if message.text == "Today":
        data['date'] = datetime.datetime.today().strftime('%-d.%-m.%Y')
    elif message.text == "Tomorrow":
        data['date'] = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%-d.%-m.%Y')
    else:
        message.reply_text(GET_C_DATE_MSG,
                           reply_markup=ForceReply(selective=True))
        return CUSTOM_DATE
    message.reply_text("the user_data: " + str(user_data))
    return HOUR


def handle_custom_date(bot, update, user_data):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :return:
    """
    message = update.message  # type: telegram.Message
    data = user_data['remind']  # type: dict
    data['date'] = message.text


def handle_day_name(bot, update, user_data):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :return:
    """
    message = update.message  # type: telegram.Message
    data = user_data['remind']  # type: dict
    # TODO: get date by weekday


def cancel(bot, update):
    """
    cancel the conversation
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    update.message.reply_text('Well, ok then why you ask for it...',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


tools.add_conversations(ConversationHandler(
    entry_points=[CommandHandler('remind', remind, pass_user_data=True)],

    states={
        MESSAGE: [MessageHandler(Filters.text, get_message, pass_user_data=True)],

        CONFIRM_MESSAGE: [RegexHandler('^(Yes!|No!)$', is_message_good, pass_user_data=True)],

        DATE: [RegexHandler('^(Today|Tomorrow|Further)$', select_date_type, pass_user_data=True)],

        CUSTOM_DATE: [RegexHandler('^(0{0,1}[1-9]|[12][0-9]|3[01])\.(0{0,1}[1-9]|1[012])\.20\d\d$',
                                   handle_custom_date, pass_user_data=True),
                      RegexHandler('^([Ss]unday|[Mm]onday|[Tt]uesday|[Ww]ednesday|[Tt]hursday|[Ff]riday|[Ss]aturday)$',
                                   handle_day_name, pass_user_data=True)
                      ],
    },

    fallbacks=[CommandHandler('cancel', cancel)]
))
