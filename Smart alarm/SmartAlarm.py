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

Events_list = []  # [[event_name,epoch,event_desc,repeat=boolean,weather =boolean,news = boolean]]
notification_list = []
events = sched.scheduler(time.time, time.sleep) #inititat the schduler
app = Flask(__name__, template_folder='template')
removed_manually = False # global variable to determine is event has been removed or it expired by itself
notification_index = 0#for keeping track of niotifications to be deleted.


def event_log(event_type: str,description: str):
    """
    event_type:used to show what event occured
    description:brief summary of event details

    """
    log_file = open(read_json("Event_log"), "a")
    log_file.write("time: " + str(time.time()) + " ,type of event :" + str(event_type) + " ,description:  " + str(description) + "\n")
    log_file.close()


def read_json(key: str)->str:
    """
    one paramater:key used to find the desired date from json file
    returns a list:[item1:str,item2:str] or string
    """

    with open('jsonFile.json') as f:
        data = json.load(f)#loads json file
        x = data[key]
        if key == "Event_database" or key == "Event_log":#logic to detemine what date to exctract
            return x[0]["location"]
        elif key == "weather_api" or key == "news_api":
            return [x[0]["location"], x[0]["api-key"]]
        else:
            return [x[0]["volume"], x[0]["speed"]]
        event_log("reading json file...."," looking for : "+ str(key) +"")

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



def weather()->str:
    """
    returns "weather_desc" which is a string from the weather api

    """
    event_log("retrieve weather data...","")
    location =read_json("weather_api")[0] #grabs infro from json fucntion
    complete_api_link = "https://api.openweathermap.org/data/2.5/weather?q="+location+"&appid="+read_json("weather_api")[1]+""
    api_link = requests.get(complete_api_link)
    api_data = api_link.json()
    weather_desc = api_data['weather'][0]['description']#exctracts the wanted data from api
    return(weather_desc)

def news()->str:#return array[news desc,news link]
        """
        returns "news_result" which is a string from the weather api

        """
        event_log("retrieve news data....","")
        c = 0
        location = read_json("news_api")[0]
        main_url = "https://newsapi.org/v2/top-headlines?country="+location+"&apiKey="+read_json("news_api")[1]+""#add a country selection optin via json
        page = requests.get(main_url).json()
        article = page["articles"]
        news_result = []
        for data in article:
            news_result.append([data["title"],str(data["url"]).replace('"'," ")])#exctracts the wanted data from api
            if c == 5:#add this to json file so scalibility
                break
            c+=1
        return news_result

def covid_data()->str:# make it so json file can change days number
    """
    returns "cases_list" which is a string from the weather api
    """
    event_log("retrieve covid data...","")
    c = 0
    covid_info= (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=nation;areaName=england&'
        'structure={"date":"date","newCases":"newCasesByPublishDate"}'
    )
    response = get(covid_info, timeout=10)
    result = response.json()
    cases_list=[]
    for x in result['data']:
        cases_list.append((str(x['date']) + " Cases in the country on that day:    " + str(x['newCases'])))
        if c == 6:#displays covid cases for past 7 days
            break
        c+=1
    return cases_list
# add tts to every necessary place in code


def convert_to_epoch(event_time_date) -> int:
    """
    returns integer epoch value of date

    """
    pattern = '%Y-%m-%d %H:%M'
    return int(time.mktime(time.strptime(event_time_date, pattern)))#to epoch value


def read():
    """
    this function reads existing alarms froma text file
    so the can be re displayed in the ui even after the aplication restarts

    """
    # checks if existing alarms exist and places them in a list for faster data manipulation
    event_log("reading event database....","")
    data_file = open(read_json("Event_database"), "r+")
    temp_list = []
    if os.stat(read_json("Event_database")).st_size > 0:
        for z in data_file:#reads each line of file
            temp = ""
            for element in z:
                if element == ",":#looks for comma as its used for seperating data in file
                    temp_list.append(temp)
                    temp = ""
                else:
                    temp = temp + element
            Events_list.append(temp_list.copy())
            if math.floor(time.time()) - (convert_to_epoch(temp_list[1])) < 0:#determines if event is not expired
                events.enter(-(math.floor(time.time()) - (convert_to_epoch(temp_list[1]))), 1, expired_alarm)
            else:  # already expired
                expired_alarm()
            temp_list.clear()
    data_file.close()
def write():
    event_log("wrtiting to event database.....","")
    data_file = open(read_json("Event_database"), "r+")
    data_file.truncate(0)
    for z in range(len(Events_list)):#wtites the list into the file
        a = Events_list[z][0]
        b = Events_list[z][1]
        c = Events_list[z][2]
        d = Events_list[z][3]
        e = Events_list[z][4]
        f = Events_list[z][5]
        data_file.write((a + "," + str(b) + "," + c + "," + d + "," + e + "," + f + "," ) + "\n")
    data_file.close()

