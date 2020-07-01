
"""A demo script showing how to DIARIZATION ON WAV USING UIS-RNN."""


import json
import pickle
import numpy as np
import os

# from mongoDbUtils import *
# os.chdir('a2lsv_web')

def similar(matrix):  # calc speaker-embeddings similarity in pretty format output.
    print('shape:', matrix.shape)
    dists = []
    ids = matrix.shape[0]
    for i in range(ids-1,ids):
        for j in range(ids):
            dist = matrix[i,:]*matrix[j,:]
            dist = np.linalg.norm(matrix[i,:] - matrix[j,:])
            dists.append(dist)
        break
    return dists


def moveFiles(labelList, datasetName, videoId, ID, k):
    for fileId, speakerId in labelList.items():
        if speakerId == k:
            finalsDir = 'static/datasets/{0}/final_dataset'.format( datasetName.replace(" ", "_") )
            if not os.path.exists( finalsDir ):
                os.system("mkdir {}".format(finalsDir))
            speakerDir = finalsDir+"/"+ID
            if not os.path.exists( speakerDir ):
                os.system("mkdir {}".format(speakerDir))

            videoIdDir = speakerDir+"/"+videoId
            if not os.path.exists(videoIdDir):
                os.system("mkdir {}".format(videoIdDir))
                
            fileDir = 'static/datasets/{0}/{1}/{2}.wav'.format( datasetName.replace(" ", "_") , videoId, fileId)
            moveDir =  videoIdDir+"/{}.wav".format(fileId)
            os.system("mv {0} {1}".format(fileDir, moveDir))

def deleteFiles(datasetName, videoId):
    videoDir = 'static/datasets/{0}/{1}'.format( datasetName.replace(" ", "_") , videoId)
    # print('dir to be deleted:', videoDir)
    os.system("rm -rf {0}/*".format(videoDir))
    os.system("rm -rf {0}*".format(videoDir))

