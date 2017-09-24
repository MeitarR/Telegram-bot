import telegram
import re

from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler

from collections import namedtuple

import tools

YoutubeID = namedtuple('YoutubeID', 'video list')


def is_youtube_video_url(url):
    """
    if it is a youtube video url it returns YoutubeID namedtuple with the id of the video
    else it returns False

    :param url: the url
    :type url: str
    :return: YoutubeID or bool
    """
    res = re.match(
        '^(?:http://|https://|)(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?$', url)
    if res is None:
        return False
    else:
        return YoutubeID(video=next(s for s in res.groups() if s), list=None)


def is_youtube_playlist_url(url):
    """
    if it is a youtube playlist url it returns YoutubeID namedtuple with the id of the playlist
    else it returns False

    :param url: the url
    :type url: str
    :return: YoutubeID or bool
    """
    res = re.match('^(?:http://|https://|)(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)$', url)
    if res is None:
        return False
    else:
        return YoutubeID(list=next(s for s in res.groups() if s), video=None)


def is_youtube_video_and_playlist_url(url):
    """
    if it is a youtube video and playlist url it returns YoutubeID namedtuple with the id of the video and the playlist
    else it returns False

    :param url: the url
    :type url: str
    :return: YoutubeID or bool
    """
    res = re.match(
        '^(?:http://|https://|)(?:www\.)?youtube\.com/watch\?(list=[a-zA-Z0-9_-]+|v=[a-zA-Z0-9_-]+)'
        '(&list=[a-zA-Z0-9_-]+|&v=[a-zA-Z0-9_-]+)$', url)
    if res is None:
        return False
    else:
        return YoutubeID(
            video=next(s.replace('&v=', '').replace('v=', '')
                       for s in res.groups() if s and str(s).lower().replace('&', '').startswith('v=')),
            list=next(s.replace('&list=', '').replace('list=', '')
                      for s in res.groups() if s and str(s).lower().replace('&', '').startswith('list=')))


def get_youtube_id(url):
    """
    returns YoutubeID if the url is valid
    else return None
    :param url: the url
    :type url: str
    :return:
    """
    r = is_youtube_video_url(url)
    if r:
        return r
    r = is_youtube_playlist_url(url)
    if r:
        return r
    else:
        return is_youtube_video_and_playlist_url(url)


def youtube(bot, update, user_data, args):
    """
    download songs with a link or with a name
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: the user's data
    :type user_data: dict
    :param args: the args from the user
    :type args: list
    :return:
    """
    message = update.message  # type: telegram.Message

    if len(args) == 0:
        message.reply_text("that's a conversation")
    elif len(args) == 1:
        message.reply_text(get_youtube_id(args[0]))
    else:
        message.reply_text("its a search cmd")

    return ConversationHandler.END


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

tools.add_conversations(ConversationHandler(
    entry_points=[CommandHandler('youtube', youtube, pass_user_data=True, pass_args=True)],

    states={},

    fallbacks=[CommandHandler('cancel', cancel)]
))
