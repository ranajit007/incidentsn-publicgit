# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 06:22:08 2020

@author: DanielEnriqueNavaTor
"""

import os
import pandas as pd
import numpy  as np


os.chdir(os.path.dirname(os.path.abspath(__file__)))


import pymongo 
ip = "9.85.140.181"
ip = "localhost"
connection = "mongodb://" + ip + ":27017/&socketTimeoutMS=360000"
if 'MONGODB_HOST' in os.environ:
    connection =  'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOST'] +  '/service_now&socketTimeoutMS=360000'        
db_client = pymongo.MongoClient(connection)
db_name = db_client["service_now"]
db_col = db_name["incidents"]


mongo_query = {"category":"User",
               "$and": [ {"description_long" : { "$ne" : "404"}},
                         {"description_long" : { "$ne" : ""}}]
               } #mongodb



mongo_query = { "description" : { "$ne" : "404"},
               "$and": [
                   {"description" : { "$ne" : ""}},
                   # {"predictions" : {"$exists" : False }}
                   
                   
                   ]}
                #mongodb
                
                
incident_data = pd.DataFrame.from_records(db_client
                                          .service_now
                                          .incidents_ewm_full.find(mongo_query)) #mongodb


incident_data = incident_data.fillna(' ')


from joblib import dump, load
##############################################
# Resolution model
##############################################
from keras.models import Model
from keras.layers import Input, LSTM, Dense, Embedding, TimeDistributed

from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.text import text_to_word_sequence,one_hot
from tensorflow import keras
import pickle 


latent_dim = 300
VOCAB_SIZE = 5000
MAX_LEN = 100
MAX_LEN2 = MAX_LEN
num_encoder_tokens = VOCAB_SIZE
num_decoder_tokens = VOCAB_SIZE


infile = open('models/word2idx','rb')
word2idx = pickle.load(infile)
infile.close()


infile = open('models/idx2word','rb')
idx2word = pickle.load(infile)
infile.close()


infile = open('models/tokenizer','rb')
tokenizer = pickle.load(infile)
infile.close()


def text2seq(encoder_text, decoder_text, tokenizer):

  encoder_sequences = tokenizer.texts_to_sequences(encoder_text)
  decoder_sequences = tokenizer.texts_to_sequences(decoder_text)
  
  return encoder_sequences, decoder_sequences




def padding(encoder_sequences, decoder_sequences, max_len_enc, max_len_dec):
  
  encoder_input_data = pad_sequences(encoder_sequences, maxlen=MAX_LEN, dtype='int32', padding='post', truncating='post')
  decoder_input_data = pad_sequences(decoder_sequences, maxlen=MAX_LEN, dtype='int32', padding='post', truncating='post')
  
  return encoder_input_data, decoder_input_data


def decoder_output_creater(decoder_input_data, num_samples, MAX_LEN, VOCAB_SIZE):
  
  decoder_output_data = np.zeros((num_samples, MAX_LEN, VOCAB_SIZE), dtype="float32")

  for i, seqs in enumerate(decoder_input_data):
      for j, seq in enumerate(seqs):
          if j > 0:
              decoder_output_data[i][j-1][seq] = 1.
  print(decoder_output_data.shape)
  
  return decoder_output_data



encoder_sequences, decoder_sequences = text2seq(incident_data['description'], [''], tokenizer)
                                                
encoder_input_data, decoder_input_data = padding(encoder_sequences,decoder_sequences,MAX_LEN, MAX_LEN )
#decoder_output_data = decoder_output_creater(decoder_input_data, len(all_incidents), MAX_LEN, VOCAB_SIZE)



  # Define an input sequence and process it.
encoder_inputs = Input(shape=(None, ) )
encoder_embedding = Embedding(input_dim = num_encoder_tokens, output_dim = latent_dim)
x = encoder_embedding(encoder_inputs)
x, state_h, state_c = LSTM(latent_dim, return_state=True)(x)
encoder_states = [state_h, state_c]

# Set up the decoder, using `encoder_states` as initial state.
decoder_inputs = Input(shape=( None, ) )
decoder_embedding = Embedding(input_dim = num_decoder_tokens, output_dim = latent_dim)
x = decoder_embedding(decoder_inputs)
decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
decoder_outputs,_ ,_ = decoder_lstm(x, initial_state=encoder_states)

#decoder_outputs = Dense(VOCAB_SIZE, activation='softmax')(x)
#decoder_dense = TimeDistributed(Dense(num_decoder_tokens, activation='softmax'))
decoder_dense = Dense(num_decoder_tokens, activation='softmax')
outputs = decoder_dense(decoder_outputs)
# Define the model that will turn
# `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
model = Model([encoder_inputs, decoder_inputs], outputs)

# Compile & run training
# model.compile(optimizer='rmsprop', loss='categorical_crossentropy',
#               metrics=['accuracy'])
# Note that `decoder_target_data` needs to be one-hot encoded,
# rather than sequences of integers like `decoder_input_data`!


# model.fit([encoder_input_data, decoder_input_data], decoder_output_data,
#           batch_size=batch_size,
#           epochs=epochs,
#           validation_split=0.2)  
    
##################################################################################    
    
    
# Save model
# model.save('s2s.h5')
model = keras.models.load_model('models/s2s.h5')

# Next: inference mode (sampling).
# Here's the drill:
# 1) encode input and retrieve initial decoder state
# 2) run one step of decoder with this initial state
# and a "start of sequence" token as target.
# Output will be the next target token
# 3) Repeat with the current target token and current states

# Define sampling models
encoder_model = Model(encoder_inputs, encoder_states)

decoder_state_input_h = Input(shape=(latent_dim,))
decoder_state_input_c = Input(shape=(latent_dim,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]

decoder_emb_2 = decoder_embedding(decoder_inputs)

decoder_outputs, state_h, state_c = decoder_lstm(decoder_emb_2, initial_state=decoder_states_inputs)
decoder_states = [state_h, state_c]
decoder_outputs = decoder_dense(decoder_outputs)
decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs] + decoder_states)



def decode_sequence(input_seq):
    # Encode the input as state vectors.
    states_value = encoder_model.predict(input_seq)

    # Generate empty target sequence of length 1.
    target_seq = np.zeros((1, 1))
    # Populate the first character of target sequence with the start character.
    target_seq[0, 0] = word2idx['strstrng']
    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    stop_condition = False
    decoded_sentence = ''
    counter = 0
    while not stop_condition:
       
        output_tokens, h, c = decoder_model.predict( [target_seq] + states_value)
       
        # Sample a token
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        if(sampled_token_index > 0):
            sampled_char = idx2word[sampled_token_index]
        else:
            sampled_char = 'endstrng'
        
        
        # Exit condition: either hit max length
        # or find stop character.
        if (sampled_char == 'endstrng' or
           counter >= MAX_LEN-1 ):
            stop_condition = True
        else:
            decoded_sentence += sampled_char + ' '
        
        
        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1))
        target_seq[0, 0] = sampled_token_index
        # Update states
        states_value = [h, c]
        
        counter += 1

    return decoded_sentence


for seq_index in range(len(incident_data)):
    input_seq = encoder_input_data[seq_index: seq_index + 1]
    decoded_sentence = decode_sequence(input_seq)
    
    incident_data.loc[seq_index, 'generated_description'] = decoded_sentence

##############################################
# Feature set model
##############################################



##############################################
# categories model
##############################################
from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer


from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn import svm
from sklearn.naive_bayes import MultinomialNB



## Read from saved objects

##Save Vectorizer
description_long_tfidfvectorizer = load('tfidf_vectorizer.joblib')

##Save models
model_pipeline = load('model_pipeline.joblib')

##
model_pipeline_cat2 = load('model_pipeline_cat2.joblib')


incident_data['close_notes'] = incident_data['close_notes'].map(' '.join)
incident_data['merged_description'] = incident_data['short_description']
incident_data['merged_description'] = incident_data['merged_description'] + ' ' + incident_data['description'] 
incident_data['merged_description'] = incident_data['merged_description'] + ' ' + incident_data['close_notes'] 
#incident_data['merged_description'] = incident_data['merged_description'] + ' ' + incident_data['comments']

#incident_data['merged_description'] = incident_data['merged_description'] .replace(np.nan, '', regex=True)

incident_data['merged_description'] = incident_data.merged_description.apply(str)

incident_data['cat1_pred'] =  model_pipeline.predict(description_long_tfidfvectorizer.transform(incident_data['merged_description']))
incident_data['cat2_pred'] =  model_pipeline_cat2.predict(description_long_tfidfvectorizer.transform(incident_data['merged_description']))


import uuid
from bson.objectid import ObjectId
from datetime import datetime
from time import sleep
prediction_template = {   
            'uuid': "",
            'type': "category_1",
            'text': "Inbound",
            'date': "2020-11-11 01:01:01",
            'feedback'     : '', 
            #'feedback_date':  "2020-11-12 01:01:01"
}

for idx, ticket in incident_data.iterrows():
    predictions = []
    # Cat 1
    prediction = {}
    prediction['uuid'] = str(uuid.uuid4())
    prediction['type'] = 'category 1'
    prediction['text'] = ticket['cat1_pred']
    prediction['date'] = str(datetime.now())
    predictions.append(prediction)
    # sleep(0.01)
    # Cat 2
    prediction = {}
    prediction['uuid'] = str(uuid.uuid4())
    prediction['type'] = 'category 2'
    prediction['text'] = ticket['cat2_pred']
    prediction['date'] = str(datetime.now())
    predictions.append(prediction)
    # sleep(0.01)
    # Cat 1
    prediction = {}
    prediction['uuid'] = str(uuid.uuid4())
    prediction['type'] = 'Resolution'
    prediction['text'] = ticket['generated_description']
    prediction['date'] = str(datetime.now())
    
    predictions.append(prediction)
    update_query = { 'number' : ticket['number'] }
    set_query = { '$set' : { 'predictions' : predictions }}
    db_client.service_now.incidents_ewm_full.update_one(update_query, set_query)
    

