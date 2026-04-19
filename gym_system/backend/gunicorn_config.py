import multiprocessing
import os

bind = '0.0.0.0:5000'

workers = multiprocessing.cpu_count() * 2 + 1

worker_class = 'gevent'

worker_connections = 1000

timeout = 60

keepalive = 5

backlog = 2048

threads = 4

loglevel = 'info'

accesslog = '-'
errorlog = '-'

capture_output = True

preload_app = True

max_requests = 1000
max_requests_jitter = 100

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    server.log.info("Worker about to be spawned (pid: %s)", worker.pid)

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
