from pprint import pprint

import youtube_dl
import telegram
import threading
import re
import os

from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler

from collections import namedtuple
from os.path import basename, splitext

import tools

DIR_NAME = 'youtube_mp3'

YoutubeID = namedtuple('YoutubeID', 'video list')

if not os.path.exists(DIR_NAME):
    os.makedirs(DIR_NAME)


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


def get_url(youtube_id, force_playlist=False):
    if (force_playlist and youtube_id.list) or (not youtube_id.video and youtube_id.list):
        return "https://www.youtube.com/playlist?list={}".format(youtube_id.list)
    elif youtube_id.video:
        return "https://www.youtube.com/watch?v={}".format(youtube_id.video)
    else:
        return None


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
        yt_id = get_youtube_id(args[0])

        if yt_id:
            threading.Thread(target=Downloader(get_url(yt_id), bot, message.chat_id).download).start()
        else:
            message.reply_text("Sorry...\nI cant search (yet)")
    else:
        message.reply_text("Sorry...\nI cant search (yet)")

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
    update.message.reply_text("bey")

    return ConversationHandler.END


tools.add_conversations(ConversationHandler(
    entry_points=[CommandHandler('youtube', youtube, pass_user_data=True, pass_args=True)],
    states={},
    fallbacks=[CommandHandler('cancel', cancel)]
))


class MyLogger(object):
    def __init__(self, downloader, bot=None, chat_id=None):
        self.name = None
        self.downloader = downloader
        self.bot = bot
        self.chat_id = chat_id

    def debug(self, msg):
        if msg.startswith('[download] Destination: '):
            msg = msg.replace('[download] Destination: ', '')
            self.downloader.send_message("Started downloading {}".format(splitext(basename(msg))[0]))
        elif msg.startswith('[ffmpeg] Destination: '):
            self.name = msg.replace('[ffmpeg] Destination: ', '')
        elif msg.startswith('Deleting original file'):
            self.downloader.upload_file(self.name)

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class Downloader(object):
    def __init__(self, url, bot=None, chat_id=None):
        self.url = url
        self.chat_id = chat_id
        self.bot = bot
        self.vid_data = None
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': DIR_NAME + '/%(title)s.%(ext)s',
            'restrictfilenames': True,
            'quiet': True,
            'logger': MyLogger(self),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        self.update_info()

    def update_info(self):
        with youtube_dl.YoutubeDL({'quiet': True}) as ydl:
            self.vid_data = ydl.extract_info(self.url, download=False)

    def download(self):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([self.url])

    def upload_file(self, filename):
        if self.bot is None or self.chat_id is None:
            print("bot or chat_id is None so no file sent")
        else:
            self.bot.send_chat_action(self.chat_id, telegram.ChatAction.UPLOAD_AUDIO)
            self.bot.send_audio(self.chat_id, open(filename, 'rb'), timeout=5000)
            os.remove(filename)

    def send_message(self, message):
        if self.bot is None or self.chat_id is None:
            print("bot or chat_id is None so i print it: '{}'".format(message))
        else:
            self.bot.send_message(self.chat_id, message)
