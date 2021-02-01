
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 14:05:33 2020

@author: jbust
"""
import os
import re
from joblib      import load
tech_token_buffer = {}
def words_analyzer(doc):
    
    location = os.path.dirname(os.path.abspath(__file__))
    model_path = location + '/../ticket_analyzer/models/tech_word_detector.joblib'
    if(os.path.exists(model_path)):
        tech_word_detector = load(model_path)
    else:
        print('tech word detector not found')        
        return 'tech_word_detector'

    from nltk.stem import PorterStemmer
    porter = PorterStemmer()
    
    replace_map =  {
        ' ' : [ ',', '.', ':' ,';','<','>','=', '?', '[', ']', '~','\r','\n','\t','&'],
        '' : ['!','"','#',"'", '(',')', '*', '+', '$','-']
    }
    
    regex_replace_map = {
        '<abap_trx_id>' : r'[a-fA-F0-9]{24,30}',
        '<scd_idoc_number>' : r'(19|26)[0-9]{8}',
        '<gxs_reference_number>' : r'f[0-9]{10}',
        '<tm_freight_order>' : r'f200[0-9]{6}',
        '<tm_bo_number>' : r'fb000[0-9]{5}',
        '<tm_fu_create_queue>' : r'fu_create_[0-9]{9}',
        '<queue_name>' : r'xbqi[a-fA-F0-9]{16}',
        '<related_incident_number>' :  r'inc[0-9]{8}',
        '<shipment_number>' :  r'(u|t)[0-9]{9}',
        '<po_number>' : r'45[0-9]{8}',
        '<hu_id>' : r'(10178|37613)[0-9]{13}',
        '<material_id>' : r'12[0-9]{6}',
        '<inbound_delivery_id>' : r'40[0-9]{7}',
        '<tu_id>' : r'uc[0-9]{8}',
        '<odo_id>' : r'10000[0-9]{6}',
        '<erp_deliver_id>': r'88[0-9]{7}'
    }
     
    
    stop_words = [
        'the', 'in', 'to', 'if', 'is', 'be','please','pleas','and','or','by',
        'ticket','on','at','teh','de', 'hello', 'for', 'are' ,'as', 'you', 'that'
    ,'el','en','del','se','es', 'what', 'laptop', 'desktop', 'we', 'r',
    'la', 'que', 'un', 'para', 'al', 'cual', 'con','pued', 'lo' ,'', 'tablet',
    'hard', 'disk'  ]
    
    numeric_ids = []
               
    doc = doc.lower()
    
    for key in replace_map.keys():
        
        for replace_char in replace_map[key]:
            doc = doc.replace(replace_char,key)
    
    #Pattern replace
    for key in regex_replace_map.keys():
        doc = re.sub(regex_replace_map[key], ' '+key+' ', doc)
    
    processed_words = []
        
    words = doc.split(' ')
    
    for word in words:
        word = word.strip()
        word = word.lstrip('0')
        word =  porter.stem(word)
        if(len(word) < 3):
            continue
    
        if( not (  re.match(r'^[a-z]+$',word) 
                           or re.match(r'^[0-9]+$',word)) ):                
            
            if(word in tech_token_buffer):
                word_token = tech_token_buffer[word]
    
            else:
                word_token = tech_word_detector.predict([word])[0]
                tech_token_buffer[word] = word_token
            
            if(not (word_token in ['<common_word>','<abap_object_ecc>','<abap_object_ewm>','<custom_abap_object>'])):
                word = word_token
        
        if word in stop_words:
            continue
        
        if(re.match(r'^[0-9]+$',word)):
            if word not in numeric_ids:    
                numeric_ids.append(word)
            word = '<unknown_'+ str(word[:2]) +'_len_' + str(len(word)) +'_id>'
            
        
        processed_words.append(word)
    
    
    return processed_words


from flaskr.routes import app
if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0')