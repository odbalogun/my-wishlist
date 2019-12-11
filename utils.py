import os
from datetime import date


def get_file_path(model_path, end_path):
    file_path = os.path.join(os.path.dirname(__file__), 'static', 'uploads', model_path, end_path)

    try:
        os.mkdir(file_path)
    except OSError:
        pass
    return file_path


def date_format(view, value):
    return value.strftime('%d %b, %Y %H:%M:%S')


def generate_folder_name():
    return date.today().strftime('%Y%m%d')
