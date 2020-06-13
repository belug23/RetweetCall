#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

from retweet_call import RetweetCall # pylint: disable=all; noqa
#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = RetweetCall.script_name
Website = "https://github.com/belug23/"
Description = "Search your tweets to find your last go live tweet and post the link in the chat"
Creator = "Belug"
Version = RetweetCall.version


chad_bot = RetweetCall()
# Ugly StreamLab part, just map functions to the class
def ScriptToggled(state):
    return chad_bot.script_toggled(state)

def Init():
    chad_bot.set_parent(Parent)  #  noqa injected by streamlabs chatbot
    return chad_bot.set_configs()

def Execute(data):
    return chad_bot.execute(data)

def ReloadSettings(jsonData):
    return chad_bot.set_configs()

def OpenReadMe():
    return chad_bot.open_read_me()

def Tick():
    return chad_bot.tick()
