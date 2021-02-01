import os
import pandas as pd
import pymongo
class predictor:
    def predict(self,ticket_data,mongo_ip):
        #database instance
        db_client = pymongo.MongoClient(mongo_ip)
        db_name = db_client["service_now"]
        db_col = db_name["ProposedProcedure"]    
        #check if l3 is missing:
        if 'l3' not in ticket_data.keys():
            from .l3_category import predictor as l3_predictor
            l3_predictor_obj = l3_predictor()
            ticket_data['l3'] = l3_predictor_obj.predict(ticket_data,mongo_ip)['prediction']            
        #query prepare
        db_query = {'l3': ticket_data['l3'], 'active': True }
        db_view = {'solution': 1 }            
        document = db_col.find_one(db_query,db_view)
        #Check if found:
        if document != None:
            return { 'prediction_type' : 'resolution', 'prediction' : str(document['solution'])}
        else:
            return { 'prediction_type' : 'resolution', 'prediction' : "Couldn't propose a resolution" }    
    
#test = predictor()
#test_df = {'u_feature_set':'', 'description':'ewm pgi warehouse', 'short_description':'','close_notes':''}
#print(test.predict(test_df))