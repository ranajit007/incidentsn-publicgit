# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 01:19:16 2020

@author: DanielEnriqueNavaTor
"""

###### load data #######
import os
import pandas as pd
import numpy as np
from joblib      import dump, load
from DAC.mongodb import mongoDbDac



## Dependencies
import re
from sklearn.model_selection import KFold
from sklearn import svm
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from scipy.sparse import coo_matrix, hstack




def get_tech_word_detector(incident_data,retrain=False):
    model_path = 'models/tech_word_detector.joblib'
    if(os.path.exists(model_path) and not retrain):
        tech_word_detector = load(model_path)
        return tech_word_detector
    
    ##########get "normal" words #################

    normal_words = set()
    for incident in incident_data.description:
        incident = incident.lower()
        words = incident.split(' ')
        
        for word in words:
            if(re.match(r'^[a-z]+$',word)):
                normal_words.add(word)
            
            
    common_words = pd.DataFrame(list(normal_words),columns=['text'])
    common_words['token'] = '<common_word>'
    
    
    #######load technical ids ####################
    technical_ids = pd.read_csv('text_corpora/technical_names_tokens.csv')
    technical_ids['text'] = technical_ids['text'].str.lower()
    technical_ids['token'] = technical_ids['token'].str.lower()
    
    
    ### merge #######
    all_words = pd.concat([common_words,technical_ids],axis=0)
    
    if(len(all_words) == len(technical_ids) + len(common_words)):
        print('Ok!')
    
    del(common_words)
    del(technical_ids)
    
    
    ## Fin overlaps ##
    all_words = all_words.drop_duplicates(['text'])
    
    duplicated_words = {}
    for word in all_words.text:
        if word not in duplicated_words.keys():
            duplicated_words[word] = 1
        else:
            print(all_words[all_words.text == word] )
    
    del(duplicated_words)
    ##### apply countvectorizer   #########
    
    id_count_analyzer = CountVectorizer(analyzer='char_wb', ngram_range=(4,4),min_df=2)
    id_count_analyzer.fit(all_words['text'])
    id_count_analyzer.stop_words_ = None #Delete stop words vector as it can get pretty large
    print(len(id_count_analyzer.vocabulary_))
    
    ############### classifier  ################

    
    all_words = all_words.sample(frac=1).reset_index(drop=True)
    
    token_classifier = svm.SVC()
    k_fold = KFold(n_splits=10)
    #confusion = np.zeros((10, 10))
    scores = []
    for train_indices, test_indices in k_fold.split(all_words):
        
        
        train_text = id_count_analyzer.transform(all_words.iloc[train_indices]['text'])
        
        train_y = all_words.iloc[train_indices]['token']
        
        test_text = id_count_analyzer.transform(all_words.iloc[test_indices]['text'])
        test_y = all_words.iloc[test_indices]['token']
        
        token_classifier.fit(train_text, train_y)
        predictions = token_classifier.predict(test_text)
        print('Confusion matrix: ')
        print(confusion_matrix(test_y, predictions))
        score = f1_score(test_y,predictions,average='micro')
        scores.append(score)
    
    
    print('Total documents classified', len(all_words))
    print('Score:', round(sum(scores)/len(scores),2))
    
    
    
    
    #### save model ###
    from sklearn.pipeline import Pipeline
    tech_word_detector = Pipeline([
        ('word_vect', id_count_analyzer ),
        ('clf', token_classifier ),
        ])
    
    dump(tech_word_detector,model_path)
    
    return tech_word_detector




def words_analyzer(doc):


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



def get_ticket_vectorizer(retrain=False):
    model_path = 'models/ticket_vectorizer.joblib'
    if(os.path.exists(model_path) and not retrain):
        ticket_vectorizer = load(model_path)
        return ticket_vectorizer
    
    
    
    
    word_tokenizer = TfidfVectorizer( ngram_range=(1,2),min_df=3,tokenizer=words_analyzer,strip_accents='unicode')
    word_tokenizer.fit( incident_data['merged_texts'] )
    word_tokenizer.stop_words = None
    dump(word_tokenizer,model_path)
    
    return word_tokenizer
    


incident_data = mongoDbDac().get_ticket_data()



tech_word_detector = get_tech_word_detector(incident_data)



incident_data['merged_texts'] = incident_data['short_description'] + ' ' + incident_data['description'] + incident_data['close_notes']
incident_data['merged_texts'] = incident_data['merged_texts'].str.replace(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", '')

tech_token_buffer = {}


new_categories = pd.read_csv('text_corpora/ewm_tickets_dump_w_cats.csv',
    names=[
        'ticket_number','asignee','company','description','description_long',
        'issue_type','resolution','previous_category','l1__l2','l3'
        ], header = 0)


new_categories = new_categories[['ticket_number','l1__l2','l3']]
new_categories[['l1','l2']] = new_categories['l1__l2'].str.split('__', expand=True)
new_categories['_ticket_number'] = new_categories['ticket_number']
del(new_categories['ticket_number'])
new_categories = new_categories.set_index('_ticket_number')

incident_data = incident_data.join(new_categories)


word_tokenizer = get_ticket_vectorizer()


from sklearn.naive_bayes import ComplementNB
############### classifier  ################
from sklearn.preprocessing import LabelEncoder,OneHotEncoder

categories_df = (incident_data['l1'].value_counts() > 1)
categories_df = categories_df.reset_index()
categories_df = categories_df[categories_df['l1']]

incident_data_sample = incident_data[ ( incident_data['l1'].isin( categories_df['index']) ) & ~ ( (incident_data['l1'].isna() ) | (incident_data['merged_texts'].isna()) )  ]
incident_data_sample = incident_data_sample.sample(frac=1).reset_index(drop=True)


feature_set_map = incident_data['u_feature_set'].value_counts()
feature_set_map = feature_set_map.reset_index()
labelencoder = LabelEncoder()
feature_set_map['label_id'] = labelencoder.fit_transform(feature_set_map['index'])


one_hot_encoder_feature_set = OneHotEncoder()
one_hot_encoder_feature_set.fit(feature_set_map[['label_id']])
ticket_classifier_l1 = ComplementNB()
k_fold = KFold(n_splits=8)
#confusion = np.zeros((10, 10))
scores = []
for train_indices, test_indices in k_fold.split(incident_data_sample):
    
    train_text = hstack( 
        (
            word_tokenizer.transform(incident_data_sample.iloc[train_indices]['merged_texts']),
            one_hot_encoder_feature_set.transform(labelencoder.transform(incident_data_sample.iloc[train_indices]['u_feature_set']).reshape(-1,1))
        )
    )
    
    train_text = word_tokenizer.transform(incident_data_sample.iloc[train_indices]['merged_texts'])
    #train_text = word_tokenizer.transform(incident_data_sample.iloc[train_indices]['merged_texts'])
    train_y = incident_data_sample.iloc[train_indices]['l1']
    
    test_text = hstack( 
        (
            word_tokenizer.transform(incident_data_sample.iloc[test_indices]['merged_texts']),
            one_hot_encoder_feature_set.transform(labelencoder.transform(incident_data_sample.iloc[test_indices]['u_feature_set']).reshape(-1,1))
            
        )
    )
    test_text = word_tokenizer.transform(incident_data_sample.iloc[test_indices]['merged_texts'])
    
    #test_text =word_tokenizer.transform(incident_data_sample.iloc[test_indices]['merged_texts'])
    test_y = incident_data_sample.iloc[test_indices]['l1']
    
    ticket_classifier_l1.fit(train_text, train_y)
    predictions = ticket_classifier_l1.predict(test_text)
    score = f1_score(test_y,predictions,average='micro')
    scores.append(score)


# incident_data_sample['l1_pred'] =  ticket_classifier_l1.predict(hstack( 
#         (
#             word_tokenizer.transform(incident_data_sample['merged_texts']),
#             one_hot_encoder_feature_set.transform(labelencoder.transform(incident_data_sample['u_feature_set']).reshape(-1,1))
#         )
#     ))


incident_data_sample['l1_pred'] =  ticket_classifier_l1.predict(
    word_tokenizer.transform(incident_data_sample['merged_texts'])
        )
print(ticket_classifier_l1.classes_)
print('Score total l1:',f1_score(incident_data_sample['l1'],incident_data_sample['l1_pred'],average='micro'))
print('Confusion matrix: ')
print(confusion_matrix(incident_data_sample['l1'],incident_data_sample['l1_pred']))
print('Total documents classified', len(incident_data_sample))
print('Score:', round(sum(scores)/len(scores),2))

ticket_classifier_l1.categories_df = categories_df['index']
    
dump(ticket_classifier_l1, 'models/l1_model.joblib')
dump(labelencoder, 'models/feature_set_labeler.joblib')
dump(one_hot_encoder_feature_set, 'models/feature_set_onehot_encoder.joblib')



############### classifier  ################
test = (incident_data['l2'].value_counts() > 1)
test = test.reset_index()
test = test[test['l2']]
incident_data_sample = incident_data[ ( incident_data['l2'].isin( test['index']) ) &  ~ ( (incident_data['l2'].isna() ) | (incident_data['merged_texts'].isna()) )  ]
incident_data_sample = incident_data_sample.sample(frac=1).reset_index(drop=True)

#l1_cat_onehot = pd.get_dummies(incident_data_sample.l1).to_numpy()


l1_map = incident_data['l1'].value_counts()
l1_map = l1_map.reset_index()
labelencoder = LabelEncoder()
l1_map['label_id'] = labelencoder.fit_transform(l1_map['index'])


one_hot_encoder_l1 = OneHotEncoder()
one_hot_encoder_l1.fit(l1_map[['label_id']])



#ticket_classifier_l2 = svm.SVC()
ticket_classifier_l2 = ComplementNB()
k_fold = KFold(n_splits=8)
#confusion = np.zeros((10, 10))
scores = []
for train_indices, test_indices in k_fold.split(incident_data_sample):
    
    
    train_text = hstack( 
        (
            word_tokenizer.transform(incident_data_sample.iloc[train_indices]['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data_sample.iloc[train_indices]['l1']).reshape(-1,1))
        )
    )
    #train_text = word_tokenizer.transform(incident_data_sample.iloc[train_indices]['merged_texts'])
    train_y = incident_data_sample.iloc[train_indices]['l2']
    
    test_text = hstack( 
        (
            word_tokenizer.transform(incident_data_sample.iloc[test_indices]['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data_sample.iloc[test_indices]['l1']).reshape(-1,1))
        )
    )
    #test_text =word_tokenizer.transform(incident_data_sample.iloc[test_indices]['merged_texts'])
    test_y = incident_data_sample.iloc[test_indices]['l2']
    
    ticket_classifier_l2.fit(train_text, train_y)
    predictions = ticket_classifier_l2.predict(test_text)
    score = f1_score(test_y,predictions,average='micro')
    scores.append(score)


incident_data_sample['l2_pred'] =  ticket_classifier_l2.predict(hstack( 
        (
            word_tokenizer.transform(incident_data_sample['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data_sample['l1']).reshape(-1,1))
        )
    ))

print('Score total l2:',f1_score(incident_data_sample['l2'],incident_data_sample['l2_pred'],average='micro'))


print(ticket_classifier_l2.classes_)
print('Confusion matrix: ')
print(confusion_matrix(incident_data_sample['l2'],incident_data_sample['l2_pred']))
print('Total documents classified', len(incident_data_sample))
print('Score:', round(sum(scores)/len(scores),2))
    
dump(ticket_classifier_l2, 'models/l2_model.joblib')
dump(labelencoder, 'models/l1_labeler.joblib')
dump(one_hot_encoder_l1, 'models/l1_onehot_encoder.joblib')


############### classifier  ################
test = (incident_data['l3'].value_counts() > 1)
test = test.reset_index()
test = test[test['l3']]

incident_data_sample = incident_data[ ( incident_data['l3'].isin( test['index']) ) &  ~ ( (incident_data['l2'].isna() ) | (incident_data['merged_texts'].isna()) )  ]
incident_data_sample = incident_data_sample.sample(frac=1).reset_index(drop=True)


l2_map = incident_data['l2'].value_counts()
l2_map = l2_map.reset_index()
labelencoder_l2 = LabelEncoder()
l2_map['label_id'] = labelencoder_l2.fit_transform(l2_map['index'])


one_hot_encoder_l2 = OneHotEncoder()
one_hot_encoder_l2.fit(l2_map[['label_id']])

#ticket_classifier_l3 = svm.SVC()
ticket_classifier_l3 = ComplementNB()
k_fold = KFold(n_splits=8)
#confusion = np.zeros((10, 10))
scores = []
for train_indices, test_indices in k_fold.split(incident_data_sample):
    
    
    train_text = hstack( 
        (
            word_tokenizer.transform(incident_data_sample.iloc[train_indices]['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data_sample.iloc[train_indices]['l1']).reshape(-1,1)),
            one_hot_encoder_l2.transform(labelencoder_l2.transform(incident_data_sample.iloc[train_indices]['l2']).reshape(-1,1)),
                    )
    )
    #train_text = word_tokenizer.transform(incident_data_sample.iloc[train_indices]['merged_texts'])
    train_y = incident_data_sample.iloc[train_indices]['l3']
    
    test_text = hstack( 
        (
            word_tokenizer.transform(incident_data_sample.iloc[test_indices]['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data_sample.iloc[test_indices]['l1']).reshape(-1,1)),
            one_hot_encoder_l2.transform(labelencoder_l2.transform(incident_data_sample.iloc[test_indices]['l2']).reshape(-1,1))
        )
    )
    #test_text =word_tokenizer.transform(incident_data_sample.iloc[test_indices]['merged_texts'])
    test_y = incident_data_sample.iloc[test_indices]['l3']
    
    ticket_classifier_l3.fit(train_text, train_y)
    predictions = ticket_classifier_l3.predict(test_text)
    score = f1_score(test_y,predictions,average='micro')
    scores.append(score)


incident_data_sample['l3_pred'] =  ticket_classifier_l3.predict(hstack( 
        (
            word_tokenizer.transform(incident_data_sample['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data_sample['l1']).reshape(-1,1)),
            one_hot_encoder_l2.transform(labelencoder_l2.transform(incident_data_sample['l2']).reshape(-1,1))
        
        )
    ))

print('Score total l3:',f1_score(incident_data_sample['l3'],incident_data_sample['l3_pred'],average='micro'))

print(ticket_classifier_l3.classes_)
print('Confusion matrix: ')
print(confusion_matrix(incident_data_sample['l3'],incident_data_sample['l3_pred']   ))
print('Total documents classified', len(incident_data_sample))
print('Score:', round(sum(scores)/len(scores),2))
    
dump(ticket_classifier_l3, 'models/l3_model.joblib')
dump(labelencoder_l2, 'models/l2_labeler.joblib')
dump(one_hot_encoder_l2, 'models/l2_onehot_encoder.joblib')



# Upload prediction preview

incident_data['l1_pred'] =  ticket_classifier_l1.predict(
    word_tokenizer.transform(incident_data['merged_texts'])
        )

incident_data['l2_pred'] =  ticket_classifier_l2.predict(hstack( 
        (
            word_tokenizer.transform(incident_data['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data['l1']).reshape(-1,1))
        )
    ))



incident_data['l3_pred'] =  incident_data.predict(hstack( 
        (
            word_tokenizer.transform(incident_data['merged_texts']),
            one_hot_encoder_l1.transform(labelencoder.transform(incident_data['l1']).reshape(-1,1)),
            one_hot_encoder_l2.transform(labelencoder_l2.transform(incident_data['l2']).reshape(-1,1))
        
        )
    ))


for idx, ticket in incident_data.iterrows():
    
    update_query = { 'number' : ticket['number'] }
    set_query = { '$set' : { 'l1_pred' : incident_data['l1_pred'],
                             'l2_pred' : incident_data['l2_pred'],
                             'l3_pred' : incident_data['l2_pred']
                            
                            }}
    mongoDbDac.get_connection().service_now.incidents_ewm_full.update_one(update_query, set_query)