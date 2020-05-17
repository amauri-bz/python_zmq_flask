#!/usr/bin/env python
# encoding: utf-8

import zmq
import time
import os
import multiprocessing

'''
A ZMQ PUB/SUB topology to illustrate a distributed system in which we can add sensor devices without impact in other modules.

The HTML interface is implemented by a Flask code that uses the Interface class to request information by the ZMQ REQ/REP messages 
to a Controller module that publishes a PUB/SUB message to update the DB module with the new Sensors information.
Every sensor sends the information to the DB module that summarises and publishes the new data to the Controller module.

The final information is displayed on a web page table.

+------+       +------+   REQ   +------+
|      |  POST |      +-------->+      |SUB
| HTML +<----->+ INTF |         | CTRL +<--------------+
|      |       |      +<--------+      |               |
+------+       +------+   REP   +------+               |
                               PUB|  |PUB              |
                                  |  |                 |
                        SUBv------+  +------v SUB      |
                     +------+             +------+     |
                     |      |             |      |     |
                     |SENSOR|             |SENSOR|     |
                     |      |             |      |     |
                     +------+             +------+     |
                         |PUB                |PUB      |
                         |                   |         |
                         |     +-------+     |         |
                         +---->+       +<----+         |
                            SUB|  DB   |SUB            |
                               |       |               |
                               +-------+               |
                                PUB|                   |
                                   +-------------------+
'''


class Controler(multiprocessing.Process):
    def __init__(self, name, in_addr, out_addr, intf_address):
        super(Controler, self).__init__()
        self.name = str(name)
        self.in_socket_add = in_addr
        self.out_socket_add = out_addr
        self.rsocket_add = intf_address

    def init_zmq(self):
        self.context = zmq.Context()
        self.in_socket = self.context.socket(zmq.SUB)
        self.in_socket.connect("tcp://127.0.0.1:%s" % self.in_socket_add)
        self.in_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.out_socket = self.context.socket(zmq.PUB)
        self.out_socket.bind("tcp://127.0.0.1:%s" % self.out_socket_add)
        self.poller = zmq.Poller()
        self.poller.register(self.in_socket, zmq.POLLIN)

        self.rsocket = self.context.socket(zmq.REP)
        self.rsocket.bind("tcp://127.0.0.1:%s" % self.rsocket_add)
        self.poller.register(self.rsocket, zmq.POLLIN)

    def run(self):
        self.init_zmq()

        print ("Component: %s %d" % (self.name, os.getpid()))

        while True:
            socks = dict(self.poller.poll())
            if self.in_socket in socks and socks[self.in_socket] == zmq.POLLIN:
                msg = self.in_socket.recv_json()
                if msg['command'] == "GET":
                    print ("Controler: command[%s],type[%s], sensor[%s], value[%s], ret[%s]" 
                        %(msg['command'], msg['type'], msg['name'], msg['value'], msg[ 'ret']))
                    self.rsocket.send_json(msg)
            elif self.rsocket in socks and socks[self.rsocket] == zmq.POLLIN:
                msg = self.rsocket.recv_json()
                if msg['command'] == "INFO":
                    print("Ctrl sending")
                    self.out_socket.send_json({'command': "GET"})

class Sensor(multiprocessing.Process):
    def __init__(self, name, in_addr, out_addr):
        super(Sensor, self).__init__()
        self.name = str(name)
        self.in_socket_add = in_addr
        self.out_socket_add = out_addr

    def init_zmq(self):
        self.context = zmq.Context()
        self.in_socket = self.context.socket(zmq.SUB)
        self.in_socket.connect("tcp://127.0.0.1:%s" % self.in_socket_add)
        self.in_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.out_socket = self.context.socket(zmq.PUB)
        self.out_socket.connect("tcp://127.0.0.1:%s" % self.out_socket_add)
        self.poller = zmq.Poller()
        self.poller.register(self.in_socket, zmq.POLLIN)

    def run(self):
        self.init_zmq()

        print ("Component: %s %d" % (self.name, os.getpid()))

        while True:
            socks = dict(self.poller.poll())
            if self.in_socket in socks and socks[self.in_socket] == zmq.POLLIN:
                rec_command = self.in_socket.recv_json()
                print ("Sensor %s %d: msg received" % (self.name, os.getpid()))
                send_command  = {}
                send_command['type'] = 33
                send_command['name'] = self.name
                
                if(rec_command['command'] == "GET"):
                    send_command['command'] = "GET"
                    send_command['value'] = 11
                    send_command[ 'ret'] = True
                else:
                    print ("ERROR")
                    send_command[ 'ret'] = False
                print ("Sensor %s: sending msg"  % self.name)
                self.out_socket.send_json(send_command)


class Database(multiprocessing.Process):
    def __init__(self, name, in_addr, out_addr):
        super(Database, self).__init__()
        self.name = str(name)
        self.in_socket_add = in_addr
        self.out_socket_add = out_addr
        self.db = {}

    def init_zmq(self):
        self.context = zmq.Context()
        self.in_socket = self.context.socket(zmq.SUB)
        self.in_socket.bind("tcp://127.0.0.1:%s" % self.in_socket_add)
        self.in_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.out_socket = self.context.socket(zmq.PUB)
        self.out_socket.bind("tcp://127.0.0.1:%s" % self.out_socket_add)
        self.poller = zmq.Poller()
        self.poller.register(self.in_socket, zmq.POLLIN)

    def db_save(self, msg):
        self.db[msg['name']] = msg
        return len(self.db.keys())

    def run(self):
        self.init_zmq()

        print ("Component: %s %d" % (self.name, os.getpid()))

        while True:
            socks = dict(self.poller.poll())
            if self.in_socket in socks and socks[self.in_socket] == zmq.POLLIN:
                msg = self.in_socket.recv_json()
                print("DB recieved %s"%(msg))
                num = self.db_save(msg)

                #Only one sensor is supported at this moment
                if num == 1:
                    self.out_socket.send_json(msg)
                else:
                    self.out_socket.send_json({"command" : "END"})
                print("DB sending")

"""
REQ/REP interface to access information from the ZMQ topology
"""
class Interface(object):
    def __init__(self, name, out_addr):
        super(Interface, self).__init__()
        self.name = str(name)
        self.out_socket_add = out_addr

    def init_zmq(self):
        self.context = zmq.Context()
        self.out_socket = self.context.socket(zmq.REQ)
        self.out_socket.connect("tcp://127.0.0.1:%s" % self.out_socket_add)

    def run(self):
        self.init_zmq()
        self.out_socket.send_json({'command': "INFO"})
        msg = self.out_socket.recv_json()
        self.out_socket.close()
        print("Interface recieved msg: %s", msg)
        return msg

"""
Using the multiprocessing library to simulating the ZMQ PUB/SUB topology.
"""
def ZmQTest():
    try:
        db1 = Database('db', "5553", "5551")
        db1.start()
        s1 = Sensor('s1', "5552", "5553")
        s1.start()
        crtl1 = Controler('ctrl', "5551", "5552", "5555")
        crtl1.start()

        db1.join()
        s1.join()
        crtl1.join()
    except:
        db1.terminate()
        s1.terminate()
        crtl1.terminate()

if __name__ == "__main__":
    ZmQTest()