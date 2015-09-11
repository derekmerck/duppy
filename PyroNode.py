# Implements a simple Pyro4 network with data brokers, sinks, and sources

import logging
import Pyro4
import numpy as np
import time
import threading


class PyroNode(object):

    # Shared deamon object
    daemon = Pyro4.Daemon()

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
        uri = PyroNode.daemon.register(self)
        ns = Pyro4.locateNS()
        ns.register(self.pn_id, uri)
        self._broker = None
        self.broker = kwargs.get('broker')
        self.update_funcs = []
        self.update_freq = kwargs.get('update_freq', 1)
        # Dictionary for storing data streams
        self.pn_data = {}

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
        value = update_func()
        logging.debug('PUT {0}:{1}'.format(channel, value))
        broker.pn_put(value, channel)

    @classmethod
    def get_from_channel(cls, update_func, *args, **kwargs):
        channel = kwargs.get('channel')
        broker = kwargs.get('broker')
        value = broker.pn_get(channel)
        logging.debug('GET {0}:{1}'.format(channel, value))
        if update_func:
            update_func(value)

    def update(self, update_func=None, **kwargs):
        raise NotImplementedError

    def run(self):
        def update_loop():
            secs = 1/self.update_freq
            while 1:
                time.sleep(secs)
                for update in self.update_funcs:
                    update[0](update[1], *update[2], **update[3])
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_pyronode()


