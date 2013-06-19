#!/usr/bin/env python

# Shows how the implicit futures are used.

# The ThreadPoolExecutor is imported from the futuro package.
# This executor is exactly as the one in the standard library but calling
# submit returns an ImplicitFuture (instead of a Future)
from futuro import ThreadPoolExecutor

# You use the ThreadPoolExecutors as you will normally do
with ThreadPoolExecutor(max_workers=2) as executor:
    x = executor.submit(lambda: 1)
    y = executor.submit(lambda: 2)
    z = executor.submit(lambda: 3)
    w = executor.submit(lambda: 0)

# But x, y, z, w are instances of the ImplicitFuture class
# and therefore any operation on them will rebind the variable
# to the result (blocking until ready if necessary)
from math import cos
print(x + 5)
print(y + z)
print(cos(w))
