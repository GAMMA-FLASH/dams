from WorkerManager import WorkerManager
from DL0toDL2__service.WorkerThread_gflash import WorkerThread_DL0toDL2
from DL0toDL2__service.WorkerProcess_gflash import WorkerProcess_DL0toDL2

class WorkerManager_DL0toDL2(WorkerManager):
	def __init__(self, manager_id, supervisor, name = "dl0dl2"):
		super().__init__(manager_id, supervisor, name)

	def start_worker_threads(self, num_threads):
		super().start_worker_threads(num_threads)
		#Worker threads
		for i in range(num_threads):
			thread = WorkerThread_DL0toDL2(i, self, "dl0dl2_thread")
			self.worker_threads.append(thread)
			thread.start()

	def start_worker_processes(self, num_processes):
		super().start_worker_processes(num_processes)
		# Worker processes
		for i in range(num_processes):
			process = WorkerProcess_DL0toDL2(i, self, self.processdata_shared, "dl0dl2_process")
			self.worker_processes.append(process)
			process.start()
			