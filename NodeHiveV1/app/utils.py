import psutil
import socket
from uuid import uuid4
import json
from datetime import datetime as dt


from flask import jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId


from config import MASTER_DATA_SOURCE_HOST, MASTER_DATA_SOURCE_PORT


uid = uuid4().hex

class ConnecterMongo():

    def __init__(self):
        self.client = MongoClient('mongodb://{}:{}/'.format(MASTER_DATA_SOURCE_HOST, MASTER_DATA_SOURCE_PORT))
        self.bugRepo = self.client['bug-repo']
        self.nodes = self.bugRepo['nodes']
        self.heartbeats = self.bugRepo['heartbeats']

    def addNode(self, req):
        data = validateRequest(req)
        newNode = {
            "active" : -1,
            "uid": data['uid'],
            "born": dt.utcnow().isoformat(),
            "meta": data['meta']
        }
        inRes = self.nodes.insert_one(newNode)
        return str(inRes.inserted_id)

    def activateNode(self, req):
        res = {'rc': 0}
        data = validateRequest(req)
        target_node = self.checkNode(data['nodeId'])
        if target_node['active'] == -1:
            upRes = self.nodes.update_one(
                {"_id": target_node['_id']},
                {
                    "$set": {
                        "active": 1
                    }
                }
            )
            if upRes.modified_count == 1:
                # update ok
                return jsonify(res)
        elif target_node['active'] == 1:
            # Node already active
            res['rc'] = 1
            res['rc-msg'] = 'Node already active'
            return jsonify(res)
        else:
            # Node already active
            res['rc'] = 2
            res['rc-msg'] = 'Error processing activate request'
            return jsonify(res)

    def deactivateNode(self, req):
        res = {'rc': 0}
        data = validateRequest(req)
        if 'rc' in data.keys() and data['rc'] == 1:
            res['rc'] = 2
            res['rc-msg'] = data['rc-msg']
            return jsonify(res)
        target_node = self.checkNode(data['nodeId'])

        if target_node['active'] == 1:
            upRes = self.nodes.update_one(
                {"_id": target_node['_id']},
                {
                    "$set": {
                        "active": 0
                    }
                }
            )
            if upRes.modified_count == 1:
                # update ok
                return jsonify(res)
        elif target_node['active'] in [-1, 0]:
            # Not activated
            res['rc'] = 1
            res['rc-msg'] = 'Node not active'
            return jsonify(res)

    def checkNode(self, id):
        return self.nodes.find_one({'_id': ObjectId(id)})

    def pingNode(self):
        pass

    def addHeartbeat(self, node_uid, load):
        target_node = self.checkNode(node_uid)
        if target_node['active'] == 1:
            # ok
            beat = {'tstamp': dt.utcnow().isoformat(), 'node_id': target_node['_id'], 'load': load}
            inRes = self.heartbeats.insert_one(beat)
            if inRes.inserted_id:
                return 0
        elif target_node['active'] == 0:
            # node is deactived
            return 1
        elif target_node['active'] == -1:
            # node is not been activated
            return 2



    def acceptNodeHeartbeat2(self, req):
        res = {'rc': 0}
        rjson = req.json
        try:
            data = rjson['data']
        except KeyError:
            res['rc'] = 1
            res['rc-msg'] = 'Not able to access node heartbeat data'
            return jsonify(res)

        target_node = self.checkNode(data['nodeId'])
        if target_node['active'] == 1:
            # ok
            # "nodeId": "5a92a585dcc7e31a4eff6fe6",
            if self.addHeartbeat(target_node['_id'], data['load']) == 0:
                return jsonify(res)
            else:
                res['rc'] = 4
                res['rc-msg'] = 'Heartbeat Error.'
                return jsonify(res)
        elif target_node['active'] == 0:
            # node is deactived
            # "5a92913cdcc7e313d7a9bf83"
            res['rc'] = 2
            res['rc-msg'] = 'Node is deactive'
            return jsonify(res)
        elif target_node['active'] == -1:
            # node is not been activated
            # '5a928f22dcc7e31326b84631'
            res['rc'] = 3
            res['rc-msg'] = 'Node not active'
            return jsonify(res)


def validateRequest(req):
    rjson = req.json
    try:
        data = rjson['data']
        return data
    except (KeyError, TypeError):
        return {'rc': 1, 'rc-msg': 'Not able to access request data.'}


def getIP():
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

def runDiagn():
    rc = 0
    results = {"tstamp":dt.utcnow().isoformat()}

    results["uid"] = getIP() + uid
    results["cpu_percent"] = psutil.cpu_percent()
    results["virtual_memory"] = psutil.virtual_memory()

    return json.dumps({
        "rc" : rc,
        "results": results,
        })
