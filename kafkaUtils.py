#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 12:11:23 2020

@author: ali
"""


from kafka import KafkaProducer
import json

def publish_message(producer_instance, topic_name, key, value):
    try:
        key_bytes = bytes(key, encoding='utf-8')
        value_bytes = bytes(value, encoding='utf-8')
        producer_instance.send(topic_name, key=key_bytes, value=value_bytes)
        producer_instance.flush()
        print('Message published successfully.')
    except Exception as ex:
        print('Exception in publishing message')
        print(str(ex))


def connect_kafka_producer():
    _producer = None
    try:
        try:
            configs = json.load(open('configs.json', 'r'))
        except:
            configs = json.load(open('../configs.json', 'r'))
        kafkaPort = str(configs["kafkaPort"])

        _producer = KafkaProducer(bootstrap_servers=['localhost:'+kafkaPort], api_version=(0, 10))
    except Exception as ex:
        print('Exception while connecting Kafka')
        print(str(ex))
    finally:
        return _producer
