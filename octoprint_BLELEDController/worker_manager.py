# coding=utf-8
from __future__ import absolute_import

from threading import Thread
import asyncio
import concurrent

class WorkerManager:
    def __init__(self, plugin):
        self.event_loop_thread = Thread(target=self._event_loop_worker)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()
        self.plugin = plugin
        self._logger = plugin._logger
        self._logger.debug("Worker thread started")

    def _event_loop_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=2))
        self.loop = loop
        return loop.run_forever()