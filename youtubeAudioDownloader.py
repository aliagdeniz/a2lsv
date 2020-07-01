#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 01:36:59 2020

@author: ali
"""

from mongoDbUtils import * 
import subprocess
from os import path, system
from pydub import AudioSegment

from kafkaUtils import *
from kafka import KafkaConsumer
from time import sleep

from glob import glob
from vadUtils import *

from time import sleep

MAX_DOWNLOAD_RETRY = 3

def saveOnlyActiveSegments(fileDir):
    system('mkdir {}'.format(fileDir))
    audio, sample_rate = read_wave(fileDir+'.wav')
    vad = webrtcvad.Vad(1)
    frames = frame_generator(30, audio, sample_rate)
    frames = list(frames)
    segments = vad_collector(sample_rate, 30, 300, vad, frames)
    active_segments = None
    for i, segment in enumerate(segments):
        length = len(segment)//sample_rate
        if length >= 4 and length < 60:
            if active_segments:
                active_segments += segment
            else:
                active_segments = segment
            write_wave('{0}/{1}.wav'.format(fileDir, i), segment, sample_rate)
    write_wave(fileDir+'_active_segments.wav', active_segments, sample_rate)

def downloadVideo(videoId, db, datasetName, kafka_producer, attempt = 0):
    collection = db[datasetName]
    video = collection.find_one({'videoId' : videoId})
    if video and video['downloaded'] == False:
        try:
            videoPath = "./a2lsv_web/static/datasets/{0}/{1}".format(datasetName.replace(" ", "_"), videoId)
            command = 'youtube-dl --no-warnings --extract-audio -o {0}.%(ext)s {1}'.format(videoPath, videoId)
            # command = 'youtube-dl --no-warnings --extract-audio --audio-format aac -o {0}.%(ext)s {1}'.format(videoPath, videoId)
            print("video: {0} attempt: {1}".format(videoId, attempt))
            proc = subprocess.Popen(command.split(' '), 
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True,
                                    )
            out, err = proc.communicate()
            isDownloaded = '[download] 100% of ' in out
            isConverted = '[ffmpeg] Adding thumbnail to ' in out or "[ffmpeg] Destination: " in out
            isSkipped = "exists, skipping" in out
            error = "ERROR: No video formats found" in out
            if isDownloaded and isConverted or isSkipped:
                collection.update_one({'videoId' : videoId},
                                     {"$set" : {'downloaded' : True}})
                print("video: {0} downloaded.".format(videoId))

                videoFullPath = glob(videoPath+"*")[0]
                command = 'ffmpeg -i {0} -ac 1 -ar 16000 -y {1}.wav'.format(videoFullPath, videoPath)
                # command = 'ffmpeg -i {} -af pan=mono|c0=FL -ar 16000 -y {}.wav'.format(videoFullPath, videoPath)
                # command = 'ffmpeg -i {} -af pan=mono -ar 16000 {}.wav'.format(videoFullPath, videoPath)
                proc = subprocess.Popen(command.split(' '),
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        universal_newlines=True,
                                        )
                out, err = proc.communicate()
                # print(out)
                # sound = AudioSegment.from_file(videoPath +".aac")
                # sound.export(videoPath +".aac", format="wav", parameters=["-ar", "16000"])
                # sound.export(videoPath +".aac", format="m4a", parameters=["-ar", "16000"])
                # system('rm '+videoPath+".m4a")

                db.web_interface_datasets.update(
                    {'name': datasetName},
                    {"$inc": { 'countOfDownloadeds': 1} }
                    )

                saveOnlyActiveSegments(videoPath)
                ext = videoFullPath.split(".")[-1]
                print('message sent:', videoId, datasetName, ext)
                publish_message(kafka_producer, 'diarizeAudio', 'videoInfo', '{0};{1};{2}'.format(videoId, datasetName, ext) )
                sleep(5)
            elif attempt <= MAX_DOWNLOAD_RETRY:
                downloadVideo(videoId, collection, datasetName, kafka_producer,  attempt+1)
        except FileNotFoundError:
            print("Please install youtube-dl from https://youtube-dl.org/")
    elif video and video['downloaded'] == True:
        print('videoId:{} already downloaded.'.format(video['videoId']))
    else:
        print('videoId:{} couldn\'t find.'.format(videoId) )
        


print('Running Consumer..')
parsed_records = []
topic_name = 'downloadAudios'

db = getDB()
consumer = KafkaConsumer(topic_name, auto_offset_reset='earliest',
                         bootstrap_servers=['localhost:9092'], api_version=(0, 10), consumer_timeout_ms=1000)


kafka_producer = connect_kafka_producer()

while True:
    for msg in consumer:
        try:
            videoId, datasetName = msg.value.decode('utf-8').split(";")
            print('got request:', videoId, datasetName)
            downloadVideo(videoId, db, datasetName, kafka_producer)
        except:
            pass
    sleep(1)

