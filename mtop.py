#!/usr/bin/env python

import psutil
import time

# Count class got a "key" property and are iterable


class IOCount(object):
    key = "io"

    def __init__(self):
        self.read_count = 0
        self.write_count = 0
        self.read_bytes = 0
        self.write_bytes = 0

    def count(self, p):
        try:
            io = p.io_counters()
        except AttributeError, psutil.NoSuchProcess:
            pass
        else:
            self.read_count += io.read_count
            self.write_count += io.write_count
            self.read_bytes += io.read_bytes
            self.write_bytes += io.write_bytes

    def __repr__(self):
        return "<IO %i %i %i %i>" % (self.read_count, self.write_count,
                                     self.read_bytes, self.write_bytes)

    def __iter__(self):
        yield "read_count", self.read_count
        yield "write_count", self.read_count
        yield "read_bytes", self.read_bytes
        yield "write_bytes", self.write_bytes


class ThreadCount(object):
    key = "thread"

    def __init__(self):
        self.threads = 0

    def count(self, p):
        try:
            self.threads += p.num_threads()
        except psutil.AccessDenied, psutil.NoSuchProcess:
            pass

    def __repr__(self):
        return "<Threads %i>" % self.threads

    def __iter__(self):
        yield "threads", self.threads


class MemoryCount(object):
    key = "memory"

    def __init__(self):
        self.memory = dict()
        self._rss = 0

    def count(self, p):
        try:
            for m in p.memory_maps(grouped=True):
                if m.path not in self.memory:
                    if m.path[0] == '/':
                        self.memory[m.path] = m
                if m.path[0] != '/':
                    self._rss += m.rss
        except psutil.AccessDenied, psutil.NoSuchProcess:
            pass

    @property
    def rss(self):
        return self._rss + sum(m.rss for m in self.memory.values())

    @property
    def libs(self):
        return len(self.memory)

    def __repr__(self):
        return "<Memory %i (%i)>" % (self.rss, self.libs)

    def __iter__(self):
        yield "rss", self.rss


class CPUCount(object):
    key = "cpu"

    def __init__(self):
        self.percent = 0.0

    def count(self, p):
        try:
            self.percent += p.cpu_percent()
        except psutil.AccessDenied, psutil.NoSuchProcess:
            pass

    def __repr__(self):
        return "<CPU %f>" % self.percent

    def __iter__(self):
        yield "percent", self.percent


class FdCount(object):
    key = "fd"

    def __init__(self):
        self.fd = 0

    def count(self, p):
        try:
            self.fd += p.num_fds()
        except psutil.AccessDenied, psutil.NoSuchProcess:
            pass

    def __repr__(self):
        return "<Fd %i>" % self.fd

    def __iter__(self):
        yield "count", self.fd


class ConnectionCount(object):
    key = "connection"

    def __init__(self):
        self.unix = 0
        self.inet = 0

    def count(self, p):
        try:
            self.inet += len(p.connections('inet'))
            self.unix += len(p.connections('unix'))
        except psutil.AccessDenied, psutil.NoSuchProcess:
            pass

    def __repr__(self):
        return "<Connection %i %i>" % (self.inet, self.unix)

    def __iter__(self):
        yield "inet", self.inet
        yield "unix", self.unix


class Stats(object):
    "Stats object count things."

    def __init__(self, *users):
        self.users = users

    def the_procs(self):
        "Iter over targeted process."
        for p in psutil.process_iter():
            try:
                username = p.username()
                if username in self.users:
                    yield p
            except psutil.AccessDenied, psutil.NoSuchProcess:
                pass

    def poll(self, interval):
        "Wait and ftech values from counters."
        time.sleep(interval)
        stats = dict()
        for user in self.users:
            stats[user] = [ThreadCount(), IOCount(), MemoryCount(), CPUCount(),
                           FdCount()]  # , ConnectionCount()]
        for p in self.the_procs():
            for c in stats[p.username()]:
                c.count(p)
        return stats

    def loop(self, interval=1):
        "Event loop."
        try:
            delta = 0
            while True:
                stats = self.poll(delta)
                yield stats
                delta = interval
        except (KeyboardInterrupt, SystemExit):
            pass


if __name__ == '__main__':
    import sys
    import socket
    import os
    from cStringIO import StringIO

    from graphite import GraphiteStore

    try:
        os.nice(-20)
    except:
        pass
    hostname = socket.gethostname()
    if sys.argv[1] == "-":
        graphite = None
        hz = 5
    else:
        graphite = GraphiteStore(host=sys.argv[1])
        hz = 60

    s = Stats(*sys.argv[2:])
    for top in s.loop(hz):
        ts = time.time()
        buff = StringIO()
        for user, stats in top.items():
            for stat in stats:
                for k, v in stat:
                    buff.write("servers.%s.mtop.%s.%s.%s %f %i\n" % (hostname,
                                                                     user,
                                                                     stat.key,
                                                                     k,
                                                                     float(v),
                                                                     ts))
        buff.seek(0)
        #try:
        if graphite:
            graphite._write_metric(buff.read())
            graphite.close()
        else:
            print buff.read()
        #except:
            #graphite.logger.exception("Failed to write out the metrics!")
        #print ".",
