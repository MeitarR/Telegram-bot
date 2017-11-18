import json

from collections import namedtuple

Command = namedtuple('Command', 'name function args_to_pass')

conversation_list = []


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def create_file_if_not_exits(file_name):
    """
    create a file with this name only if it now exits

    :param file_name: the name of the file
    :type file_name: str
    :return: None
    """
    try:
        open(file_name, "x").close()
    except FileExistsError:
        pass


def create_json_obj_file_if_not_exits(file_name):
    """
    create a file with this name only if it now exits and write to in empty json object

    :param file_name: the name of the file
    :type file_name: str
    :return: None
    """
    try:
        open(file_name, "x").close()
        with open(file_name, 'w', encoding='UTF-8') as f:
            json.dump({}, f)
    except FileExistsError:
        pass


def create_json_list_file_if_not_exits(file_name):
    """
    create a file with this name only if it now exits and write to in empty list

    :param file_name: the name of the file
    :type file_name: str
    :return: None
    """
    try:
        open(file_name, "x").close()
        with open(file_name, 'w', encoding='UTF-8') as f:
            json.dump([], f)
    except FileExistsError:
        pass


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.

    :param dict_args: iterator of all the dicts to merge
    :type dict_args: dict
    :return: the merged dict
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def function_registerer():
    """
    create a list of functions from all the functions that @ that function
    """
    functions_list = []

    def registrar_warp(name, args_to_pass=None):
        if args_to_pass is None:
            args_to_pass = dict()

        def registrar(func):
            functions_list.append(Command(name=name, function=func, args_to_pass=args_to_pass))
            return func

        return registrar

    registrar_warp.functions_list = functions_list
    return registrar_warp


def func_reg_need_job_queue():
    """
    create a list of functions from all the functions that @ that function
    """
    functions_list = []

    def registrar(func):
        functions_list.append(func)
        return func
    registrar.functions_list = functions_list
    return registrar


def add_conversations(*conversation_handlers):
    """
    adds the conversation handlers to the list
    :param conversation_handlers: the handlers to add
    :return: None
    """
    for conversation_handler in conversation_handlers:
        conversation_list.append(conversation_handler)


register_command = function_registerer()
register_callback = function_registerer()
register_need_job_queue = func_reg_need_job_queue()
register_init = func_reg_need_job_queue()
