import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

_LOG_DIRECTORY = f"{os.environ.get('LOG_FILEPATH', './logs')}/user/"
if not os.path.exists(_LOG_DIRECTORY):
    os.mkdir(_LOG_DIRECTORY)


class UserLogger:
    """this class will be used to store user activities in separated log files"""
    __log_formatter = logging.Formatter('%(asctime)s %(name)s %(module)s  %(lineno)d %(levelname)s %(message)s')

    def __init__(self, user_email: Optional[str] = None):
        self.__user_email = user_email
        self.__debug_level = logging.DEBUG
        # only one logger will be used and its file handler will be updated on demand
        self.__file_logger = logging.getLogger("user-logger")
        self.set_user_email(self.__user_email, self.__debug_level)

    def set_user_email(self, user_email: Optional[str], log_level: int = logging.DEBUG):
        """set user email of the logger and change its file handler consequently"""
        if user_email is None:
            user_email = '000000-Default'

        # remove all handlers from the logger
        for handler in self.__file_logger.handlers:
            self.__file_logger.removeHandler(handler)
        # create new handler and attach it to logger
        log_handler = TimedRotatingFileHandler(f"{_LOG_DIRECTORY}/{user_email}.log",
                                               when='midnight',
                                               backupCount=7,
                                               utc=True)
        log_handler.setFormatter(UserLogger.__log_formatter)
        self.__file_logger.addHandler(log_handler)

        # set wanted log level
        self.__debug_level = log_level
        self.__file_logger.setLevel(self.__debug_level)

    @property
    def file_logger(self):
        return self.__file_logger


