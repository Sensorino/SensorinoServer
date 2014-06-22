#!/usr/bin/python
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

coreEngine = coreEngine.Core()


class RestSensorinoList(restful.Resource):
    """ Handle sensorinos list and creation"""
    def get(self):
        sensorinos=[]
        for s in coreEngine.getSensorinos():
            sensorinos.append(s.toData())
        return sensorinos

    def post(self):
        rparse = reqparse.RequestParser()   
        rparse.add_argument('name', type=str, required=True, help="your sensorino needs a name", location="json")
        rparse.add_argument('address', type=str, required=True, help="your sensorino needs a name", location="json")
        rparse.add_argument('description', type=str, required=True, help="Please give a brief description for your sensorino", location="json")
        args = rparse.parse_args()
        try:
            sens=sensorino.Sensorino( args['name'],  args['address'], args['description'])
            coreEngine.addSensorino(sens)
            print "let's save sensorino" 
            sens.save()
            return sens.address
        except Exception as e:
            return e.message, 500


class RestSensorino(restful.Resource):
    """ Handle sensorino details, update and delete"""
    def get(self, address):
        try:
            sens=coreEngine.findSensorino(saddress=address)
            return sens.toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")

    def put(self, address):
        rparse = reqparse.RequestParser()   
        rparse.add_argument('name', type=str, required=True, help="your sensorino needs a name", location="json")
        rparse.add_argument('description', type=str, required=True, help="Please give a brief description for your sensorino", location="json")

        args = rparse.parse_args()
        try:
            sens=coreEngine.findSensorino(saddress=address)
            sens.name=args['name']
            sens.description=args['description']

            sens.save()
            return sens.toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")


    def delete(self, address):
        return coreEngine.delSensorino(address)



class ServicesBySensorino(restful.Resource):
    """ List and create services inside a sensorino"""
    def get(self, address):
        services=[]
        for service in coreEngine.getServicesBySensorino(saddress=address):
            services.append(service.toData())
        return services

    def post(self, address):
        rparse = reqparse.RequestParser()
        rparse.add_argument('name', type=str, required=True, help="your service needs a name", location="json")
      #  rparse.add_argument('location', type=str, required=False, help="Where is your device ?", location="json")
        args =rparse.parse_args()
        
        try:
            service=coreEngine.createDataService( address, args['name'])
            return service.toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino "+address)



class ServiceBySensorino(restful.Resource):
    """ Handle service details, update and delete"""
    def get(self, address, serviceId):
        try:
            service=coreEngine.findSensorino(saddress=address).getService(serviceId)
            print "now transform service to data"
            print service.toData()
            return coreEngine.findSensorino(saddress=address).getService(serviceId).toData()
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")

    def delete(self, address, serviceId):
        try:
            coreEngine.deleteService(address, serviceId)
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")



class ChannelsByService(restful.Resource):
    """Handle channels list"""
    def get(self, address, serviceId):
        try:
            sensorinoId=int(address)
            return coreEngine.findSensorino(saddress=address).getService(serviceId).channels
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")

    def post(self, address, serviceId):
        rparse = reqparse.RequestParser()
        rparse.add_argument('channels', type=str, required=True, help="Need an array of dataType", location="json")
        args =rparse.parse_args()
        try: 
            sensorinoId=int(address)
            return coreEngine.findSensorino(saddress=address).getService(serviceId).setChannels(args["channels"])
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")


class Channel(restful.Resource):
    def delete(self, address, serviceId, channelId):
        try:
            coreEngine.deleteChannel(self, address, serviceId, channelId)
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")

    #def get(self, address, serviceId, channelId):
    #def put(self, address):

    def post(self, address, serviceId):
        rparse = reqparse.RequestParser()
        rparse.add_argument('data', type=str, required=True, help="are you loging data ?", location="json")
        args =rparse.parse_args()
        try: 
            coreEngine.publish(address, serviceId, channelId,  args['data'])
        except SensorinoNotFoundError:
            abort(404, message="no such sensorino")
        except ServiceNotFoundError:
            abort(404, message="no such service")

      


api.add_resource(RestSensorinoList, '/sensorinos')
api.add_resource(RestSensorino, '/sensorinos/<string:address>')
api.add_resource(ServicesBySensorino, '/sensorinos/<string:address>/services')
api.add_resource(ServiceBySensorino, '/sensorinos/<string:address>/services/<int:serviceId>')
api.add_resource(ChannelsByService, '/sensorinos/<string:address>/services/<int:serviceId>/channels')
api.add_resource(Channel, '/sensorinos/<string:address>/services/<int:serviceId>/channels/<int:channelId>')
#api.add_resource(PublishDataServiceByChannel, '/sensorinos/<string:address>/services/<int:serviceId>/channel/<int:channelId>/data')



if __name__ == '__main__':
    print("sensorino server m0.1")
    coreEngine.start()
    print "engine started"
    app.config['PROPAGATE_EXCEPTIONS'] = True

    print("launch app on local loop, you should proxy/forward port on "+common.Config.getRestServer())
    app.run(debug=True)
    print "app running"


