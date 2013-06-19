# -*- coding: utf-8 -*-
"""
    futuro.implicitfutures
    ~~~~~~~~~~~~~~~~~~~~~~

    Implements an implicit future (aka Promise) class and a executor that use it.

    :copyright: 2013 by Hernan E. Grecco, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import, print_function

import gc as gc
import types as types
import inspect as inspect

from concurrent.futures import (Future as _Future,
                                ThreadPoolExecutor as _ThreadPoolExecutor)


_WRAPPER_TYPES = (type(object.__init__), type(object().__init__),)


def proxy0(data):
    def proxy1(): return data
    return proxy1


_CELLTYPE = type(proxy0(None).func_closure[0])


def replace_all_refs(org_obj, new_obj):
    """ Uses the :mod:`gc` module to replace all references to obj
    :attr:`org_obj` with :attr:`new_obj` (it tries it's best, anyway).

    :param org_obj: The obj you want to replace.
    :param new_obj: The new_obj you want in place of the old obj.

    :returns: The org_obj

    .. note:
        The obj returned is, by the way, the last copy of :attr:`org_obj` in
        memory; if you don't save a copy, there is no way to put state of the
        system back to original state.

    .. warning::

       This function does not work reliably on strings, due to how the
       Python runtime interns strings.

    Taken from: https://github.com/cart0113/pyjack

    """

    gc.collect()

    hit = False
    for referrer in gc.get_referrers(org_obj):

        # FRAMES -- PASS THEM UP
        if isinstance(referrer, types.FrameType):
            continue

        # DICTS
        if isinstance(referrer, dict):

            cls = None

            # THIS CODE HERE IS TO DEAL WITH DICTPROXY TYPES
            if '__dict__' in referrer and '__weakref__' in referrer:
                for cls in gc.get_referrers(referrer):
                    if inspect.isclass(cls) and cls.__dict__ == referrer:
                        break

            for key, value in referrer.items():
                # REMEMBER TO REPLACE VALUES ...
                if value is org_obj:
                    hit = True
                    value = new_obj
                    referrer[key] = value
                    if cls: # AGAIN, CLEANUP DICTPROXY PROBLEM
                        setattr(cls, key, new_obj)
                # AND KEYS.
                if key is org_obj:
                    hit = True
                    del referrer[key]
                    referrer[new_obj] = value

        # LISTS
        elif isinstance(referrer, list):
            for i, value in enumerate(referrer):
                if value is org_obj:
                    hit = True
                    referrer[i] = new_obj

        # SETS
        elif isinstance(referrer, set):
            referrer.remove(org_obj)
            referrer.add(new_obj)
            hit = True

        # TUPLE, FROZENSET
        elif isinstance(referrer, (tuple, frozenset,)):
            new_tuple = []
            for obj in referrer:
                if obj is org_obj:
                    new_tuple.append(new_obj)
                else:
                    new_tuple.append(obj)
            replace_all_refs(referrer, type(referrer)(new_tuple))

        # CELLTYPE
        elif isinstance(referrer, _CELLTYPE):
            def proxy0(data):
                def proxy1(): return data
                return proxy1
            proxy = proxy0(new_obj)
            newcell = proxy.func_closure[0]
            replace_all_refs(referrer, newcell)

        # FUNCTIONS
        elif isinstance(referrer, types.FunctionType):
            localsmap = {}
            for key in ['func_code', 'func_globals', 'func_name',
                        'func_defaults', 'func_closure']:
                orgattr = getattr(referrer, key)
                if orgattr is org_obj:
                    localsmap[key.split('func_')[-1]] = new_obj
                else:
                    localsmap[key.split('func_')[-1]] = orgattr
            localsmap['argdefs'] = localsmap['defaults']
            del localsmap['defaults']
            newfn = types.FunctionType(**localsmap)
            replace_all_refs(referrer, newfn)

        # OTHER (IN DEBUG, SEE WHAT IS NOT SUPPORTED).
        else:
            # debug:
            # print type(referrer)
            pass

    if hit is False:
        raise AttributeError("Object '%r' not found" % org_obj)

    return org_obj



def _swap_dict(obj1, obj2):
    obj1.__dict__, obj2.__dict__ = obj2.__dict__, obj1.__dict__


def _swap_slot(cls, obj1, obj2):
    values = []
    for attr in cls.__slots__:
        values.append(
            (attr,
             getattr(obj1, attr),
             getattr(obj2, attr),
             ))
    for attr, val1, val2 in values:
        setattr(obj1, attr, val2)
        setattr(obj2, attr, val1)


class ImplicitFutureMeta(type):

    def __new__(mcs, name, bases, dct):
        marker = '_implicit_future_meta'

        def make_method(method_name):
            def method(self, *args, **kw):
                result = self.result()
                args = [a.result() if hasattr(a, marker) else a
                        for a in args]
                kw = {k: v.result() if hasattr(v, marker) else v
                      for k, v in kw}
                return getattr(result, method_name)(*args, **kw)
            return method

        for method_name in mcs._special_names:
            dct[method_name] = make_method(method_name)
            dct[marker] = True

        return type.__new__(mcs, name, bases, dct)

    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
        '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__',
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
        '__truediv__', '__xor__', 'next',
    ]


class ImplicitFuture(_Future):
    """Represents the result of an asynchronous computation.
    Unlike (explicit) Futures, ImplicitFutures become the result of the
    computation when an operation is used on them.
    """
    __metaclass__ = ImplicitFutureMeta

    def __getattr__(self, item):
        result = self.result()
        return getattr(result, item)

    def result(self, timeout=None):
        res = super(ImplicitFuture, self).result(timeout)
        replace_all_refs(self, res)
        return res


from concurrent.futures.thread import _WorkItem


class ThreadPoolExecutor(_ThreadPoolExecutor):
    """An executor derived from the ThreadPoolExecutor of the standard library
    that returns an ImplicitFuture (instead of a Future) when submit is used.

    """

    def submit(self, fn, *args, **kwargs):
        """Submits a callable to be executed with the given arguments.

        Schedules the callable to be executed as fn(*args, **kwargs) and returns
        a ImplicitFuture instance representing the execution of the callable.

        Returns:
            An ImplicitFuture representing the given call.
        """
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')

            f = ImplicitFuture()
            w = _WorkItem(f, fn, args, kwargs)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f


__all__ = ['ThreadPoolExecutor', 'ImplicitFuture']
