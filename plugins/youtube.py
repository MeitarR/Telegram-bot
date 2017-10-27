from pprint import pprint

import youtube_dl
import telegram
import re
import os

from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler

from collections import namedtuple

import tools

DIR_NAME = 'youtube_mp3'

YoutubeID = namedtuple('YoutubeID', 'video list')

files_name = dict()

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
        Downloader(get_url(yt_id), bot, message.chat_id).do_your_thing()
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
    update.message.reply_text("bey")

    return ConversationHandler.END


tools.add_conversations(ConversationHandler(
    entry_points=[CommandHandler('youtube', youtube, pass_user_data=True, pass_args=True)],
    states={},
    fallbacks=[CommandHandler('cancel', cancel)]
))


class Downloader(object):
    def __init__(self, url, bot=None, chat_id=None):
        self.url = url
        self.chat_id = chat_id
        self.bot = bot
        with youtube_dl.YoutubeDL({'quiet': True}) as ydl:
            self.vid_data = ydl.extract_info(self.url, download=False)

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': DIR_NAME + '/%(title)s.%(ext)s',
            'restrictfilenames': True,
            'quiet': True,
            'progress_hooks': [self.gen_hook(self.vid_data['id'], bot, chat_id)],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    @staticmethod
    def gen_hook(vid, bot=None, chat_id=None):
        def _hook(data):
            global files_name
            if data['status'] == 'finished':
                filename = data['filename']
                file_tuple = os.path.split(os.path.abspath(filename))
                spliced_f_name = filename.split('.')
                spliced_f_name[-1] = 'mp3'
                files_name[vid] = '.'.join(spliced_f_name)
                if bot is None or chat_id is None:
                    print("Done downloading {}\nNow converting!".format('.'.join(file_tuple[1].split('.')[:-1])))
                else:
                    bot.send_message(chat_id,
                                     "Done downloading {}\n"
                                     "Now converting!".format('.'.join(file_tuple[1].split('.')[:-1])))
        return _hook

    def download(self):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            ydl.extract_info(self.url)
            global files_name
            return files_name[self.vid_data['id']]

    def upload_file(self, filename):
        if self.bot is None or self.chat_id is None:
            raise ValueError("bot or chat_id is None")
        self.bot.send_audio(self.chat_id, open(filename, 'rb'), timeout=5000)

    def do_your_thing(self):
        self.upload_file(self.download())

if __name__ == "__main__":
    pass
