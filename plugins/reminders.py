import hashlib
import re
import json
import telegram

from telegram import ForceReply
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import RegexHandler
from telegram.ext import JobQueue
from telegram.ext import Job

from collections import namedtuple
from datetime import datetime, timedelta

from pprint import pprint

import tools

CHOOSE, LIST, CHOOSE_ACTION, CONFIRM_DELETE, MESSAGE, CONFIRM_MESSAGE, DATE, \
    CUSTOM_DATE, HOUR, CONFIRM_TIME, REPEAT, CUSTOM_DAYS, CONFIRM_REPEAT = range(13)
EVERY_DAY, CUSTOM, NO_REP = range(3)

REMIND_CANCEL_MSG = '\n(Remember, if you regret, just use /cancel to discard)\n'

START_MSG = 'What can i help you with reminders?\n'
NEW_MSG = 'What do you need me to remind you of?\n'
LIST_MSG = 'Choose the reminder you wish to modify.\n'
LIST_EMPTY_MSG = 'There are no reminders in this chat.\n'
REMINDER_CHOSE_MSG = 'Reminder on {0}:\n"{1}"\nAnd it {2}.\n\nWhat would you like to do with it?\n'
CONF_DELETE_MSG = 'Are you sure you want to delete this reminder?\n'
CONF_TEXT_MSG = 'Are you sure that you want to be reminded about "{0}"?\n'
GET_DATE_MSG = 'Should i remind you of that today or tomorrow?\n'
GET_C_DATE_MSG = 'Tell me on what day do you need to be reminded please, \n' \
                 'with a date in this format - DD.MM.YYYY (ex: 1.1.2000),' \
                 '\nor just tell me what day (ex: sunday)\n'
GET_HOUR_MSG = 'What time do you need me to remind you of that? Please write in this format - HH:MM\n'
CONF_TIME_MSG = 'So let\'s see if i got it right. You want me to remind you on {0} at {1}. Am I correct?\n'
GET_REP_MSG = 'Do you need to be reminded of that repeatedly? For instance, every week?\n'
GET_C_REP_MSG = 'Choose the days you want it to repeat.\n\nYou already chose those days:\n{0}\n'
CONF_REP_MSG = 'All right, you want me to remind you {0}. Correct?\n'
END_MSG = 'Excellent! Your reminder has been set! \n'
CANCEL_MSG = 'Well, okay, Then why\'d you ask for it...'

TO_REMIND_MSG = 'I was told to remind you of this:\n\n{0}'

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
WEEK_LENGTH = 7
DATE_FORMAT = '%-d.%-m.%Y'

FILE_NAME = 'reminders.json'

Repeat = namedtuple('Repeat', 'type days')
Reminder = namedtuple('Reminder', 'text time repeat chat_id')

tools.create_json_list_file_if_not_exits(FILE_NAME)


def get_future_weekday_date(name):
    """
    :param name: the name of the day
    :type name: str
    :return: Datetime
    """
    name = name.lower()
    if name in DAYS:
        day_num = DAYS.index(name)
        today = datetime.today()
        if today.weekday() <= day_num:
            days = day_num - today.weekday()
        else:
            days = WEEK_LENGTH - (today.weekday() - day_num)
        return today + timedelta(days=days)
    else:
        return None


def remind(bot, update, user_data):
    """
    show the menu of the remind system
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :return:
    """
    reply_keyboard = [['Create a new reminder'], ['Modify exiting reminders']]

    update.message.reply_text(
        START_MSG + REMIND_CANCEL_MSG,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))

    return CHOOSE


