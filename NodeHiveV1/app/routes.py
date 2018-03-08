from app import app
from flask import jsonify, request
from .utils import runDiagn, ConnecterMongo

cm = ConnecterMongo()

@app.route('/nbt', methods=['POST'])
def acceptNodeHeartbeat():
    res = cm.acceptNodeHeartbeat2(request)
    return res

@app.route('/deactivate', methods=['POST'])
def deactivate():
    # res = {'rc':0}
    # cm.deactivateNode(request.json['nodeId'])
    # return jsonify(res)
    res = cm.deactivateNode(request)
    return res

@app.route('/activate', methods=['POST'])
def activate():
    res = cm.activateNode(request)
    return res

@app.route('/join', methods=['POST'])
def join():
    res = {'rc':0}

    res['nodeId'] = cm.addNode(request)

    return jsonify(res)

@app.route('/stats')
def stats():
    res = runDiagn()
    return res

@app.route('/')
@app.route('/index')
def index():
    return "Hive Home!"