
import pymongo
import os
import pandas as pd


import pymongo 
ip = "localhost"
 
class mongoDbDac:
    connection_config = {
        'ip'  : 'localhost',
        'port': '27017'
        }
    
    
    def __init__(self):
        pass
    
    
    def get_connection(self):
        connection = "mongodb://" + self.connection_config['ip'] + ":"+ self.connection_config['port']+"/&socketTimeoutMS=360000"
        if 'MONGODB_HOST' in os.environ:
            connection =  'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOST'] +  '/service_now&socketTimeoutMS=360000'        
        return pymongo.MongoClient(connection)
    
    
    def get_data(self, database, collection, query, limit = 0):
        db_client = self.get_connection()
        db_database = db_client[database]
        db_collection = db_database[collection]
        
        query_obj = db_collection.find(query)
        
        if(limit > 0):
            query_obj.limit(limit)
        
        return query_obj
    
    def get_ticket_data(self, limit = 0):
        
        
        mongo_query = { "cause" : { "$ne" : "404"},
                      "$and": [
                           {"description" : { "$ne" : ""}},
        #                    {"predictions" : {"$exists" : False }}
                           
                           
                           ]}
                        #mongodb
    
    
        incident_data = pd.DataFrame.from_records( self.get_data('service_now', 'incidents_ewm_full', mongo_query, limit) )
        incident_data = incident_data.fillna(' ')
        incident_data = incident_data.reset_index(drop=True)
        incident_data['_ticket_number'] = incident_data['number']
        incident_data = incident_data.set_index('_ticket_number')
        return incident_data
    
    def update_ticket(self):
        pass

test = mongoDbDac()
test_data =  test.get_ticket_data()