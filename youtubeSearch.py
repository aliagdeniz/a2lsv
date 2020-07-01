#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 23:48:18 2020

@author: ali
"""

import os
import googleapiclient.discovery
import googleapiclient.errors
import json

from pprint import pprint
from mongoDbUtils import *
from kafkaUtils import *

from kafka import KafkaConsumer
from time import sleep


def getGoogleApiClient():
    api_service_name = "youtube"
    api_version = "v3"
    configs = json.load(open('configs.json', 'r'))
    developerKey = configs["googleAPIDeveloperKey"]
    
    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=developerKey)
    return youtube

def getCountryOfYoutubeChannel(apiClient, channelIds):
    request = apiClient.channels().list(
        part="snippet",
        id=','.join(channelIds.keys())
    )
    try:
        results = request.execute()
    # except errors.HttpError as e:
    #     print(e)
    except:
        print('waiting')
        sleep(2)
        return getCountryOfYoutubeChannel(apiClient, channelId)
    for i in results['items']:
        try:
            channelIds[i['id']] = i['snippet']['country']
        except:
            pass
    return channelIds
    
def getYoutubeSearchResults(apiClient, query, lang):
    request = apiClient.search().list(
        q=query,
        part="id,snippet",
        type='video',
        eventType="completed",
        regionCode= lang.upper(),
        relevanceLanguage=lang,
        videoDuration="medium",
        maxResults=50,
        # pageToken='CAUQAA'
    )
    try:
        results = request.execute()
    # except errors.HttpError as e:
    #     print(e)
    except:
        return getYoutubeSearchResults(apiClient, query, lang)
    
    
    nextPageToken = results['nextPageToken']
    totalResults = results['pageInfo']['totalResults']
    channelIds = {}
    for i in results['items']:
        channelId = i['snippet']['channelId']
        channelIds[channelId] = ''

    channelIds = getCountryOfYoutubeChannel(apiClient, channelIds)

    validChannelIds = []
    for k, v in channelIds.items():
        if v == lang.upper():
            validChannelIds.append(k)
    results['validChannelIds'] = validChannelIds
    return results

def insertResultsToDb(results, lang, db, datasetName):
    # snippets = [ i['snippet'] for i in results['items'] ]
    collection = db[datasetName]
    collection.create_index(
        [("videoId", pymongo.DESCENDING), ("channelId", pymongo.ASCENDING)],
        unique=True
        )
    kafka_producer = connect_kafka_producer()
    validChannelIds = results['validChannelIds']
    for i in results['items']:
        if i['snippet']['channelId'] in validChannelIds:
            document = {
                'videoId' : i['id']['videoId'],
                'channelId' : i['snippet']['channelId'],
                'titles' : i['snippet']['title'],
                'channelTitles' : i['snippet']['channelTitle'],
                'language': lang,
                'downloaded' : False,
                'speakersDiarized' : False,
                'labelsConfirmed' : False,
                'speakersAdded' : False
                }
            try:
                collection.insert_one(document)
                print(document)
                publish_message(kafka_producer, 'downloadAudios', 'videoInfo', '{0};{1}'.format(document['videoId'], datasetName) )
            except pymongo.errors.DuplicateKeyError:
                print(document['videoId'], 'already exists.')
    
def createDataset(db, name, lang):
    db.web_interface_datasets.create_index(
        [("name", pymongo.DESCENDING)],
        unique=True
        )
    try:
        db.web_interface_datasets.insert_one({
            'name' : name,
            'language': lang,
            'countOfDownloadeds': 0,
            'countOfLabeleds': 0,
            })
    except pymongo.errors.DuplicateKeyError:
        print(name, 'dataset already exists.')


print('Running Consumer..')
parsed_records = []
topic_name = 'searchByKeyword'

db = getDB()

configs = json.load(open('configs.json', 'r'))
kafkaPort = str(configs["kafkaPort"])

consumer = KafkaConsumer(topic_name, auto_offset_reset='earliest',
                         bootstrap_servers=['localhost:'+kafkaPort], api_version=(0, 10), consumer_timeout_ms=1000)


while True:
    for msg in consumer:
        try:
            datasetName, lang, query = msg.value.decode('utf-8').split(";")
            print('request got: {}, {}, {}'.format(datasetName, lang, query ))

            collection = db[datasetName]
            apiClient = getGoogleApiClient()
            results = getYoutubeSearchResults(apiClient, query, lang)
            insertResultsToDb(results, lang, db, datasetName)
        except:
            pass
    sleep(1)



# print(collection.find({}).count())


# for i in collection.find({}):
#     print(i)

# print(collection.find({}).count())
# collection.delete_many({})

# print(results)

# if __name__ == "__main__":
#     main()
