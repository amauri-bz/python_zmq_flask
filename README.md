# python_zmq_flask
A ZMQ PUB/SUB topology to illustrate a distributed system in which we can add sensor devices without impact in other modules.

The HTML interface is implemented by a Flask code that uses the Interface class to request information by the ZMQ REQ/REP messages 
to a Controller module that publishes a PUB/SUB message to update the DB module with the new Sensors information.
Every sensor sends the information to the DB module that summarises and publishes the new data to the Controller module.

The final information is displayed on a web page table.
```
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
```