def set_alarm(event_date_time:str, event_name:str, event_desc:str, repeat:bool,weather:bool,news:bool):
    """
    paramaters:
    event_time_date-the date of event set
    event_name-event name every event has a unique name
    event_desc-brief description of the event
    repeat-a boolean to determine if event has to be repeated
    weather-boolean is weather is wanted
    news-booleann if news are wanted.

     returns: False if error occured
    """
    event_log("setting a alarm....","alarm name: " + str(event_name)+"")
    already_found = False
    epoch = convert_to_epoch(event_date_time)
    if epoch > int(time.time()):  # has to check is time set is in the future.
        if len(Events_list) > 0:  # checks if there is a item in a list to avoid index out of range error
            for x in range(len(Events_list)):
                if Events_list[x][0] == event_name:
                    if epoch == Events_list[x][1]:  # same time and event name means duplicate,can still update other stuff
                        Events_list[x][2] = event_desc
                        Events_list[x][3] = repeat
                        Events_list[x][4] = weather
                        events_list[x][5] = news
                        already_found = True
                        break
                    else:  # (update) ;  same event but different time.
                        Events_list.pop(x)
                        break
            if not already_found:
                Events_list.append([event_name, event_date_time, event_desc, repeat,weather,news])
                Events_list.sort(key=lambda z: z[1])#sorts the events in order of time
                write()
                events.enter(-(math.floor(time.time()) - epoch), 1, expired_alarm)#adds event to scheduler
        elif len(Events_list) == 0:  # if list is empty:
            Events_list.append([event_name, event_date_time, event_desc, repeat,weather,news])
            events.enter(-(math.floor(time.time()) - epoch), 1, expired_alarm)#adds event to scheduler
            write()
    else:
        return False


def event_remove(event_name:str):#maybe make a add events function
    """
    removes an event and decides if the event has additional notifications to be displayed.

    """
    global removed_manually
    global notification_index #always incremented so notifications can be removed
    for y in range(len(Events_list)):  # sorted in ascending order.
        if removed_manually is False:#if the alrm has expired by its own ,check if it has extras selected and if so; display them:
            if Events_list[y][5] == "true": #news
                temp_notifi_list = news().copy()
                for w in temp_notifi_list:
                    a = w[0]#news title
                    b = w[1]#link
                    notification_list.append(['"{}"'.format(a), "not_alarm",[str(notification_index),"newslink",'{}'.format(b)]])
                    notification_index+=1
                temp_notifi_list = covid_data().copy()
                for w in temp_notifi_list:
                    notification_list.append(['"{}"'.format(w), "not_alarm",[str(notification_index)]])
                    notification_index+=1
            if Events_list[y][4] == "true":#weather
                   notification_list.append(['"{}"'.format("Todays Weather: " + weather()), "not_alarm",[str(notification_index)]])
                   notification_index+=1
        if Events_list[y][0] == event_name:
            event_log("rescheduling alarm for next day....","")
            if Events_list[y][3] == "true" and removed_manually is False:#if this is true the the event is set to be repeated
                new_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(convert_to_epoch(Events_list[y][1]) + 86400))
                set_alarm(new_date, event_name, Events_list[y][2], Events_list[y][3],Events_list[y][4],Events_list[y][5])
                notification_list.append(['"{}"'.format(event_name) + "Has been rescheduled for next day", "alarm", Events_list[y]])
                speak_output(event_name + "has been repeated for next day")
            else:#event is going to be removed
                event_log("removing alarm....","")
                removed_manually = False#changes the boolean so the function can go back to deafult state as this is global varibale
                notification_list.append(['"{}"'.format(event_name) + " is expired/deleted", "alarm", Events_list[y]])
                speak_output(event_name + "has expired or been removed")
                Events_list.pop(y)#removes from list
            temp_notifi_list = []
            write()
            break


def expired_alarm():
    """
    checks if a alarm has expired,called using the scheduler

    """
    temp_events = Events_list.copy()
    for x in range(len(temp_events)):#iterates for the whole events list
        if time.time() >= convert_to_epoch(temp_events[x][1]):#if the time set is less than current time it must be expired
            event_remove(temp_events[x][0])

read()#this reads alarms from the txt file in case there are some upcomming alarms



@app.route('/delete_alarm/<event_name>')
def event_remove_manual(event_name:str):
    """
    remove a given alarms one the use presses a button on the ui.
    paramater:event_name - string to help determine which alram to remove from the events_list
    """
    event_log("user deleted alarm: ",str(event_name))
    global removed_manually
    removed_manually = True
    event_remove(event_name)
    return render_template("alarm.html", Events_list=Events_list, notification_list=notification_list)


@app.route('/', methods=['POST', 'GET'])
def alarm_page_clock():
    """
    this function grabs data form (once buton has been pressed)

    """
    events.run(blocking=False)
    if request.method == 'POST':
        event_name = str(request.values.get('event_name'))
        event_date_time = str(request.values.get('event_date'))
        event_desc = str(request.values.get('event_desc'))
        event_log("user submitted data...","event :"+event_name+" date :"+event_date_time+" description: "+event_desc+"")
        if event_name != "" and event_date_time != "":#logic for setting boleans so the program can determine what data to display with each event as it expires
            if request.form.get("repeat") is None:
                repeat = "false"
            else:
                repeat = "true"
            if request.form.get("weather") is None:
                weather = "false"
            else:
                weather = "true"
            if request.form.get("news") is None:
                news = "false"
            else:
                news = "true"
            set_alarm(event_date_time.replace("T", " "), event_name, event_desc,repeat,weather,news)
            speak_output(event_name + "has been added to upcomming alarms")
    return render_template("alarm.html", Events_list=Events_list, notification_list=notification_list)


@app.route('/delete_notification/<expired_alarm_name>', methods=['POST', "GET"])
def delete_notification(expired_alarm_name):#no need to change
    """
    remove NOTIFICATIONS
    paramater:expired_alarm -helps to identify which notification to remove

    """
    event_log("user deleted notification....","  notification id/name:"+ str(expired_alarm_name)+"")
    for y in range(len(notification_list)):  # sorted in ascending order.
        if notification_list[y][2][0] == expired_alarm_name:
            notification_list.pop(y)#remove from notification list
            break
    return render_template("alarm.html", Events_list=Events_list, notification_list=notification_list)


if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)
