import telegram
import tools


@tools.register_command(name='ping')
def ping_cmd(bot, update):
    """
    Answers pong. The user can play ping pong with the bot.
    ***----***
    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :return:
    """
    message = update.message  # type: telegram.Message
    message.reply_text("pong")
