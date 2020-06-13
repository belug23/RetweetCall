import clr # pylint: disable=all; noqa .net system
import codecs
import json
import os
import sys
import uuid
import base64

clr.AddReference('System.Speech')
from System.Speech.Synthesis import SpeechSynthesizer, VoiceGender # pylint: disable=all; noqa .net system


class RetweetCall(object):
    """ 
    Because I hate coding with only functions and using Global variables.
    Here is the RetweetCall, the tweeter reader.
    This will download your last X tweets and find the last one with the
    hashtag you determined and post it to the chat so your viewer can retweet it.
    """
    script_name = "Retweet Call"
    config_file = "config.json"
    application_name = 'Retweet Call'
    version = '1.0.0'

    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        self.settings = {}
        self.parent = None
        self.token = ''
    
    def set_parent(self, parent):
        self.parent = parent

    def set_configs(self):
        self.load_settings()
        self.setup_credentials()

    def setup_credentials(self):
        # Make this persistant
        self.register()
 
    def register(self):
        login_url = '{}{}'.format(
            self.settings.get('base_url'),
            self.settings.get('oauth2_url')
        )

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Authorization': 'Basic {}'.format(self.get_http_auth()),
        }

        # Post request
        self.parent.Log(self.script_name, headers['Authorization'])
        result = self.parent.PostRequest(login_url, headers, {}, False)
        # Decode and save API key
        self.parent.Log(self.script_name, result)
        response = json.loads(json.loads(result)['response'])
        self.token = response['access_token']
    
    def get_http_auth(self):
        return base64.standard_b64encode('{}:{}'.format(
            self.settings.get('api_key'),
            self.settings.get('api_secret')
        ))
    
    def download_tweets(self):
        headers = {
            'Authorization': 'Bearer {}'.format(self.token)
        }

        timeline_url = '{}{}{}'.format(
            self.settings.get('base_url'),
            self.settings.get('timeline_url').format(
                self.settings.get('number_of_tweets')
            ),
            self.settings.get('screen_name')
        )

        result = self.parent.GetRequest(timeline_url,headers)
        return json.loads(json.loads(result)['response'])

    def find_online_tweet(self, tweets):
        for tweet in tweets:
            entities = tweet.get('entities', {})
            for hashtag in entities.get('hashtags', []):
                if hashtag.get('text') == self.settings.get('search_hashtag'):
                    return tweet
        return None

    def load_settings(self):
        """
            This will parse the config file if present.
            If not present, set the settings to some default values
        """
        try:
            with codecs.open(os.path.join(self.base_path, '..', self.config_file), encoding='utf-8-sig', mode='r') as file:
                self.settings = json.load(file, encoding='utf-8-sig')
        except Exception:
            self.settings = {
                "liveOnly": True,
                "command": "!RetweetThis",
                "permission": "editor",
                "api_key": '',
			    "api_secret": '',
			    "retweet_text": '{user} is calling for a retweet, please go retweet this tweet: {tweet_url}',
                'screen_name': 'Belug23',
                "useCooldown": False,
                "useCooldownMessages": True,
                "cooldown": 60,
                "onCooldown": "{user}, {command} is still on cooldown for {cd} minutes!",
                "userCooldown": 180,
                "onUserCooldown": "{user}, {command} is still on user cooldown for {cd} minutes!",
                "base_url": "https://api.twitter.com",
                "oauth2_url": "/oauth2/token?grant_type=client_credentials",
                "search_hashtag": "GoingLive",
                "timeline_url": "/1.1/statuses/user_timeline.json?tweet_mode=extended&count={}&screen_name=",
                "tweet_url": "https://twitter.com/i/web/status/{}",
                "number_of_tweets": 10
            }


    def script_toggled(self, state):
        """
            Do an action if the state change. Like sending an announcement message
        """
        return

    def execute(self, data):
        """
            Parse the data sent from the bot to see if we need to do something.
        """
        # If it's from chat and the live setting correspond to the live status
        
        if self.can_parse_data(data):
            command = self.settings["command"].lower()
            if data.GetParam(0).lower() == command:
                if not self.is_on_cool_down(data, command):
                    return self.call_for_retweet(data, command)
        return
    
    def can_parse_data(self, data):
        return (
            data.IsChatMessage() and
            (
                (self.settings["liveOnly"] and self.parent.IsLive()) or 
                (not self.settings["liveOnly"])
            )
        )
    
    def is_on_cool_down(self, data, command):
        if (
            self.settings["useCooldown"] and
            (self.parent.IsOnCooldown(self.script_name, command) or
            self.parent.IsOnUserCooldown(self.script_name, command, data.User))
        ):
            self.send_on_cool_down_message(data, command)
            return True
        else:
            return False
    
    def send_on_cool_down_message(self, data, command):
        if self.settings["useCooldownMessages"]:
            commandCoolDownDuration = self.parent.GetCooldownDuration(self.script_name, command)
            userCoolDownDuration = self.parent.GetUserCooldownDuration(self.script_name, command, data.User)

            if commandCoolDownDuration > userCoolDownDuration:
                cdi = commandCoolDownDuration
                message = self.settings["onCooldown"]
            else:
                cdi = userCoolDownDuration
                message = self.settings["onUserCooldown"]
            
            cd = str(cdi / 60) + ":" + str(cdi % 60).zfill(2) 
            self.send_message(data, message, command=command, cd=cd)
    
    def call_for_retweet(self, data, command):
        tweets = self.download_tweets()
        tweet = self.find_online_tweet(tweets)
        tweet_id = tweet.get('id')
        tweet_url = self.settings.get('tweet_url').format(tweet_id)
        call = self.settings.get('retweet_text')
        self.set_cool_down(data, command)
        self.send_message(data, call, command, url=tweet_url)

    def set_cool_down(self, data, command):
        if self.settings["useCooldown"]:
            self.parent.AddUserCooldown(self.script_name, command, data.User, self.settings["userCooldown"])
            self.parent.AddCooldown(self.script_name, command, self.settings["cooldown"])

    def send_message(self, data, message, command=None, cd="0", url=''):
        if command is None:
            command = self.settings["command"]

        outputMessage = message.format(
            user=data.UserName,
            cost=str(None),  # not used
            currency=self.parent.GetCurrencyName(),
            command=command,
            cd=cd,
            tweet_url=url
        )
        self.parent.SendStreamMessage(outputMessage)

    def tick(self):
        """
        not used, here for maybe future projects.
        """
        return
    
    def open_read_me(self):
        location = os.path.join(os.path.dirname(__file__), "README.txt")
        if sys.platform == "win32":
            os.startfile(location)  # noqa windows only
        else:
            import subprocess
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, location])
        return
