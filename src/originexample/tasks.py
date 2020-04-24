from redis import Redis
from celery import Celery
from contextlib import contextmanager

from originexample.settings import REDIS_BROKER_URL, REDIS_BACKEND_URL

from .cache import redis


# The celery app uses a Redis connection to broker tasks and results
celery_app = Celery(
    main='tasks',
    broker=REDIS_BROKER_URL,
    backend=REDIS_BACKEND_URL,
)


@contextmanager
def lock(key):
    my_lock = redis.lock(key)
    have_lock = False
    try:
        have_lock = my_lock.acquire(blocking=True, blocking_timeout=2)
        yield have_lock
    finally:
        if have_lock:
            my_lock.release()
