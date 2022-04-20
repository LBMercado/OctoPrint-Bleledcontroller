# coding=utf-8
from __future__ import absolute_import

from threading import Thread
import asyncio
import concurrent
import uuid

class WorkerManager:
    def __init__(self, plugin):
        self.event_loop_thread = Thread(target=self._event_loop_worker)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()
        self.plugin = plugin
        self._logger = plugin._logger
        self._logger.debug("Worker Manager: Worker thread started")
        self.task_list = {}

    def register_task(self, task: asyncio.Future, task_id: str = None):
        reg_task_id = task_id
        if reg_task_id is None:
            reg_task_id = str(uuid.uuid4())
        self.task_list[reg_task_id] = task
        self._logger.debug('Worker Manager: ' + 'Task registered with id: ' + reg_task_id)
        return str(reg_task_id)

    def deregister_task(self, task_id: str):
        if task_id in self.task_list:
            del self.task_list[task_id]
        self._logger.debug('Worker Manager: ' + 'Task deregistered with id: ' + task_id)

    def get_task(self, task_id: str):
        if task_id in self.task_list:
            return self.task_list[task_id]
        self._logger.debug('Worker Manager: ' + 'Task with id = ' + task_id + ' does not exist.')
        return None
    
    def _event_loop_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=2))
        self.loop = loop
        return loop.run_forever()