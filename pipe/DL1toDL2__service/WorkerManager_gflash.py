from WorkerManager import WorkerManager
from DL1toDL2__service.WorkerThread_gflash import WorkerThread_DL1toDL2
from DL1toDL2__service.WorkerProcess_gflash import WorkerProcess_DL1toDL2

class WorkerManager_DL1toDL2(WorkerManager):
	def __init__(self, manager_id, supervisor, name = "dl1dl2_wm"):
		super().__init__(manager_id, supervisor, name)

	def start_worker_threads(self, num_threads):
		super().start_worker_threads(num_threads)
		#Worker threads
		for i in range(num_threads):
			thread = WorkerThread_DL1toDL2(i, self, "dl1dl2_thread")
			self.worker_threads.append(thread)
			thread.start()

	def start_worker_processes(self, num_processes):
		super().start_worker_processes(num_processes)
		# Worker processes
		for i in range(num_processes):
			process = WorkerProcess_DL1toDL2(i, self, self.processdata_shared, "dl1dl2_process")
			self.worker_processes.append(process)
			process.start()
			