#!/usr/bin/env python

# Shows how the TasksGroup is used.

import time

# Import TasksGroup and create an instance
from futuro import TasksGroup
tasks = TasksGroup()

# Functions are added to the group using the `add` decorator.
@tasks.add()
def f1():
    time.sleep(.4)
    print(time.time(), 1)


# Dependencies are indicated in the arguments
@tasks.add(f1)
def f2():
    time.sleep(4)
    print(time.time(), 2)


@tasks.add(f1)
def f3():
    time.sleep(.4)
    print(time.time(), 3)


# Multiple dependencies can be specified
@tasks.add(f2, f3)
def f4():
    time.sleep(.4)
    print(time.time(), 4)

# The executor is imported from the standard library or from futuro
from concurrent.futures import ThreadPoolExecutor

# The task is run using a predefined the executor.
with ThreadPoolExecutor(max_workers=2) as executor:
    tasks.run(executor)
