# -*- coding: utf-8 -*-
"""
    futuro.tasks
    ~~~~~~~~~~~~~~~~~

    Functions and classes related to unit definitions and conversions.

    :copyright: 2013 by Hernan E. Grecco, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import, print_function

from collections import defaultdict
import concurrent.futures


class TasksGroup(object):
    """A group of tasks with dependencies.

    >>> tasks = TasksGroup()
    >>> @tasks.add()
    ... def first():
    ...     print(1)
    >>> @tasks.add(first)
    ... def second():
    ...     print(2)
    >>> import concurrent.futures
    >>> with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    ...     tasks.run(executor)
    1
    2
    """

    def __init__(self):
        #: Map functions to their upstream connections (dependencies)
        self._upstream = {}
        #: Map functions to their downstream connections
        self._downstream = defaultdict(set)

    def add(self, *depends_on):
        """Add a task to the group.
        """
        def decorator(func):
            self._upstream[func] = depends_on
            for f in depends_on:
                self._downstream[f].add(func)
            return func

        return decorator

    def run(self, executor):
        """Run tasks respecting the dependencies using an executor.
        """
        count_deps = {task: len(deps) for task, deps in self._upstream.items()}
        base_tasks = {task for task, count in count_deps.items() if count == 0}

        future_to_task = {executor.submit(task): task for task in base_tasks}
        not_done = set(future_to_task.keys())

        wait = concurrent.futures.wait
        FIRST_COMPLETED = concurrent.futures.FIRST_COMPLETED
        while not_done:
            done, not_done = wait(not_done, return_when=FIRST_COMPLETED)
            for future in done:
                task = future_to_task[future]
                for f in self._downstream[task]:
                    count_deps[f] -= 1
                    if count_deps[f] == 0:
                        fut = executor.submit(f)
                        future_to_task[fut] = f
                        not_done.add(fut)

        return {value: key for key, value in future_to_task}


__all__ = ['TasksGroup']
