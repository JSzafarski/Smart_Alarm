import time
from datetime import datetime
from flask import Flask, render_template, request
import sched
import os
import math
import pyttsx3
import requests #for api use
import json
from requests import get


########################################################################


def read_json(key):#returns list given the key
# validate if data is not found
    with open('jsonFile.json') as f:
        data = json.load(f)
        x = data[key]
        if key == "Event_database" or key == "Event_log":
            return x[0]["location"]
        elif key == "weather_api" or key == "news_api":
            return [x[0]["location"], x[0]["api-key"]]
        else:
            return [x[0]["volume"], x[0]["speed"]]


assert(read_json("Event_database"))
assert(read_json("weather_api"))

#####################################################################

def speak_output(message:str):
    """
    paramater:message for telling the tts engine what to say
    """
    event_log("voice message: ","say " + str(message)+"")
    engine = pyttsx3.init()
    engine.setProperty('rate', read_json("pyttsx3")[1])#adjusts rate from json
    engine.setProperty('volume', read_json("pyttsx3")[0])#adjusts volume from json
    engine.say(message)
    engine.runAndWait()
    engine.stop()

assert(speak_output("test1"))
assert(speak_output("test 2 2 2 2 "))
##########################################################################

def convert_to_epoch() -> int:
    """
    returns integer epoch value of date

    """
    pattern = '%Y-%m-%d %H:%M'
    return int(time.mktime(time.strptime(event_time_date, pattern)))#to epoch value
event_date_time = "2020-12-05T11:02"
assert(convert_to_epoch(event_date_time.replace("T", " ")))

############################################################################
