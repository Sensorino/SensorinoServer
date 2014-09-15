#!/usr/bin/env python

from flask import Flask
from flask.ext import restful
from flask import json
from flask.ext.restful import reqparse, abort, Api, Resource
from flask.ext.restful.utils import cors

import threading
import logging
import time

import coreEngine
import common
import sensorino
from errors import *



app = Flask(__name__)
api = restful.Api(app)

cEngine = None

class RestSensorinoList(restful.Resource):
    """ Handle sensorinos list and creation"""
    def get(self):
        sensorinos=[]
        for s in cEngine.getSensorinos():
            sensorinos.append(s.toData())
        return sensorinos

    def post(self):
        rparse = reqparse.RequestParser()   
        rparse.add_argument('name', type=str, required=True, help="your sensorino needs a name", location="json")
        rparse.add_argument('address', type=str, required=True, help="your sensorino needs a name", location="json")
        rparse.add_argument('description', type=str, required=True, help="Please give a brief description for your sensorino", location="json")
        args = rparse.parse_args()
        try:
            return cEngine.createSensorino(args['name'],  args['address'], args['description']).address
        except Exception as e:
            return e.message, 500


class RestSensorino(restful.Resource):
    """ Handle sensorino details, update and delete"""
    def get(self, address):
        try:
            return cEngine.findSensorino(saddress=address).toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")

    def put(self, address):
        rparse = reqparse.RequestParser()   
        rparse.add_argument('name', type=str, required=True, help="your sensorino needs a name", location="json")
        rparse.add_argument('description', type=str, required=True, help="Please give a brief description for your sensorino", location="json")

        args = rparse.parse_args()
        try:
            sens=cEngine.findSensorino(saddress=address)
            sens.name=args['name']
            sens.description=args['description']

            sens.save()
            return sens.toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")


    def delete(self, address):
        return cEngine.delSensorino(address)



class ServicesBySensorino(restful.Resource):
    """ List and create services inside a sensorino"""
    def get(self, address):
        services=[]
        for service in cEngine.getServicesBySensorino(saddress=address):
            services.append(service.toData())
        return services

    def post(self, address):
        rparse = reqparse.RequestParser()
        rparse.add_argument('name', type=str, required=True, help="your service needs a name", location="json")
        rparse.add_argument('instanceId', type=str, required=True, help="What's your number babe ?", location="json")
        args =rparse.parse_args()
        
        try:
            service=cEngine.createService( address, args['name'], args['instanceId'])
            return service.toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino "+address)



class ServiceBySensorino(restful.Resource):
    """ Handle service details, update and delete"""
    def get(self, address, instanceId):
        try:
            return cEngine.findSensorino(saddress=address).getService(instanceId).toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")

    def delete(self, address, instanceId):
        try:
            cEngine.deleteService(address, instanceId)
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")



class ChannelsByService(restful.Resource):
    """Handle channels list"""
    def get(self, address, instanceId):
        try:
            sensorinoId=int(address)
            return cEngine.findSensorino(saddress=address).getService(instanceId).channels
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")

    def post(self, address, instanceId):
        rparse = reqparse.RequestParser()
        rparse.add_argument('channels', type=list, required=True, help="Need an array of dataType", location="json")
        args =rparse.parse_args()
        try: 
            sensorinoId=int(address)
            return cEngine.findSensorino(saddress=address).getService(instanceId).setChannels(args["channels"])
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")

    def put(self, address, instanceId):
        rparse = reqparse.RequestParser()
        rparse.add_argument('data', type=dict, required=True, help="are you loging data ?", location="json")
        args =rparse.parse_args()
        try: 
            cEngine.publish(address, instanceId, args['data'])
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")




class Channel(restful.Resource):
    def delete(self, address, instanceId, channelId):
        try:
            cEngine.deleteChannel(self, address, instanceId, channelId)
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")


    def post(self, address, instanceId):
        rparse = reqparse.RequestParser()
        rparse.add_argument('data', type=dict, required=True, help="are you loging data ?", location="json")
        args =rparse.parse_args()
        try: 
            cEngine.publish(address, instanceId, args['data'], channelId)
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")


class ChannelLog(restful.Resource):
    def get(self, address, instanceId, channelId):
        try:
            return cEngine.getLogs( address, instanceId, channelId)
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")
        except ChannelNotFoundError:
            abort(404, message="no such channel")

        
      


api.add_resource(RestSensorinoList, '/sensorinos')
api.add_resource(RestSensorino, '/sensorinos/<string:address>')
api.add_resource(ServicesBySensorino, '/sensorinos/<string:address>/services')
api.add_resource(ServiceBySensorino, '/sensorinos/<string:address>/services/<int:instanceId>')
api.add_resource(ChannelsByService, '/sensorinos/<string:address>/services/<int:instanceId>/channels')
api.add_resource(Channel,    '/sensorinos/<string:address>/services/<int:instanceId>/channels/<int:channelId>')
api.add_resource(ChannelLog, '/sensorinos/<string:address>/services/<int:instanceId>/channels/<int:channelId>/data')



if __name__ == '__main__':
    print("sensorino server m0.3")
    cEngine = coreEngine.Core()
    cEngine.start()
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # for some reason autoreloader is confused as fuck when using threads, have to disable it
    # http://blog.davidvassallo.me/2013/10/23/nugget-post-python-flask-framework-and-multiprocessing/
    app.run(debug=True, host=common.Config.getRestServerAddress(), port=common.Config.getRestServerPort(), use_reloader=False)
    print "app running"


