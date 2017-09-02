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
