from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

import urllib.parse
import html
import json
import base64
import numpy as np

from ..decorators import labeler_required
from ..models import User, Datasets

import sys
sys.path.append('../')
from mongoDbUtils import *
from solveSpeakerDuplicates import *


def listAudios(request):
    if request.user.is_authenticated and request.user.is_labeler:
        db = getDB()
        audios = []
        lang = request.user.language.name
        datasetsCursor = Datasets.objects.filter(language__name = lang)

        counter = 0
        for dataset in datasetsCursor:
            audiosCursor = db[dataset.name].find({'speakersDiarized':True, 'downloaded':True, 'labelsConfirmed' : False}).limit(10)
            for i in audiosCursor:
                audios.append({
                    'videoId': i['videoId'],
                    'channelTitles': i['channelTitles'],
                    'titles': html.unescape(urllib.parse.unquote(i['titles']) ),
                    'dbName': dataset.name,
                    'dataIndex': counter
                    })
                counter += 1
            if audios:
                break
        return render(request, 'web_interface/labeler/audio_list.html',
                      {'audios': audios })
    else:
        return redirect('login')
    
def labelAudio(request):
    if request.user.is_authenticated and request.user.is_labeler:
        db = getDB()
        if request.method == 'GET':
            dbName = request.GET.get('dbName')
            videoId = request.GET.get('videoId')

            audios = []

            jsonSpeakerSlice = db[dbName].find_one({'videoId': videoId})['jsonSpeakerSlice']
            speakerSlice= json.loads(jsonSpeakerSlice)
            
            for label, names in speakerSlice.items():
                for name in names:
                    audios.append({
                        'videoId': videoId,
                        'dbName': dbName.replace(" ", "_"),
                        'preLabel': label,
                        'name': name,
                        })
            return render(request, 'web_interface/labeler/label_audio.html',
                          {'audios': audios,
                           "speakerCount": [i+1 for i in list(range(len(speakerSlice)))],
                            'videoId': videoId,
                            'dbName': dbName
                           })
        elif request.method == 'POST':
            # print(request.POST)
            labelList = request.POST.get('labelList')
            videoId = request.POST.get('videoId')
            dbName = request.POST.get('dbName')
            
            collection = db[dbName]
            collection.update_one({'videoId' : videoId},
                                 {"$set" : {'labelsConfirmed' : True,
                                            'labelList' :  labelList }})
            db.web_interface_datasets.update(
                {'name': dbName},
                {"$inc": { 'countOfLabeleds': 1} }
                )
            similarSpeakers = speakerDuplicatesExists(db, videoId, dbName)
            # print(similarSpeakers)
            if similarSpeakers:
                print('find possible similar speaker')
                request.session['similarSpeakers'] = similarSpeakers
                return HttpResponseRedirect(reverse('labeler:solveSpeakerDuplicate'))
            else:
                print('no similiar speaker')
                deleteFiles(dbName, videoId)
                return redirect('labeler:listAudios')
    else:
        return redirect('login')