def speakerDuplicatesExists(db, videoId, datasetName):
    collection = db[datasetName]
    speakers = db[datasetName+"_speakers"]
    
    similarSpeakers = []
    video = collection.find_one({'videoId' : videoId})
    if video and not video['speakersAdded']:
        labelList = json.loads(video['labelList'])
        embedingsDict = pickle.load(open('static/datasets/{0}/{1}/embedingsDict.pickle'.format( datasetName.replace(" ", "_") , videoId), "rb") )
        
        embeds = {}
        for fileId, speakerId in labelList.items():
            if speakerId != "-1":
                if speakerId in embeds:
                    embeds[speakerId].append(embedingsDict[fileId])
                else:
                    embeds[speakerId] = [embedingsDict[fileId]]
        
        currentEncodings = {}
        for speakerId, embeds in embeds.items():
            embeds = np.array(embeds).reshape(len(embeds), -1)
            meaned = np.mean(embeds, axis=0).reshape(1, -1)
            currentEncodings[speakerId] = {'meanedValues': meaned,
                                    'totalEmbeds':len(embeds),
                                    'channelId': video['channelId'],
                                    }
        
        similarSpeakerIndexs = []
        if speakers.count_documents({}) == 0:
            for i, [k, encoding] in enumerate(currentEncodings.items()):
                ID = str(i)
                doc = {"_id": ID,
                       "encoding": json.dumps(encoding['meanedValues'].tolist()),
                       'totalEmbeds': encoding['totalEmbeds'],
                       'channelId': encoding['channelId'],
                       'channelTitles': video['channelTitles'],
                       'sampleVideoId': video['videoId'],
                       'speakerIdOnSampleVideo': k,
                       }
                speakers.insert_one(doc)
                
                moveFiles(labelList, datasetName, videoId, ID, k)
                collection.update_one({'videoId' : videoId},
                                      {"$set" : {'speakersAdded' : True }})
        else:
            finalSpeakers = {}
            similarSpeakerIndexs = []
            for speaker in speakers.find({}):
                finalSpeakers[speaker['_id']] = {} 
                finalSpeakers[speaker['_id']]['encoding'] = speaker['encoding']
                finalSpeakers[speaker['_id']]['totalEmbeds'] = speaker['totalEmbeds']
                finalSpeakers[speaker['_id']]['channelId'] = speaker['channelId']
                finalSpeakers[speaker['_id']]['channelTitles'] = speaker['channelTitles']
                finalSpeakers[speaker['_id']]['sampleVideoId'] = speaker['sampleVideoId']
                finalSpeakers[speaker['_id']]['speakerIdOnSampleVideo'] = speaker['speakerIdOnSampleVideo']
    
            totalSpeakerCount = len(finalSpeakers)
    
            finalEncodings = []
            for k,v in finalSpeakers.items():
                finalEncodings.append(np.array(json.loads(v['encoding'])).reshape(-1))
    
            for i, [k, encoding] in enumerate(currentEncodings.items()):
                tmpEncodings = finalEncodings + [encoding['meanedValues'].reshape(-1)]
                tmpEncodings = np.array(tmpEncodings).reshape(len(tmpEncodings), -1)
                similarities = similar(tmpEncodings)
                print('similarities:',similarities)
                smallestIndex = 0
                smallestVal = similarities[0]
                for x, val in enumerate(similarities[:-1]):
                    if val < smallestVal and x not in similarSpeakerIndexs :
                        smallestVal = val
                        smallestIndex = x

                if smallestVal < 0.25: # find exact same speaker
                    print('found exact same speaker!')
                    w1 = finalSpeakers[str(smallestIndex)]['totalEmbeds']
                    w2 = encoding['totalEmbeds']
                    a1 = finalEncodings[smallestIndex].reshape(1, -1)
                    a2 = encoding['meanedValues'].reshape(1, -1)
                    finalTotalEmbed = w1 + w2
                    avarageEncoding = (a1*w1 + a2*w2)/finalTotalEmbed
                    speakers.update_one({'_id': str(smallestIndex)},
                                        {"$set": {'encoding': json.dumps(avarageEncoding.tolist()), 'totalEmbeds': finalTotalEmbed } })
                elif smallestVal < 0.75: # find possible same speaker
                    print('found possible same speaker!')
                    similarSpeakerIndexs.append(smallestIndex)
                    # print(finalSpeakers[str(smallestIndex)].keys())
                    finalSpeakers[str(smallestIndex)]['encoding'] = json.dumps(encoding['meanedValues'].tolist()),
                    finalSpeakers[str(smallestIndex)]['totalEmbeds'] = encoding['totalEmbeds']
                    finalSpeakers[str(smallestIndex)]['channelId'] = encoding['channelId']
                    finalSpeakers[str(smallestIndex)]['datasetName'] = datasetName
                    finalSpeakers[str(smallestIndex)]['speakerId'] = str(smallestIndex)
                    finalSpeakers[str(smallestIndex)]['compareVideoId'] = videoId
                    finalSpeakers[str(smallestIndex)]['compareSpeakerId'] = k
                    finalSpeakers[str(smallestIndex)]['similarSpeakerId'] = smallestIndex
                    similarSpeakers.append (finalSpeakers[str(smallestIndex)] )
                    # print (finalSpeakers[str(smallestIndex)] )
                else: # new speaker
                    print('added new speaker!')
                    ID = str(totalSpeakerCount+i)
                    doc = {"_id": ID ,
                           "encoding": json.dumps(encoding['meanedValues'].tolist()),
                           'totalEmbeds': encoding['totalEmbeds'],
                           'channelId': encoding['channelId'],
                           'channelTitles': video['channelTitles'],
                           'sampleVideoId': video['videoId'],
                           'speakerIdOnSampleVideo': k,
                           }
                    speakers.insert_one(doc)
    
                    moveFiles(labelList, datasetName, videoId, ID, k)
                    collection.update_one({'videoId' : videoId},
                                          {"$set" : {'speakersAdded' : True }})
    elif video:
        print("{} speakers allready added!".format(videoId))
    else:
        print("{} couldn't find!".format(videoId))
    return similarSpeakers






# videoId, datasetName = "01VP0K7AJmE", "tr_dataset"
# videoId, datasetName = "jdwGGZRCSPQ", "tr_dataset"
# videoId, datasetName = "7FPgM1f97wA", "tr_dataset"
# videoId, datasetName = "jdwGGZRCSPQ", "tr_dataset"

# db = getDB()
# collection = db[datasetName]
# # collection.update_many({}, {"$set": {"speakersAdded": False}})
# # collection.update_many({}, {"$set": {"labelsConfirmed": False}})


# a = speakerDuplicatesExists(db, videoId, datasetName)

