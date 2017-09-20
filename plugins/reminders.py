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

from collections import namedtuple

import tools

MESSAGE, CONFIRM_MESSAGE, DATE, CUSTOM_DATE, HOUR, CONFIRM_TIME, REPEAT, CUSTOM_DAYS, CONFIRM_REPEAT = range(9)
EVERY_DAY, EVERY_MONTH, CUSTOM, NO_REP = range(4)

REMIND_CANCEL_MSG = '\n(Remember, if you regret, just use /cancel to discard)\n'
START_MSG = 'What do you need me to remind you of?\n'
CONF_TEXT_MSG = 'Are you sure that you want to be reminded about "{0}"?\n'
GET_DATE_MSG = 'Should i remind you of that today or tomorrow?\n'
GET_C_DATE_MSG = 'Tell me on what day do you need to be reminded please, \n' \
                 'with a date in this format - DD.MM.YYYY (ex: 1.1.2000),' \
                 '\nor just tell me what day (ex: sunday)\n'
GET_HOUR_MSG = 'What time do you need me to remind you of that? Please write in this format - HH:MM\n'
CONF_TIME_MSG = 'So let\'s see if i got it right. You want me to remind you on {0} at {1}. Am I correct?\n'
GET_REP_MSG = 'Do you need to be reminded of that repeatedly? For instance, every week?\n'
GET_C_REP_MSG = 'Choose the days you want it to repeat.\n\nYou already choosed those days:\n{0}\n'
CONF_REP_MSG = 'All right, you want me to remind you {0}. Correct?\n'
END_MSG = 'Excellent! Your reminder has been set! \n'

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
WEEK_LENGTH = 7
DATE_FORMAT = '%-d.%-m.%Y'

Repeat = namedtuple('Repeat', 'type days')
Reminder = namedtuple('Reminder', 'text time repeat')


