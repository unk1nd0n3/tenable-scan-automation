import datetime
import json
import errno
from datetime import datetime
import os


def datetime_handler(x):
    """
    For for EC2 datetime.datetime() value handling
    :param x:
    :return: string
    """
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def create_dirs():
    """
    Create program working dirs
    :return: none
    """
    # Create directories
    directories = ['tmp', 'logs', 'json']
    for directory in directories:
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def write_json_to_file(filename, directory, data, time_bool=True):
    """
    Func for store json formatted data to local file
    :param filename: string
    :param directory: string
    :param data: dictionary
    :param time_bool: boolean
    :return: None
    """
    if not os.path.isdir(directory):
        os.makedirs(directory)
    if time_bool:
        scan_time = datetime.now()
        scan_start_time_str = scan_time.strftime('%Y%m%dT%H%M%S')
        filename = directory + '/' + scan_start_time_str + "-" + filename
    else:
        filename = directory + '/' + filename
    json_outfile = open(filename, 'w')
    json.dump(data, json_outfile, default=datetime_handler)
    json_outfile.close()
    return filename


def read_json_file(path):
    """
    Func for store json formatted data to local file
    :param path: string
    :return: none
    """
    try:
        return json.loads(open(path).read())
    except IOError:
        print("File is missed. Please check")

