import time


class Event:
    def __init__(self,trx=None):

        # Receive time in secs past January 1, 1970, 00:00:00 (UTC)
        if trx is None:
            self.trx = time.time()
        else:
            self.trx = trx

    def read_data(self, raw):
        pass