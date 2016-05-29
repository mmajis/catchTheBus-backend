#!/usr/bin/python

import cherrypy
import json
from cherrypy.lib.httputil import parse_query_string


class Root(object):
    @cherrypy.expose
    def index(self):
        params = parse_query_string(cherrypy.request.query_string)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        with open('connection.json', 'r') as datafile:
            data = json.load(datafile)
            return json.dumps(data)

class SetCurrentLocation(object):
    @cherrypy.expose
    def index(self):
        params = parse_query_string(cherrypy.request.query_string)

class SetDestAndArrival(object):
    @cherrypy.expose
    def index(self):
        params = parse_query_string(cherrypy.request.query_string)

if __name__ == '__main__':
    cherrypy.tree.mount(Root(), '/')
    cherrypy.tree.mount(SetDestAndArrival(), '/set')
    cherrypy.tree.mount(SetDestAndArrival(), '/set')
    cherrypy.server.socket_host = '0.0.0.0'
    # cherrypy.server.socket_port = 80
    cherrypy.engine.start()
    cherrypy.engine.block()
