#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 17:16:08 2020

@author: ali
"""

from pymongo import MongoClient
import pymongo
import json


def getMongoClient():
    try:
        configs = json.load(open('configs.json', 'r'))
    except:
        configs = json.load(open('../configs.json', 'r'))
    mongoDbAddress = configs["mongoDbAddress"]
    return MongoClient(mongoDbAddress)

def getDB():
    client = getMongoClient()
    return client.a2lsv

def dropDB():
    client = getMongoClient()
    client.drop_database('a2lsv')
