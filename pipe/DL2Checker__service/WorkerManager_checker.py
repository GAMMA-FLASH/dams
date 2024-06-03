from WorkerManager import WorkerManager
from WorkerProcess import WorkerProcess
from WorkerThread import WorkerThread
from DL2Checker__service.WorkerProcessor_gflash import WorkerDL2CCK

class WorkerManager_DL2CCK(WorkerManager):
	def __init__(self, manager_id, supervisor, name = "dl2ccheck_wm"):
		super().__init__(manager_id, supervisor, name)

	def start_worker_threads(self, num_threads):
		super().start_worker_threads(num_threads)
		#Worker threads
		for i in range(num_threads):
			processor = WorkerDL2CCK()
			thread = WorkerThread(i, self, "dl2CHK", processor)
			self.worker_threads.append(thread)
			thread.start()

	def start_worker_processes(self, num_processes):
		super().start_worker_processes(num_processes)
		# Worker processes
		for i in range(num_processes):
			processor = WorkerDL2CCK()
			process = WorkerProcess(i, self, "dl2CHK", processor)
			self.worker_processes.append(process)
			process.start()
			