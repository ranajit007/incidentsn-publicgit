# -*- coding: utf-8 -*-
'''
Created on Sun Sep 13 19:19:38 2020

@author: JorgeCarlosBustillos
'''
import os
from importlib import import_module
from bson.objectid import ObjectId
from flask import Flask,render_template, jsonify, make_response, request
from datetime import datetime
from uuid import uuid4
from .incidentSearch import IncidentSearch
from bson.json_util import dumps
from flask_pymongo import PyMongo
import pymongo
import traceback, asyncio

app = Flask(__name__)


app.config['MONGO_DBNAME'] = 'service_now'
app.config['MONGO_URI'] = 'mongodb://incidentUser:redhat@mongodb/service_now'

if 'MONGODB_HOST' in os.environ:
    app.config['MONGO_URI'] =  'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOST'] + '/service_now'

mongo = PyMongo(app)


@app.route('/')
def index():
    '''
    Gets the SAPUI5 application

    Returns
    -------
    SAPUI5 INDEX

    '''
    return render_template('index.html')

@app.route('/api/HeaderData')
def header_data():
    '''
    GETS THE INFORMATION USED IN THE HEADER

    Returns
    -------
    r : DICTIONARY
        user_id, last_update from selenium_config.

    '''
    config = mongo.db.config
    query = {'key' : 'selenium_config'}
    s = config.find_one(query)
    output = dumps({'user_id' : s['user_id'], 
                   'last_update' : s['last_update'].isoformat()
                   })
    r = make_response(output)
    r.mimetype = 'application/json'
    return r
  
@app.route('/api/incidents/update')
def update_incidents():
    '''
    Updates the incident list from Service now, getting the latest updates
    from 2 weeks.
    Returns
    -------
    JSON
        JSON Formatted Response.

    '''
    selenium_config = _get_selenium_config()
    #Instantiate incident search API
    worker = IncidentSearch(mongo_ip=app.config['MONGO_URI'],
                            user_id=selenium_config['user_id'],
                            user_pass=selenium_config['user_pass'],
                            show_browser=selenium_config['show_browser'],
                            max_login=5)
    try:
        asyncio.run(worker.new_requests())
    except:
        pass    
    _set_selenium_config(selenium_config)
    return jsonify('OK')

    

@app.route('/api/incidents_closed_count', methods=['GET'])
def get_incidents_closed_count():
    '''
    Gets the number of closed incidents
    Returns
    -------
    JSON
        JSON Formatted Response.
        incidents: integer

    '''
    query = {'close_code': {'$ne' : ''}}
    groups = request.args.get('groups')
    if groups != None:
        groups = groups.split(",")
        query["assignment_group_text"] = { "$in": groups }
    #, 'category_incident': {'$ne': 'Failure'}}
    return _get_incidents_query(query,True)

@app.route('/api/incidents_closed', methods=['GET'])
def get_incidents_closed():
    '''
    Gets an array of closed incidents
    Returns
    -------
    JSON
        JSON Formatted Response.
        Incidents: array

    '''
    query = {'close_code': {'$ne' : ''}}
    groups = request.args.get('groups')
    if groups != None:
        groups = groups.split(",")
        query["assignment_group_text"] = { "$in": groups }
    return _get_incidents_query(query)

@app.route('/api/incidents_pending_count', methods=['GET'])
def get_incidents_pending_count():
    '''
    Gets the number of open incidents
    Returns
    -------
    JSON
        JSON Formatted Response.
        incidents: integer

    '''
    query = {'close_code': {'$eq' : ''}}
    groups = request.args.get('groups')
    if groups != None:
        groups = groups.split(",")
        query["assignment_group_text"] = { "$in": groups }
    return _get_incidents_query(query,True)

@app.route('/api/incidents_pending', methods=['GET'])
def get_incidents_pending():
    '''
    Gets an array of open incidents
    Returns
    -------
    JSON
        JSON Formatted Response.
        Incidents: array

    '''    
    query = {'close_code': {'$eq' : ''}}
    groups = request.args.get('groups')
    if groups != None:
        groups = groups.split(",")
        query["assignment_group_text"] = { "$in": groups }
    return _get_incidents_query(query)

@app.route('/api/get_all_worknotes', methods=['GET'])
def get_all_worknotes():
    selenium_config = _get_selenium_config()
    worker = IncidentSearch(mongo_ip=app.config['MONGO_URI'],
                    user_id=selenium_config['user_id'],
                    user_pass=selenium_config['user_pass'],
                    show_browser=selenium_config['show_browser'],
                    max_login=5)
    try:
        asyncio.run(worker.update_all_work_notes())                   
    except:
        pass
    return 'Process finished'

