import os
from joblib      import load
import pandas as pd
import numpy as np
from scipy.sparse import coo_matrix, hstack
## Dependencies
import re
tech_token_buffer = {}

class predictor:
    def predict(self,ticket_data,mongo_ip):
        location = os.path.dirname(os.path.abspath(__file__))
        model_path = location+'/../../../ticket_analyzer/models/ticket_vectorizer.joblib'
        if(os.path.exists(model_path)):
            ticket_vectorizer = load(model_path)
        else: 
            return 'ticket_vectorizer'

        model_path =  location+'/../../../ticket_analyzer/models/l2_model.joblib'
        if(os.path.exists(model_path)):
            ticket_classifier_l2 = load(model_path)
        else:   
            return 'l2_model'
        
        model_path =  location+'/../../../ticket_analyzer/models/l1_labeler.joblib'
        if(os.path.exists(model_path)):
            labelencoder = load(model_path)
        else:   
            return 'l1_labeler'
        
        model_path =  location + '/../../../ticket_analyzer/models/l1_onehot_encoder.joblib'
        if(os.path.exists(model_path)):
            one_hot_encoder = load(model_path)
        else:   
            return 'one_hot_encoder_l1'
        
        if('l1' not in ticket_data.keys()):
            from .l1_category import predictor as l1_predictor
            l1_predictor_obj = l1_predictor()
            ticket_data['l1'] = l1_predictor_obj.predict(ticket_data,mongo_ip)['prediction']
        ticket_data['merged_texts'] = ticket_data['short_description'] + ' ' + ticket_data['description'] + ticket_data['close_notes']
        #ticket_data['merged_texts'] = ticket_data['merged_texts'].str.replace(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", '')
        
        
        
        input_data = hstack( 
            (
                ticket_vectorizer.transform([ticket_data['merged_texts']]),
                one_hot_encoder.transform(labelencoder.transform([ticket_data['l1']]).reshape(-1,1))
            )
        )
        prediction = ticket_classifier_l2.predict(input_data)
        print( ticket_classifier_l2.predict_proba(input_data))
        print( ticket_classifier_l2.classes_)
        print( ticket_classifier_l2.class_count_)
        return { 'prediction_type' : 'l1_category', 'prediction' : prediction[0] }
    