# Example (Same as tgroups1.py with different dependency graph)

from concurrent.futures import ThreadPoolExecutor
from futuro import TasksGroup

import time
tasks = TasksGroup()


@tasks.add()
def f1():
    time.sleep(.4)
    print(time.time(), 1)


@tasks.add(f1)
def f2():
    time.sleep(4)
    print(time.time(), 2)


@tasks.add(f1)
def f3():
    time.sleep(.4)
    print(time.time(), 3)


@tasks.add(f3)
def f4():
    time.sleep(.4)
    print(time.time(), 4)


with ThreadPoolExecutor(max_workers=2) as executor:
    tasks.run(executor)