def solveSpeakerDuplicate(request):
    if request.user.is_authenticated and request.user.is_labeler:
        db = getDB()
        if request.method == 'GET':
            similarSpeakers = request.session.get('similarSpeakers')
            for similarSpeaker in similarSpeakers:
                datasetName = similarSpeaker['datasetName']
    
                sampleVideoId = similarSpeaker['sampleVideoId']
                speakerIdOnSampleVideo = similarSpeaker['speakerIdOnSampleVideo']
    
                sampleAudios = []
                sampleLabelListJson = db[datasetName].find_one({'videoId': sampleVideoId})['labelList']
                sampleLabelList = json.loads(sampleLabelListJson)
                
                for fileId, speakerId in sampleLabelList.items():
                    if speakerId == speakerIdOnSampleVideo and len(sampleAudios) < 10:
                        sampleAudios.append({
                            'videoId': sampleVideoId,
                            'dbName': datasetName.replace(" ", "_"),
                            'name': fileId,
                            })
                similarSpeaker['sampleAudios'] = sampleAudios

                compareVideoId = similarSpeaker['compareVideoId']
                compareSpeakerId = similarSpeaker['compareSpeakerId']
    
                compareAudios = []
                compareLabelListJson = db[datasetName].find_one({'videoId': compareVideoId})['labelList']
                compareLabelList = json.loads(compareLabelListJson)
                
                for fileId, speakerId in compareLabelList.items():
                    if speakerId == compareSpeakerId and len(compareAudios) < 10:
                        compareAudios.append({
                            'videoId': compareVideoId,
                            'dbName': datasetName.replace(" ", "_"),
                            'name': fileId,
                            })
                similarSpeaker['compareAudios'] = compareAudios
            # similarSpeakers = [similarSpeakers[0], similarSpeakers[0]]
            
            # print(similarSpeakers, len(similarSpeakers))
            
            encodedBytes = base64.b64encode(json.dumps(similarSpeakers).encode("utf-8"))
            postData = str(encodedBytes, "utf-8")
            
            return render(request, 'web_interface/labeler/solve_speaker_duplicate.html',
                          { 'similarSpeakers': similarSpeakers[:1],
                            'postData': postData })
        if request.method == 'POST':
            postData = request.POST.get('postData')
            isSameSpeaker = request.POST.get('isSameSpeaker')

            encodedBytes = base64.b64decode(json.dumps(postData).encode("utf-8"))
            postData = str(encodedBytes, "utf-8")
            postData = json.loads(postData)
            # print(postData, isSameSpeaker)

            speaker = postData[0]
            similarSpeakers = postData[1:]

            datasetName = speaker['datasetName']
            collection = db[datasetName]
            speakers = db[datasetName+"_speakers"]

            video = collection.find_one({'videoId' : speaker['compareVideoId']})
            if isSameSpeaker == 'false':

                speakers = db[datasetName+"_speakers"]
                totalSpeakerCount = speakers.count_documents({})
                # print(video, totalSpeakerCount)

                ID = str(totalSpeakerCount)
                print('added new speaker with ID {} !'.format(ID))
                doc = {"_id": ID,
                        # "encoding": json.dumps(np.array(speaker['encoding'][0]).reshape(1, -1).tolist()),
                        "encoding": speaker['encoding'][0],
                        'totalEmbeds': speaker['totalEmbeds'],
                        'channelId': speaker['channelId'],
                        'channelTitles': video['channelTitles'],
                        'sampleVideoId': speaker['compareVideoId'],
                        'speakerIdOnSampleVideo': speaker['compareSpeakerId'],
                        }
                speakers.insert_one(doc)
            else:
                similarSpeakerId = speaker['similarSpeakerId']
                similarSpeaker = speakers.find_one({'_id': str(similarSpeakerId)})
                w1 = similarSpeaker['totalEmbeds']
                a1 = np.array(json.loads(similarSpeaker['encoding'])).reshape(1, -1)
                w2 = speaker['totalEmbeds']
                a2 = np.array(json.loads(speaker['encoding'][0])).reshape(1, -1)
                finalTotalEmbed = w1 + w2
                avarageEncoding = (a1*w1 + a2*w2)/finalTotalEmbed
                ID = str(similarSpeakerId)
                speakers.update_one({'_id': ID},
                                    {"$set": {'encoding': json.dumps(avarageEncoding.tolist()), 'totalEmbeds': finalTotalEmbed } })

            labelList = json.loads(video['labelList'])
            moveFiles(labelList , datasetName, speaker['compareVideoId'], ID, speaker['compareSpeakerId'])
            collection.update_one({'videoId' : speaker['compareVideoId']},
                                  {"$set" : {'speakersAdded' : True }})

            if similarSpeakers:
                request.session['similarSpeakers'] = similarSpeakers
                return HttpResponseRedirect(reverse('labeler:solveSpeakerDuplicate'))
            else:
                deleteFiles(datasetName, speaker['compareVideoId'])
                return redirect('labeler:listAudios')
    else:
        return redirect('login')

