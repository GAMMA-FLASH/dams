
import logging
from os import pipe
from pathlib import Path
from time import strftime

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Logger(metaclass=Singleton):

    def set_logger(self):
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m-%d %H:%M')
        self.sh = logging.StreamHandler()
        self.sh.setFormatter(self.formatter)
        self.sh.setLevel("INFO")


    def getLogger(self, loggerName):

        logger = logging.getLogger(loggerName)

        logger.addHandler(self.sh)

        return logger