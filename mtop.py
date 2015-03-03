#!/usr/bin/env python

import psutil
import time


class IOCount(object):
    def __init__(self):
        self.read_count = 0
        self.write_count = 0
        self.read_bytes = 0
        self.write_bytes = 0

    def count(self, p):
        try:
            io = p.io_counters()
        except AttributeError:
            pass
        else:
            self.read_count += io.read_count
            self.write_count += io.write_count
            self.read_bytes += io.read_bytes
            self.write_bytes += io.write_bytes


class ThreadCount(object):
    def __init__(self):
        self.threads = 0

    def count(self, p):
        try:
            self.threads += p.num_threads()
        except psutil.AccessDenied:
            pass


class MemoryCount(object):
    def __init__(self):
        self.memory = dict()

    def count(self, p):
        try:
            for m in p.memory_maps(grouped=True):
                if m.path not in self.memory:
                    if m.path[0] == '/':
                        self.memory[m.path] = m
                if m.path[0] != '/':
                    print m.path, m.rss
        except psutil.AccessDenied:
            pass


class Stats(object):

    def __init__(self, *users):
        self.users = users

    def the_procs(self):
        for p in psutil.process_iter():
            try:
                username = p.username()
                if username in self.users:
                    yield p
            except psutil.AccessDenied:
                pass

    def poll(self, interval):
        time.sleep(interval)
        thread = ThreadCount()
        io = IOCount()
        memory = MemoryCount()
        for p in self.the_procs():
            for c in [thread, io, memory]:
                c.count(p)
        return thread, io, memory

    def loop(self, interval=1):
        try:
            delta = 0
            while True:
                thread, io, memory = self.poll(delta)
                print thread.threads
                delta = interval
        except (KeyboardInterrupt, SystemExit):
            pass


if __name__ == '__main__':
    import sys

    s = Stats(sys.argv[1])
    s.loop(5)
