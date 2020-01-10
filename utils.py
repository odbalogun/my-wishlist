import os
from datetime import date
import random
import string


def get_file_path():
    file_path = os.path.join(os.path.dirname(__file__), 'static')

    try:
        os.mkdir(file_path)
    except OSError:
        pass
    return file_path


def get_relative_file_path(model_path, end_path):
    # file_path = os.path.join('uploads', model_path, end_path)
    return f'uploads/{model_path}/{end_path}/'


def generate_full_file_path(model_path, end_path, filename):
    path = os.path.join(get_file_path(), get_relative_file_path(model_path, end_path))

    try:
        os.mkdir(path)
    except OSError:
        pass
    return os.path.join(path, filename)


def date_format(view, value):
    return value.strftime('%d %b, %Y %H:%M:%S')


def generate_folder_name():
    return date.today().strftime('%Y%m%d')


def generate_random_string(length=6):
    """Generate a random string of fixed length """
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))
