from datetime import timedelta
import lxml.html as lh
import urllib.request
import collections
import telegram
import imgkit
import json
import os

import tools

TimetableChange = collections.namedtuple('TimetableChange', 'title data')
SchoolNews = collections.namedtuple('SchoolNews', 'data')
Update = collections.namedtuple('Update', 'timetable_changes school_news')

DIR = os.path.dirname(__file__) + '/'
REGISTERED_FILE = DIR + 'registered'
CACHE_FILE = DIR + 'cache'
IMG_LOC = DIR + 'out.jpg'
RTL_FIX = DIR + 'fix_rtl.css'
img_kit_options = {
    'encoding': "UTF-8",
    'quiet': ''
}

tools.create_json_list_file_if_not_exits(REGISTERED_FILE)
tools.create_json_list_file_if_not_exits(CACHE_FILE)

with open(RTL_FIX, 'w') as f:
    f.write("*{direction: rtl;}\n")


def get_updates():
    url = "http://www.smartscreen.co.il/viewScreen.aspx?screenID=776&tokenID=865cea7404587749e7332b18e68e825cb05e0d2f"

    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)'
                          ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )
    site = urllib.request.urlopen(req)
    content = site.read()

    root = lh.fromstring(content).xpath("//tr[@id='headerRow']")[0]

    timetable_changes_list, school_news_list = [], []

    timetable_changes, school_news = root
    try:
        timetable_changes = timetable_changes[0][0]
    except IndexError:
        pass
    try:
        school_news = school_news[0][0]
    except IndexError:
        pass

    for timetable_change in timetable_changes:
        title = timetable_change.xpath('h1')
        if title:
            title = title[0].text
        else:
            title = ""

        timetable_changes_list.append(TimetableChange(title, lh.tostring(timetable_change).decode('UTF-8')))

    for school_update in school_news:
        school_news_list.append(SchoolNews(lh.tostring(school_update).decode('UTF-8')))

    return Update(timetable_changes_list, school_news_list)


def filter_updates_timetable(update, filters=None):
    """

    :param update: the Update object
    :type update: Update
    :param filters: list of the filters (one of them must be to save to update)
    :type filters: List
    :return: the new Update
    """
    timetable_changes = []

    if filters is None:
        return update

    for timetable_change in update.timetable_changes:
        if any([a for a in timetable_change.title.split() if a in filters]):
            timetable_changes.append(timetable_change)
    return Update(timetable_changes, update.school_news)


def get_update_if_changed(filters=None):
    updates = filter_updates_timetable(get_updates(), filters=filters)
    with open(CACHE_FILE, 'r') as temp_file:
        cached = json.load(temp_file)
    if cached != update_to_list(updates):
        with open(CACHE_FILE, 'w') as temp_file:
            json.dump(updates, temp_file)
        if update_to_list(updates) == [[], [["<div>&#160;</div>"]]]:
            return None
        else:
            return updates
    else:
        return None


def generate_image(update):
    """

    :param update: the Update object
    :type update: Update
    :return: image location
    """
    if update is None or update_to_list(update) == [[], [["<div>&#160;</div>"]]]:
        return None

    the_code = ''
    for any_update in update.timetable_changes + update.school_news:
        the_code += any_update.data + ' <br> <div style="border-bottom: dotted;"></div> <br>'

    imgkit.from_string(the_code, IMG_LOC, options=img_kit_options, css=RTL_FIX)
    return IMG_LOC


def update_to_list(update):
    return [[list(a) for a in update.timetable_changes], [list(a) for a in update.school_news]]


@tools.register_command('getschupdates')
def get_school_updates(bot, update):
    """
    Sends updated news from school
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    message = update.message  # type: telegram.Message
    path = generate_image(filter_updates_timetable(get_updates(), filters=['יב', 'יב7']))
    if path is not None:
        message.reply_photo(open(path, 'rb'))
    else:
        message.reply_text("Sorry... There are no news!")


@tools.register_command('regschnews')
def register_to_school_updates(bot, update):
    """
    Register this chat to get update from school
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    message = update.message  # type: telegram.Message

    with open(REGISTERED_FILE, 'r') as temp_file:
        registers_list = set(json.load(temp_file))
    registers_list.add(message.chat_id)
    with open(REGISTERED_FILE, 'w') as temp_file:
        json.dump(list(registers_list), temp_file)
    message.reply_text('Done!')


def sending_job(bot, job):
    """

    :param bot: the bot class
    :type bot: telegram.Bot
    :param job: the job object
    :type job: Job
    :return:
    """
    updates = get_update_if_changed(filters=['יב', 'יב7'])
    if updates is not None:
        with open(REGISTERED_FILE, 'r') as temp_file:
            registers_list = json.load(temp_file)

        for chat_id in registers_list:
            bot.send_photo(chat_id, open(generate_image(updates), 'rb'))


@tools.register_init
def init(updater):
    updater.dispatcher.job_queue.run_repeating(callback=sending_job, interval=timedelta(minutes=30), first=0)
