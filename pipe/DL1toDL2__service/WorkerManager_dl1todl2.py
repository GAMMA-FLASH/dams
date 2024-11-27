from WorkerManager import WorkerManager
from WorkerProcess import WorkerProcess
from WorkerThread import WorkerThread
from DL1toDL2__service.WorkerProcessor_dl1todl2 import WorkerDL1toDL2

class WorkerManager_DL1toDL2(WorkerManager):
	def __init__(self, manager_id, supervisor, name=""):
		super().__init__(manager_id, supervisor, name)

	def start_worker_threads(self, num_threads):
		super().start_worker_threads(num_threads)
		#Worker threads
		for i in range(num_threads):
			processor = WorkerDL1toDL2()
			thread = WorkerThread(i, self, self.supervisor.name_workers[self.manager_id], processor, self._workers_stop_event)
			self.worker_threads.append(thread)
			thread.start()

	def start_worker_processes(self, num_processes):
		super().start_worker_processes(num_processes)
		# Worker processes
		for i in range(num_processes):
			processor = WorkerDL1toDL2()
			process = WorkerProcess(i, self, self.supervisor.name_workers[self.manager_id], processor, self._workers_stop_event)
			self.worker_processes.append(process)
			process.start()
			