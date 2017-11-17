import urllib.request
import lxml.html as lh
import collections
import imgkit
import telegram

# import tools

TimetableChange = collections.namedtuple('TimetableChange', 'title data')
SchoolNews = collections.namedtuple('SchoolNews', 'data')
Update = collections.namedtuple('Update', 'timetable_changes school_news')

RTL_FIX = 'fix_rtl.css'
img_kit_options = {
    'encoding': "UTF-8",
    'quiet': ''
}

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
    timetable_changes, school_news = timetable_changes[0][0], school_news[0][0]

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


def generate_image(update):
    """

    :param update: the Update object
    :type update: Update
    :return: image location
    """
    the_code = ''
    for any_update in update.timetable_changes + update.school_news:
        the_code += any_update.data + ' <br> <div style="border-bottom: dotted;"></div> <br>'

    imgkit.from_string(the_code, 'out.jpg', options=img_kit_options, css=RTL_FIX)


# not finished yet
# @tools.register_command('updates')
def timetable_cmd(bot, update):
    """
    sends the timetable for the selected day
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    message = update.message  # type: telegram.Message

    message.reply_text("good!")
