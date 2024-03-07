from WorkerManager import WorkerManager
from DL2Checker__service.WorkerThread_checker import WorkerThread_DL2CCK
from DL2Checker__service.WorkerProcess_checker import WorkerProcess_DL2CCK

class WorkerManager_DL2CCK(WorkerManager):
	def __init__(self, manager_id, supervisor, name = "dl2ccheck_wm"):
		super().__init__(manager_id, supervisor, name)

	def start_worker_threads(self, num_threads):
		super().start_worker_threads(num_threads)
		#Worker threads
		for i in range(num_threads):
			thread = WorkerThread_DL2CCK(i, self, "dl2ccheck_thread")
			self.worker_threads.append(thread)
			thread.start()

	def start_worker_processes(self, num_processes):
		super().start_worker_processes(num_processes)
		# Worker processes
		for i in range(num_processes):
			process = WorkerProcess_DL2CCK(i, self, self.processdata_shared, "dl2ccheck_process")
			self.worker_processes.append(process)
			process.start()
			