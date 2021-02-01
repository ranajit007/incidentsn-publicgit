import os
from joblib      import load
from scipy.sparse import hstack

tech_token_buffer = {}

class predictor:
    def predict(self,ticket_data,mongo_ip):
        location = os.path.dirname(os.path.abspath(__file__))
        model_path = location+'/../../../ticket_analyzer/models/ticket_vectorizer.joblib'
        if(os.path.exists(model_path)):
            ticket_vectorizer = load(model_path)
        else: 
            return 'ticket_vectorizer'

        model_path =  location+'/../../../ticket_analyzer/models/l3_model.joblib'
        if(os.path.exists(model_path)):
            ticket_classifier_l3 = load(model_path)
        else:   
            return 'l3_model'
        
        model_path =  location+'/../../../ticket_analyzer/models/l1_labeler.joblib'
        if(os.path.exists(model_path)):
            labelencoder_l1 = load(model_path)
        else:   
            return 'l1_labeler'
        
        model_path =  location + '/../../../ticket_analyzer/models/l1_onehot_encoder.joblib'
        if(os.path.exists(model_path)):
            one_hot_encoder_l1 = load(model_path)
        else:   
            return 'one_hot_encoder_l1'

        model_path =  location+'/../../../ticket_analyzer/models/l2_labeler.joblib'
        if(os.path.exists(model_path)):
            labelencoder_l2 = load(model_path)
        else:   
            return 'l2_labeler'
        
        model_path =  location + '/../../../ticket_analyzer/models/l2_onehot_encoder.joblib'
        if(os.path.exists(model_path)):
            one_hot_encoder_l2 = load(model_path)
        else:   
            return 'one_hot_encoder_l2'
        
        if('l1' not in ticket_data.keys()):
            from .l1_category import predictor as l1_predictor
            l1_predictor_obj = l1_predictor()
            ticket_data['l1'] = l1_predictor_obj.predict(ticket_data,mongo_ip)['prediction']
            
        if('l2' not in ticket_data.keys()):
            from .l2_category import predictor as l2_predictor
            l2_predictor_obj = l2_predictor()
            ticket_data['l2'] = l2_predictor_obj.predict(ticket_data,mongo_ip)['prediction']
            
            
        ticket_data['merged_texts'] = ticket_data['short_description'] + ' ' + ticket_data['description'] + ticket_data['close_notes']
        #ticket_data['merged_texts'] = ticket_data['merged_texts'].str.replace(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", '')
        
        
        
        input_data = hstack( 
            (
                ticket_vectorizer.transform([ticket_data['merged_texts']]),
                one_hot_encoder_l1.transform(labelencoder_l1.transform([ticket_data['l1']]).reshape(-1,1)),
                one_hot_encoder_l2.transform(labelencoder_l2.transform([ticket_data['l2']]).reshape(-1,1)),
            )
        )
        prediction = ticket_classifier_l3.predict(input_data)
        
        return { 'prediction_type' : 'l3_category', 'prediction' : prediction[0] }
