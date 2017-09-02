import telegram


def ping_cmd(bot, update, user_data=None):
    """
    answers pong so the user will play ping pong with the bot

    :param bot: the bot class
    :type bot: telegram.Bot
    :param update: the update message
    :type update: telegram.Update
    :param user_data: user's data
    :type user_data: dict
    :return: None
    """
    message = update.message  # type: telegram.Message
    message.reply_text("pong")

__commands__ = {'ping': ping_cmd}
