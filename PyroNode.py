# Implements a simple Pyro4 network with data brokers, sinks, and sources

import logging
# logging.basicConfig()  # or your own sophisticated setup
# logging.getLogger("Pyro4").setLevel(logging.DEBUG)
# logging.getLogger("Pyro4.core").setLevel(logging.DEBUG)
# import os
import Pyro4
import numpy as np
import time
import threading

# Doesn't like this argument on Windows
#Pyro4.config.SOCK_REUSE = True

# Not a good idea to use this on an isolated subnet
def get_public_ip_addr():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip_addr = s.getsockname()[0]
    s.close()
    return ip_addr


# This only works if hostnames resolve (shared /etc/hosts or lan router)
def get_host_name():
    import platform
    # host = os.uname()[1]
    host = platform.uname()[1]
    if host.endswith('.local'):
        # Get rid of OSX ".local" domain
        host = host[:-6]
    return host


class PyroNode(object):

    # Shared deamon object
    host = get_public_ip_addr()
    daemon = Pyro4.Daemon(host=host)

    @classmethod
    def get_proxy(cls, node):
        if isinstance(node, PyroNode):
            return node
        elif isinstance(node, basestring):
            return Pyro4.Proxy("PYRONAME:" + node)
        else:
            return None

    def __init__(self, **kwargs):
        self.pn_id = kwargs.get('pn_id')
        # self._pn_status = 'init'
        self.logger = logging.getLogger(self.pn_id)
        self.logger.debug('Setting up {0}@{1}'.format(self.pn_id, PyroNode.host))
        uri = PyroNode.daemon.register(self)
        ns = Pyro4.locateNS()
        ns.register(self.pn_id, uri)
        self._broker = None
        self.broker = kwargs.get('broker')
        self.update_funcs = []
        self.update_freq = kwargs.get('update_freq', 1000.)
        # Dictionary for storing data streams
        self.pn_data = {}
        # Do not need a lock on pn_data access b/c only the owner writes to it
        # self.lock = threading.Lock()

    @property
    def update_interval(self):
        return 1./self.update_freq

    @update_interval.setter
    def update_interval(self, value):
        self.update_freq = 1./value

    @property
    def broker(self):
        return self._broker

    @broker.setter
    def broker(self, _broker):
        self._broker = PyroNode.get_proxy(_broker)

    def pn_get(self, channel):
        return self.pn_data.get(channel)

    def pn_put(self, value, channel):
        self.pn_data[channel] = value

    def add_update_func(self, type, update_func, *args, **kwargs):
        kwargs.update({
            'broker': self.broker
            })
        self.update_funcs.append(
            [type, update_func, args, kwargs]
        )

    @classmethod
    def put_in_channel(cls, update_func, *args, **kwargs):
        channel = kwargs.get('channel')
        broker = kwargs.get('broker')
        value = update_func(*args)
        #logging.debug('PUT {0}:{1}'.format(channel, value))
        if value:
            broker.pn_put(value, channel)

    @classmethod
    def get_from_channel(cls, update_func, *args, **kwargs):
        channel = kwargs.get('channel')
        broker = kwargs.get('broker')
        value = broker.pn_get(channel)
        #logging.debug('GET {0}:{1}'.format(channel, value))
        if value and update_func:
            update_func(value, *args)

    def update(self, update_func=None, **kwargs):
        raise NotImplementedError

    def run(self):
        def update_loop():
            interval = 1/self.update_freq
            while 1:
                time_begin = time.time()
                for update in self.update_funcs:
                    update[0](update[1], *update[2], **update[3])
                time_end = time.time()
                time_elapsed = time_end - time_begin
                if interval - time_elapsed > 0:
                    time.sleep(interval - time_elapsed)
        thread = threading.Thread(target=update_loop)
        thread.setDaemon(True)
        thread.start()


def test_pyronode():

    broker = PyroNode(pn_id='test_broker')
    broker.run()

    source1 = PyroNode(pn_id='test_source1', broker='test_broker')
    source1.add_update_func(PyroNode.put_in_channel, np.random.rand, channel=(source1.pn_id, 'test-1'))
    source1.add_update_func(PyroNode.put_in_channel, np.random.rand, channel=(source1.pn_id, 'test-2'))
    source1.run()

    source2 = PyroNode(pn_id='test_source2', broker='test_broker')
    source2.add_update_func(PyroNode.put_in_channel, np.random.rand, channel=(source2.pn_id, 'test-1'))
    source2.run()

    sink1 = PyroNode(pn_id='test_sink1', broker='test_broker')
    sink1.add_update_func(PyroNode.get_from_channel, None, channel=(source1.pn_id, 'test-1'))
    sink1.run()

    logging.debug("Threads running.")

    PyroNode.daemon.requestLoop()


def test_multihost_pyronode():

    ns = Pyro4.locateNS()
    uri0 = ns.lookup('control0')
    uri1 = ns.lookup('control1')

    c0 = Pyro4.Proxy(uri0)
    c1 = Pyro4.Proxy(uri1)

    logging.debug(c0.broker)
    logging.debug(c1.broker)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_multihost_pyronode()