@app.route('/api/get_all_categories', methods=['GET'])
def get_all_categories():
    selenium_config = _get_selenium_config()
    worker = IncidentSearch(mongo_ip=app.config['MONGO_URI'],
                    user_id=selenium_config['user_id'],
                    user_pass=selenium_config['user_pass'],
                    show_browser=selenium_config['show_browser'],
                    max_login=5)
    try:
        asyncio.run(worker.update_all_category())
    except:
        pass    
    return 'Process finished'

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    query = {}
    return _get_incidents_query(query)

@app.route('/api/review/<number>', methods=['POST'])
def review_on(number):
    query = {'number' : number}
    incident = mongo.db.incidents_ewm_full
    s = incident.find_one(query)
    if not s:
        return jsonify('Not found')
    if s:
        if 'predictions' not in s:
            s['predictions'] = []
    feedback = request.form.get('feedback') == 'true'
    uuid = request.form.get('uuid')
    for prediction in s['predictions']:
        if prediction['uuid'] == uuid:
            prediction['feedback'] = feedback
            prediction['feedback_date'] = datetime.now().isoformat()
    newConfig = { '$set': s}
    incident.update_one(query, newConfig)
    return jsonify('OK')
    

@app.route('/api/incidents/<number>', methods=['GET'])
def get_incident(number):
    incident = mongo.db.incidents_ewm_full
    s = incident.find_one({'number' : number})
    if s:
        if 'predictions' not in s:
            s['predictions'] = []
        if 'close_notes' not in s:
            s['close_notes'] = ''
        output = s
    else:
        output = 'Not found'
    output["incident_url"] = 'https://nestle.service-now.com/incident.do?sysparm_query=number=' + str(output["number"])
    output = dumps(output)
    r = make_response(output)
    r.mimetype = 'application/json'
    return r

@app.route('/api/new_note', methods=['POST'])
def new_note():
    content =  request.get_json()
    if 'notes' not in content:
        return 'Error: notes node not present', 400
    selenium_config = _get_selenium_config()
    worker = IncidentSearch(mongo_ip=app.config['MONGO_URI'],
                    user_id=selenium_config['user_id'],
                    user_pass=selenium_config['user_pass'],
                    show_browser=selenium_config['show_browser'],
                    max_login=5)
    ret = []
    for note in content['notes']:
        try:
            res =  asyncio.run(worker.new_worknote(note['number'],note['note'],note['uuid']))          
            note['status'] = res
            note['msg'] = 'Note added.'
        except Exception as e:
            note['status'] = 500
            note['msg'] = str(e)
        ret.append(note)
    return jsonify(ret)

@app.route('/api/CRUD/ProposedProcedure', methods=['POST'])
def crud_ProposedProcedure():
    content =  request.get_json()
    ret = {
        'delete': 0,
        'update': 0,
        'create': 0
    }
    if 'delete' in content:
        ret['delete'] = _crud_ProposedProcedure_delete(content['delete'])

    if 'update' in content:
        ret['update'] = _crud_ProposedProcedure_update(content['update'])

    if 'create' in content:
        ret['create'] = _crud_ProposedProcedure_create(content['create'])

    return jsonify(ret)

@app.route('/api/predictions_conf')
def predictions_conf():
    output = dumps(_get_predictions_config())
    r = make_response(output)
    r.mimetype = 'application/json'    
    return r

@app.route('/api/delete_predictions/<number>')
def delete_predictions(number):
    print(number)
    incident = mongo.db.incidents_ewm_full
    data = incident.find_one({'number' : number})
    newConfig = { '$set': {'predictions': []} }
    updatedb = mongo.db.incidents_ewm_full.update_one({'_id':data['_id']}, newConfig)
    r = make_response(dumps(updatedb.acknowledged))
    r.mimetype = 'application/json'    
    return r

