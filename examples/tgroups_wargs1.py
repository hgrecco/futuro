# Shows how the TasksGroup is used with functions with arguments.
# (see tgroups1.py)

from concurrent.futures import ThreadPoolExecutor
from futuro import TasksGroup

import time
tasks = TasksGroup()


def f(number, sleep_time):
    time.sleep(sleep_time)
    print(time.time(), number)

f1 = tasks.add()(lambda: f(1, .4))
f2 = tasks.add(f1)(lambda: f(2, 4))
f3 = tasks.add(f1)(lambda: f(3, .4))
f4 = tasks.add(f2, f3)(lambda: f(4, .4))

with ThreadPoolExecutor(max_workers=2) as executor:
    tasks.run(executor)
