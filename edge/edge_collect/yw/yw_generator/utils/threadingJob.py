import threading
import logging


class ThreadingJob(threading.Thread):
    def __init__(self, name, interval, function):
        threading.Thread.__init__(self, name=name)
        self._name = name
        self._logger = logging.getLogger(__name__)
        self.interval = interval
        self.gen_func = function
        self.stop_thread = threading.Event()
        self.daemon = True

    def run(self):
        self._logger.info("Start %s parallel process" % self._name)
        while not self.stop_thread.is_set():
            if not self.stop_thread.is_set():
                self.gen_func()
            self.stop_thread.wait(self.interval)
        self._logger.info("Stop %s  parallel process" % self._name)

    def cancel(self):
        self.stop_thread.set()

