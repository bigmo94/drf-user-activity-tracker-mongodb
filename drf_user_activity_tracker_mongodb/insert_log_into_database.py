import logging
import time
from queue import Queue
from threading import Thread

from django.conf import settings

from drf_user_activity_tracker_mongodb.utils import MyCollection

logger = logging.getLogger('error')


class InsertLogIntoDatabase(Thread):

    def __init__(self):
        super().__init__()

        self.DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE = 50  # Default queue size 50
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE'):
            self.DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE = settings.DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE

        if self.DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE < 1:
            raise Exception("""
            DRF ACTIVITY TRACKER EXCEPTION
            Value of DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE must be greater than 0
            """)

        self.DRF_ACTIVITY_TRACKER_INTERVAL = 10  # Default DB insertion interval is 10 seconds.
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_INTERVAL'):
            self.DRF_ACTIVITY_TRACKER_INTERVAL = settings.DRF_ACTIVITY_TRACKER_INTERVAL

            if self.DRF_ACTIVITY_TRACKER_INTERVAL < 1:
                raise Exception("""
                DRF ACTIVITY TRACKER EXCEPTION
                Value of DRF_ACTIVITY_TRACKER_INTERVAL must be greater than 0
                """)

        self._queue = Queue(maxsize=self.DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE)

    def run(self) -> None:
        self.start_queue_process()

    def put_log_data(self, data):
        self._queue.put(data)

        if self._queue.qsize() >= self.DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE:
            self._start_bulk_insertion()

    def start_queue_process(self):
        while True:
            time.sleep(self.DRF_ACTIVITY_TRACKER_INTERVAL)
            self._start_bulk_insertion()

    def _start_bulk_insertion(self):
        bulk_item = []
        while not self._queue.empty():
            bulk_item.append(self._queue.get())
        if bulk_item:
            self._insert_into_data_base(bulk_item)

    def _insert_into_data_base(self, bulk_item):
        try:
            MyCollection().save(bulk_item)
        except Exception as e:
            message = "DRF ACTIVITY TRACKER EXCEPTION: {}, {}".format(str(e), type(e))
            logger.error(message)
            raise Exception(message)