@app.route('/api/get_predictions/<number>')
def get_predictions(number):
    print(number)
    predictions = _get_predictions_config()
    incident = mongo.db.incidents_ewm_full
    data = incident.find_one({'number' : number})
    new_uuid = str(uuid4())
    if 'predictions' not in data:
        data['predictions'] = []     
    prediction = {
        'uuid': new_uuid,
        'date': datetime.now().isoformat(),
        'feedback': '',
        'feedback_date': None,
        'feedback_sent': False
    }   
    for prediction_conf in predictions:
        try:
            prediction[prediction_conf['key']] = _get_prediction(data,prediction_conf,new_uuid)
        except Exception as e:
            print(str(e))
            print('Im dying :( ')
            traceback.print_exc()

            continue
    data["predictions"].append(prediction)
    newConfig = { '$set': {'predictions': data['predictions']} }
    updatedb = mongo.db.incidents_ewm_full.update_one({'_id':data['_id']}, newConfig)
    output = dumps({"_id": data['_id'],'update': updatedb.acknowledged,'number':number})
    r = make_response(output)
    r.mimetype = 'application/json'    
    return r

@app.route('/api/ProposedProcedure')
def get_proposed_procedure():
    output = dumps(_get_proposed_procedure())
    r = make_response(output)
    r.mimetype = 'application/json'    
    return r
    
def _get_prediction(data,prediction_conf,new_uuid):
    ClassPredictor = getattr(import_module('flaskr.predictors.' + prediction_conf['key']), 'predictor')
    _instance = ClassPredictor()
    res = _instance.predict(data,app.config['MONGO_URI'])
    print(res)
    if 'prediction' not in res:
        res['prediction'] = ""
    return res['prediction']

def _get_incidents_query(query, get_count=False):
    output = []
    incidents = mongo.db.incidents_ewm_full    
    documents = incidents.find(query,{'number': 1, 
                              'short_description':1,
                              'opened_at':1,
                              'predictions': 1,
                              'category_incident': 1,
                              'assignment_group_text': 1,
                              'close_code': 1})
    if get_count == True:
        output = { 'incidents': documents.count() }
        r = make_response(output)
        r.mimetype = 'application/json'
        return r
    for s in documents:
        if 'predictions' not in s:
            s['predictions'] = []
        if 'category_incident' not in s:
            s['category_incident'] = ''
        if 'assignment_group_text' not in s:
            s['assignment_group_text'] = ''
        predictions_len = len(s['predictions'])
        output.append({'number' : s['number'], 
                        'assignment_group_text': s['assignment_group_text'],
                        'short_description' : s['short_description'],
                        'opened_at' : s['opened_at'],
                        'close_code': s['close_code'],
                        'category_incident': s['category_incident'],
                        'predictions':  predictions_len
                       })
    output = dumps({ 'Incidents' : output})
    r = make_response(output)
    r.mimetype = 'application/json'
    return r

def _set_selenium_config(selenium_config):
    selenium_config['last_update'] = datetime.now()
    newConfig = { '$set': selenium_config }
    query = {'key' : 'selenium_config'}
    config = mongo.db.config
    config.update_one(query, newConfig)

def _get_selenium_config():
    config = mongo.db.config
    query = {'key' : 'selenium_config'}
    selenium_config = config.find_one(query)
    return selenium_config

def _get_predictions_config():
    config = mongo.db.config
    query = {'type' : 'predictions_config', 'active': True}
    predictions_config = config.find(query).sort('order',pymongo.ASCENDING)
    return predictions_config

def _get_proposed_procedure():
    result = []
    collection = mongo.db.ProposedProcedure
    documents = collection.find()
    for document in documents:
        result.append({
            '_id': document['_id'],
            'l3': document['l3'],            
            'solution': document['solution'],
            'active': document['active'],
            'mod': False
        })
    return result

def _crud_ProposedProcedure_delete(array):
    if len(array) == 0:
        return
    delete_array = []
    for item in array:
        delete_array.append(ObjectId(item['_id']['$oid']))
    delete_filter = {
        "_id": { "$in":  delete_array }
    }
    collection = mongo.db.ProposedProcedure    
    res = collection.delete_many(delete_filter)
    return res.deleted_count

def _crud_ProposedProcedure_update(array):
    if len(array) == 0:
        return    
    collection = mongo.db.ProposedProcedure
    count = 0
    for item in array:
        query_filter = { "_id": ObjectId(item['_id']['$oid']) }
        del item['_id']
        new_values = { '$set': item}
        res = collection.update_one(query_filter,new_values)
        count = count + res.matched_count  
    return count

def _crud_ProposedProcedure_create(array):    
    if len(array) == 0:
        return    
    collection = mongo.db.ProposedProcedure
    res = collection.insert_many(array)
    return len(res.inserted_ids)
