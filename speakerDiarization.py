
"""A demo script showing how to DIARIZATION ON WAV USING UIS-RNN."""

from time import sleep

import librosa
import numpy as np
import umap
import scipy.cluster.hierarchy as hcluster
from sklearn.manifold import TSNE         # You can try with TSNE if you like, I prefer UMAP 
from glob import glob

from encoder import inference as encoder
from mongoDbUtils import *
import json
import pickle
from kafka import KafkaConsumer

class SpeakerDiarization:

    isModelLoaded = False
    isModelLoading = False
    def __init__(self):
        if not SpeakerDiarization.isModelLoaded:
            SpeakerDiarization.isModelLoading = True
            print('loading models ...')
            self.loadModels()
            print('models loaded.')
        elif SpeakerDiarization.isModelLoading:
            while not SpeakerDiarization.isModelLoaded:
                print('loading models ...')
                sleep(2)
        else:
            print('using loaded model.')
            
    def loadModels(self):
        model_fpath = 'encoder/saved_models/pretrained.pt'
        encoder.load_model(model_fpath)        
        SpeakerDiarization.isModelLoaded = True            

    def predict(self, path):
        # fpath = '/home/ali/Desktop/a2lsv/deneme/'
        fpaths = glob(path+"/*.wav")
        embedings = []
        embedingsDict = {}
        for fpath in fpaths:
            wav = librosa.load(fpath, 16000)[0]
            encoder_wav = encoder.preprocess_wav(wav)
            embed, partial_embeds, _ = encoder.embed_utterance(encoder_wav, return_partials=True)
            embed = np.array(embed).reshape(-1)
            embedings.append(embed)
            embedingsDict[fpath.split("/")[-1].split(".wav")[0]] = embed

        pickle.dump(embedingsDict, open(path+"/embedingsDict.pickle", 'wb'))

        # reducer = TSNE()
        reducer = umap.UMAP(int(np.ceil(np.sqrt(len(embedings)))), metric="cosine")
        projections = reducer.fit_transform(embedings)
        
        thresh = 1
        clusters = hcluster.fclusterdata(projections, thresh, criterion="distance")

        speakerSlices = {}
        for fpath, speaker  in zip(fpaths, clusters):
            speaker = str(speaker)
            audioId = fpath.split('/')[-1].split('.')[0]
            if speaker not in speakerSlices.keys():
                speakerSlices[speaker] = [int(audioId)]
            else:
                speakerSlices[speaker] += [int(audioId)]
        for k, v in speakerSlices.items():
            v.sort()
        return speakerSlices

print('Running Consumer..')
parsed_records = []
topic_name = 'diarizeAudio'

db = getDB()
consumer = KafkaConsumer(topic_name, auto_offset_reset='earliest',
                         bootstrap_servers=['localhost:9092'], api_version=(0, 10), consumer_timeout_ms=1000)
sd = SpeakerDiarization()

while True:
    for msg in consumer:
        try:
            values = msg.value.decode('utf-8').split(";")
            print('got request:',values)
            videoId, datasetName, ext = values
            # if ext == 'opus':
            #     print('skipping opus file')
            #     continue
            # videoId = 'zjkqDfd4CLk'
            # datasetName = 'tr_dataset'
            collection = db[datasetName]
            video = collection.find_one({'videoId' : videoId})
            if video and video['speakersDiarized'] == False:
                print("speakers are being diarized; videoId: {}".format(videoId))
                speakerSlice = sd.predict(r'./a2lsv_web/static/datasets/{0}/{1}'.format(datasetName.replace(" ", "_"), videoId) )
                # speakerSlice = {'0':[{'start':15, 'stop':25}]}
                
                collection.update_one({'videoId' : videoId},
                                     {"$set" : {'speakersDiarized' : True,
                                                'jsonSpeakerSlice' : json.dumps(speakerSlice) }})
                db.web_interface_datasets.update(
                    {'name': datasetName},
                    {"$inc": { 'countOfDiarized': 1} }
                    )
                print('speaker diarization done; videoId:{}'.format(videoId))
            elif video and video['speakersDiarized'] == True:
                print('video:{} speakers already are diarized!'.format(videoId))
            else:
                print('videoId:{} couldn\'t find.'.format(videoId))
        except:
            pass
    sleep(1)





