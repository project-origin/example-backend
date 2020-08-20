from celery import Celery, Task
from celery.exceptions import Retry
from redis.exceptions import LockNotOwnedError
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
def lock(key, timeout):
    my_lock = redis.lock(key, timeout=timeout)
    have_lock = False
    try:
        have_lock = my_lock.acquire(blocking=True, blocking_timeout=2)
        yield have_lock
    finally:
        if have_lock:
            try:
                my_lock.release()
            except LockNotOwnedError:
                pass


@contextmanager
def many_locks(keys, timeout):
    with lock(keys[0], timeout=timeout) as acquired:
        if not acquired:
            yield False
        elif len(keys) == 1:
            yield True
        else:
            yield many_locks(keys[1:], timeout)