def choose_what_to_do(bot, update, user_data, job_queue):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :param job_queue: the job queue
    :type job_queue: JobQueue
    :return:
    """
    message = update.message  # type: telegram.Message

    user_data['remind'] = dict()

    if message.text == 'Create a new reminder':
        update.message.reply_text(NEW_MSG + REMIND_CANCEL_MSG, reply_markup=ForceReply(selective=True))
        return MESSAGE
    elif message.text == 'Modify exiting reminders':
        jobs_text = []
        for job in job_queue.jobs():  # type: Job
            if job.enabled and job.context['chat_id'] == message.chat_id:
                jobs_text.append('{} - {}\n"{}"\nid({})'.format(
                    job.context['time'], job.context['repeat'], job.context['text'], job.name))
        if len(jobs_text) > 0:
            reply_keyboard = tools.build_menu(jobs_text, 1)
            message.reply_text(LIST_MSG + REMIND_CANCEL_MSG,
                               reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
            return LIST
        else:
            message.reply_text(LIST_EMPTY_MSG)
            return ConversationHandler.END


def handle_reminder_choose(bot, update, user_data, job_queue):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :param job_queue: the job queue
    :type job_queue: JobQueue
    :return:
    """
    message = update.message  # type: telegram.Message
    name = str(re.search('.*id\((b\'.+\')\)', message.text).group(1))
    data = user_data['remind']  # type: dict

    for job in job_queue.jobs():  # type: Job
        if job.enabled and job.context['chat_id'] == message.chat_id and job.name == name:
            reply_keyboard = tools.build_menu(['delete'], 2)
            message.reply_text(REMINDER_CHOSE_MSG.format(
                job.context['time'], job.context['text'], job.context['repeat']) + REMIND_CANCEL_MSG,
                               reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
            data['chosen_job'] = job
            return CHOOSE_ACTION
    else:
        jobs_text = []
        for job in job_queue.jobs():  # type: Job
            if job.enabled and job.context['chat_id'] == message.chat_id:
                jobs_text.append('{} - {}\n"{}"\nid({})'.format(
                    job.context['time'], job.context['repeat'], job.context['text'], job.name))
        if len(jobs_text) > 0:
            reply_keyboard = tools.build_menu(jobs_text, 1)
            message.reply_text('Invalid ID\n' + LIST_MSG + REMIND_CANCEL_MSG,
                               reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
            return LIST
        else:
            message.reply_text(LIST_EMPTY_MSG)
            return ConversationHandler.END


def conf_delete(bot, update, user_data):
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
    reply_keyboard = [['Yes!', 'No!']]

    message.reply_text(CONF_DELETE_MSG,
                       reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
    return CONFIRM_DELETE


def delete(bot, update, user_data, job_queue):
    """
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :param job_queue: the job queue
    :type job_queue: JobQueue
    :return:
    """
    message = update.message  # type: telegram.Message
    data = user_data['remind']  # type: dict

    if message.text == 'Yes!':
        data['chosen_job'].enabled = False
        message.reply_text("Reminder removed.")
        return ConversationHandler.END
    else:
        message.reply_text("OK")
        return ConversationHandler.END


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
        message.reply_text('Well...\nLet\'s fix it.\n\n' + NEW_MSG + REMIND_CANCEL_MSG,
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
        data['date'] = datetime.today().strftime(DATE_FORMAT)
    elif message.text == "Tomorrow":
        data['date'] = (datetime.today() + timedelta(days=1)).strftime(DATE_FORMAT)
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

    if data['date'] == datetime.today().strftime(DATE_FORMAT):
        spited_hour = hour.split(':')
        if int(spited_hour[0]) < datetime.now().hour or \
                (int(spited_hour[0]) == datetime.now().hour and
                         int(spited_hour[1]) <= datetime.now().minute):
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
        reply_keyboard = tools.build_menu(['Every day', 'Custom', 'Nope'], 2)

        message.reply_text('Good!\n\n' + GET_REP_MSG + REMIND_CANCEL_MSG,
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
        return REPEAT
    else:
        reply_keyboard = tools.build_menu(['Today', 'Tomorrow', 'No, a different date'], 2)

        message.reply_text('Well...\nLet\'s fix it.\n\n' + GET_DATE_MSG + REMIND_CANCEL_MSG,
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
    :type job_queue: JobQueue
    :return:
    """
    message = update.message  # type: telegram.Message
    data = user_data['remind']  # type: dict

    if message.text == "Yes!":
        date, hour = [int(n) for n in str(data['date']).split('.')], [int(n) for n in str(data['hour']).split(':')]
        the_time = datetime(day=date[0], month=date[1], year=date[2], hour=hour[0], minute=hour[1])
        reminder = Reminder(text=data['message'], time=the_time, repeat=data['repeat'], chat_id=message.chat_id)

        set_reminder(reminder, job_queue)

        message.reply_text(END_MSG)
        return ConversationHandler.END
    else:
        reply_keyboard = tools.build_menu(['Every day', 'Custom', 'Nope'], 2)

        message.reply_text('Ok, let\'s change that.\n\n' + GET_REP_MSG + REMIND_CANCEL_MSG,
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
    update.message.reply_text(CANCEL_MSG,
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def get_reminders_from_file():
    """
    returns the json object from the file

    :return:
    """
    with open(FILE_NAME, encoding='UTF-8') as f:
        data = json.load(f, object_hook=from_json)
    return data


def write_reminder(reminder):
    """
    write the reminder to the file

    :param reminder: the reminder with all the data
    :type reminder: Reminder
    :return:
    """
    the_obj = get_reminders_from_file()
    to_add = reminder._asdict()
    to_add['repeat'] = to_add['repeat']._asdict()
    the_obj.append(to_add)
    with open(FILE_NAME, 'w', encoding='UTF-8') as f:
        json.dump(the_obj, f, default=to_json, indent=2, ensure_ascii=False)


@tools.register_need_job_queue
def load_reminders(job_queue):
    """
    loads the reminders from the file to the job queue

    :param job_queue: the job queue
    :type job_queue: JobQueue
    :return:
    """
    refresh_saved_reminds()
    the_reminders = get_reminders_from_file()

    for a_remind in the_reminders:
        set_reminder(Reminder(text=a_remind['text'],
                              time=a_remind['time'],
                              repeat=Repeat(type=a_remind['repeat']['type'], days=a_remind['repeat']['days']),
                              chat_id=a_remind['chat_id']), job_queue, write_to_file=False)


def set_reminder(reminder, job_queue, write_to_file=True):
    """
    sets the reminder

    :param reminder: the reminder with all the data
    :type reminder: Reminder
    :param job_queue: the job queue
    :type job_queue: JobQueue
    :param write_to_file: if it should write it to the file
    :type write_to_file: bool
    :return:
    """
    context = {'chat_id': reminder.chat_id,
               'text': reminder.text,
               'time': reminder.time.strftime(DATE_FORMAT + ' - %H:%M')}
    the_hash = str(hashlib.md5((str(context) + str(datetime.now())).encode()).digest())
    if write_to_file:
        write_reminder(reminder)
    if reminder.repeat.type == EVERY_DAY:
        context['repeat'] = "repeats every day"
        job_queue.run_daily(do_reminder, reminder.time, context=context, name=the_hash)
    elif reminder.repeat.type == CUSTOM:
        context['repeat'] = "repeats every " + ', '.join([DAYS[i] for i in reminder.repeat.days])
        job_queue.run_daily(do_reminder, reminder.time, days=tuple(reminder.repeat.days), context=context,
                            name=the_hash)
    else:
        context['repeat'] = "does not repeat"
        job_queue.run_once(do_reminder, reminder.time, context=context, name=the_hash)


tools.add_conversations(ConversationHandler(
    entry_points=[CommandHandler('remind', remind, pass_user_data=True)],

    states={
        CHOOSE: [RegexHandler('^(Create a new reminder|Modify exiting reminders)$',
                              choose_what_to_do, pass_user_data=True, pass_job_queue=True)],

        LIST: [MessageHandler(Filters.text,
                              handle_reminder_choose, pass_user_data=True, pass_job_queue=True)],

        CHOOSE_ACTION: [RegexHandler('^delete$', conf_delete, pass_user_data=True)],

        CONFIRM_DELETE: [RegexHandler('^(Yes!|No!)$', delete, pass_user_data=True, pass_job_queue=True)],

        MESSAGE: [MessageHandler(Filters.text, get_message, pass_user_data=True)],

        CONFIRM_MESSAGE: [RegexHandler('^(Yes!|No!)$', is_message_good, pass_user_data=True)],

        DATE: [RegexHandler('^(Today|Tomorrow|No, a different date)$', select_date_type, pass_user_data=True)],

        CUSTOM_DATE: [RegexHandler('^(0{0,1}[1-9]|[12][0-9]|3[01])\.(0{0,1}[1-9]|1[012])\.20\d\d$',
                                   handle_custom_date, pass_user_data=True),
                      RegexHandler('^([Ss]unday|[Mm]onday|[Tt]uesday|[Ww]ednesday|[Tt]hursday|[Ff]riday|[Ss]aturday)$',
                                   handle_day_name, pass_user_data=True)],

        HOUR: [RegexHandler('^([01]{0,1}[0-9]|2[0-3]):[0-5]{0,1}[0-9]$', get_hour, pass_user_data=True)],

        CONFIRM_TIME: [RegexHandler('^(Yes!|No!)$', is_time_good, pass_user_data=True)],

        REPEAT: [RegexHandler('^(Every day|Custom|Nope)$', get_repeat_type, pass_user_data=True)],

        CUSTOM_DAYS: [RegexHandler('^([Ss]unday|[Mm]onday|[Tt]uesday|[Ww]ednesday|[Tt]hursday|[Ff]riday|'
                                   '[Ss]aturday|Done)$',
                                   handle_custom_days, pass_user_data=True)],

        CONFIRM_REPEAT: [RegexHandler('^(Yes!|No!)$', is_repeat_good, pass_user_data=True, pass_job_queue=True)],

    },

    fallbacks=[CommandHandler('cancel', cancel)]
))


def do_reminder(bot, job):
    """

    :param bot: the bot class
    :type bot: telegram.Bot
    :param job: the job object
    :type job: Job
    :return:
    """
    bot.send_message(job.context['chat_id'], TO_REMIND_MSG.format(job.context['text']))
    refresh_saved_reminds()


def refresh_saved_reminds():
    the_reminders = get_reminders_from_file()
    for a_remind in the_reminders:
        if datetime.now() >= a_remind['time']:
            the_reminders.remove(a_remind)
    with open(FILE_NAME, 'w', encoding='UTF-8') as f:
        json.dump(the_reminders, f, default=to_json, indent=2, ensure_ascii=False)


def to_json(py_obj):
    if isinstance(py_obj, datetime):
        return {'__class__': 'datetime',
                '__value__': py_obj.timestamp()}
    raise TypeError(repr(py_obj) + ' is not JSON serializable')


def from_json(json_obj):
    if '__class__' in json_obj:
        if json_obj['__class__'] == 'datetime':
            return datetime.fromtimestamp(json_obj['__value__'])
    return json_obj
