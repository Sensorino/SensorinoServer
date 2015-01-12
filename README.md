Project is abandoned
====================

NOTE: this project was declared abandoned in its early development stage and is left in a non-functional state.  See https://github.com/Sensorino/sensorino-smarthome for a working Server implementation that follows a different approach.

SensorinoServer
===============

A server that gets data from Sensorinos and allows controlling them

Running
=======

Once the dependencies are satisfied (see server/INSTALL and
server/http-proxy/README.md), three basic processes are necessary for
end-to-end functionality.  Assuming the Base is connected to ttyUSB0
go to the server/ subdirectory and run:

$ ./serialGateway.py /dev/ttyUSB0

on the machine where the base is connected.  On the server (can be the
same machine or a different one) launch mosquitto (if not running
already), lighttpd and restServer.py -- the former two from the top-
level directory and the latter from withing server/:

$ mosquitto -d
$ lighttpd -f server/http-proxy/lighttpd.conf
$ cd server/
$ ./restServer.py
