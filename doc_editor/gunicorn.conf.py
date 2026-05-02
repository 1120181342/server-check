# -*- coding: utf-8 -*-
"""
文档编辑器 - Gunicorn生产环境配置
"""

import multiprocessing
import os

# 基础配置
bind = os.getenv('GUNICORN_BIND', 'unix:/tmp/doc_editor.sock')
# bind = '127.0.0.1:8000'  # 或者使用TCP端口

# 工作进程配置
# 推荐：CPU核心数 * 2 + 1
workers = os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1)
worker_class = 'sync'  # 对于CPU密集型使用sync，对于IO密集型使用gevent

# 线程配置（每个worker的线程数）
threads = os.getenv('GUNICORN_THREADS', 2)

# 工作进程超时时间（秒）
timeout = 120

# 优雅关闭超时时间（秒）
graceful_timeout = 30

# 保持连接时间（秒）
keepalive = 5

# 请求处理后重启worker（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 预加载应用（减少内存占用，加快启动）
preload_app = True

# 进程名称
proc_name = 'doc_editor'

# 日志配置
accesslog = '-'  # 标准输出
errorlog = '-'   # 标准错误
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# 访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 守护进程配置（如果需要）
# daemon = True
# pidfile = '/var/run/doc_editor.pid'
# user = 'www-data'
# group = 'www-data'

# 环境变量
raw_env = [
    'FLASK_ENV=production',
]


def when_ready(server):
    """服务器启动时的钩子函数"""
    server.log.info("文档编辑器服务已启动，监听: %s" % bind)
    server.log.info("工作进程数: %s, 线程数: %s" % (workers, threads))


def pre_fork(server, worker):
    """fork工作进程前的钩子函数"""
    pass


def post_fork(server, worker):
    """fork工作进程后的钩子函数"""
    server.log.info("工作进程 #%s 已启动" % worker.id)


def worker_int(worker):
    """工作进程收到中断信号时的钩子函数"""
    worker.log.info("工作进程 #%s 收到中断信号" % worker.id)


def worker_abort(worker):
    """工作进程异常终止时的钩子函数"""
    worker.log.info("工作进程 #%s 异常终止" % worker.id)