def get_future_weekday_date(name):
    """
    :param name: the name of the day
    :type name: str
    :return: Datetime
    """
    name = name.lower()
    if name in DAYS:
        day_num = DAYS.index(name)
        today = datetime.datetime.today()
        if today.weekday() <= day_num:
            days = day_num - today.weekday()
        else:
            days = WEEK_LENGTH - (today.weekday() - day_num)
        return today + datetime.timedelta(days=days)
    else:
        return None


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
        reply_keyboard = tools.build_menu(['Today', 'Tomorrow', 'No, a different date'], 2)

        message.reply_text('Good!\n\n' + GET_DATE_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return DATE
    else:
        message.reply_text('Well...\nlet\'s fix it.\n\n' + START_MSG + REMIND_CANCEL_MSG,
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
        data['date'] = datetime.datetime.today().strftime(DATE_FORMAT)
    elif message.text == "Tomorrow":
        data['date'] = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime(DATE_FORMAT)
    else:
        message.reply_text(GET_C_DATE_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ForceReply(selective=True))
        return CUSTOM_DATE
    message.reply_text(GET_HOUR_MSG + REMIND_CANCEL_MSG)
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
    message.reply_text(GET_HOUR_MSG + REMIND_CANCEL_MSG)
    return HOUR


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
    data['date'] = get_future_weekday_date(message.text).strftime(DATE_FORMAT)
    message.reply_text(GET_HOUR_MSG + REMIND_CANCEL_MSG)
    return HOUR


def get_hour(bot, update, user_data):
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

    hour = str(message.text)

    if data['date'] == datetime.datetime.today().strftime(DATE_FORMAT):
        spited_hour = hour.split(':')
        if int(spited_hour[0]) < datetime.datetime.now().hour or \
                (int(spited_hour[0]) == datetime.datetime.now().hour and
                 int(spited_hour[1]) <= datetime.datetime.now().minute):
            message.reply_text("That hour already passed...\nFix it.\n\n" + GET_HOUR_MSG)
            return HOUR

    data['hour'] = hour
    reply_keyboard = [['Yes!', 'No!']]

    message.reply_text(CONF_TIME_MSG.format(data['date'], data['hour']) + REMIND_CANCEL_MSG,
                       reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
    return CONFIRM_TIME


def is_time_good(bot, update, user_data):
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
        reply_keyboard = tools.build_menu(['Every day', 'Every month', 'Custom', 'Nope'], 3)

        message.reply_text('Good!\n\nNow ' + GET_REP_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return REPEAT
    else:
        reply_keyboard = tools.build_menu(['Today', 'Tomorrow', 'No, a different date'], 2)

        message.reply_text('Well...\nlet\'s fix it.\n\n' + GET_DATE_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return DATE


def get_repeat_type(bot, update, user_data):
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

    reply_keyboard = [['Yes!', 'No!']]

    if message.text == 'Every day':
        data['repeat'] = Repeat(type=EVERY_DAY, days=None)
    elif message.text == 'Every month':
        data['repeat'] = Repeat(type=EVERY_MONTH, days=None)
    elif message.text == 'Custom':
        reply_keyboard = tools.build_menu(DAYS, 3)

        data['custom_repeat'] = []
        message.reply_text(GET_C_REP_MSG.format('None'),
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return CUSTOM_DAYS
    else:
        data['repeat'] = Repeat(type=NO_REP, days=None)
        message.reply_text(CONF_REP_MSG.format("with no repeat") + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return CONFIRM_REPEAT

    message.reply_text(CONF_REP_MSG.format(message.text.lower()) + REMIND_CANCEL_MSG,
                       reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
    return CONFIRM_REPEAT


def handle_custom_days(bot, update, user_data):
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
    chosen_days = data['custom_repeat']  # type: list

    if message.text == 'Done':
        data['repeat'] = Repeat(type=CUSTOM, days=chosen_days)
        reply_keyboard = [['Yes!', 'No!']]
        message.reply_text(CONF_REP_MSG.format('every ' + ', '.join([DAYS[i] for i in chosen_days])),
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return CONFIRM_REPEAT
    else:
        chosen_days.append(DAYS.index(message.text))

        available_days = list(DAYS)
        [available_days.remove(DAYS[i]) for i in chosen_days]
        reply_keyboard = tools.build_menu(available_days, 3, footer_buttons=['Done'])

        message.reply_text(GET_C_REP_MSG.format(', '.join([DAYS[i] for i in chosen_days])) + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return CUSTOM_DAYS


def is_repeat_good(bot, update, user_data, job_queue):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :param job_queue: the job queue
    :type job_queue: telegram.ext.JobQueue
    :return:
    """
    message = update.message  # type: telegram.Message
    data = user_data['remind']  # type: dict

    if message.text == "Yes!":
        date, hour = [int(n) for n in str(data['date']).split('.')], [int(n) for n in str(data['hour']).split(':')]
        the_time = datetime.datetime(day=date[0], month=date[1], year=date[2], hour=hour[0], minute=hour[1])
        reminder = Reminder(text=data['message'], time=the_time, repeat=data['repeat'])

        set_reminder(reminder, job_queue)

        message.reply_text(END_MSG)
        message.reply_text("user_data:\n" + str(user_data))
        return ConversationHandler.END
    else:
        reply_keyboard = tools.build_menu(['Every day', 'Every month', 'Custom', 'Nope'], 3)

        message.reply_text('Good!\n\nNow ' + GET_REP_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return REPEAT


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


def set_reminder(reminder, job_queue):
    """
    sets the reminder

    :param reminder: the reminder with all the data
    :type reminder: Reminder
    :param job_queue: the job queue
    :type job_queue: telegram.ext.JobQueue
    :return:
    """
    pass


tools.add_conversations(ConversationHandler(
    entry_points=[CommandHandler('remind', remind, pass_user_data=True)],

    states={
        MESSAGE: [MessageHandler(Filters.text, get_message, pass_user_data=True)],

        CONFIRM_MESSAGE: [RegexHandler('^(Yes!|No!)$', is_message_good, pass_user_data=True)],

        DATE: [RegexHandler('^(Today|Tomorrow|No, a different date)$', select_date_type, pass_user_data=True)],

        CUSTOM_DATE: [RegexHandler('^(0{0,1}[1-9]|[12][0-9]|3[01])\.(0{0,1}[1-9]|1[012])\.20\d\d$',
                                   handle_custom_date, pass_user_data=True),
                      RegexHandler('^([Ss]unday|[Mm]onday|[Tt]uesday|[Ww]ednesday|[Tt]hursday|[Ff]riday|[Ss]aturday)$',
                                   handle_day_name, pass_user_data=True)],

        HOUR: [RegexHandler('^([01]{0,1}[0-9]|2[0-3]):[0-5]{0,1}[0-9]$', get_hour, pass_user_data=True)],

        CONFIRM_TIME: [RegexHandler('^(Yes!|No!)$', is_time_good, pass_user_data=True)],

        REPEAT: [RegexHandler('^(Every day|Every month|Custom|Nope)$', get_repeat_type, pass_user_data=True)],

        CUSTOM_DAYS: [RegexHandler('^([Ss]unday|[Mm]onday|[Tt]uesday|[Ww]ednesday|[Tt]hursday|[Ff]riday|'
                                   '[Ss]aturday|Done)$',
                                   handle_custom_days, pass_user_data=True)],

        CONFIRM_REPEAT: [RegexHandler('^(Yes!|No!)$', is_repeat_good, pass_user_data=True, pass_job_queue=True)],

    },

    fallbacks=[CommandHandler('cancel', cancel)]
))
