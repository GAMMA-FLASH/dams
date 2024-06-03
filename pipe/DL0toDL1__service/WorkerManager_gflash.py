from WorkerManager import WorkerManager
from WorkerProcess import WorkerProcess
from WorkerThread import WorkerThread
from DL0toDL1__service.WorkerProcessor_gflash import WorkerDL0toDL1

class WorkerManager_DL0toDL1(WorkerManager):
	def __init__(self, manager_id, supervisor, name = "dl0dl1_wm"):
		super().__init__(manager_id, supervisor, name)

	def start_worker_threads(self, num_threads):
		super().start_worker_threads(num_threads)
		#Worker threads
		for i in range(num_threads):
			processor = WorkerDL0toDL1()
			thread = WorkerThread(i, self, "dl0dl1", processor)
			self.worker_threads.append(thread)
			thread.start()

	def start_worker_processes(self, num_processes):
		super().start_worker_processes(num_processes)
		# Worker processes
		for i in range(num_processes):
			processor = WorkerDL0toDL1()
			process = WorkerProcess(i, self, "dl0dl1", processor)
			self.worker_processes.append(process)
			process.start()