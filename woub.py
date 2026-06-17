"""Unread messages count from woub API

   Displays the total number of unread chat messages.
   Requires configuration: woub.url and woub.api_key

   Usage:
     bumblebee-status -m woub -p woub.url=https://your-api.com -p woub.api_key=YOUR_KEY

   Update interval (default 60s, override with -p woub.interval=N):
     bumblebee-status -m woub -p woub.interval=30 ...

   Visible hours (default 9:00-18:00, override with -p woub.start_time=HH:MM woub.end_time=HH:MM):
     bumblebee-status -m woub -p woub.start_time=8:30 -p woub.end_time=17:00 ...
"""

import core.module
import core.widget
import core.decorators
import requests
from datetime import datetime


class Module(core.module.Module):
    @core.decorators.every(minutes=1)
    def __init__(self, config, theme):
        super().__init__(config, theme, core.widget.Widget(self.full_text))

        self.__url = self.parameter("url", "")
        self.__api_key = self.parameter("api_key", "")
        self.__start_time = self.parameter("start_time", "9:00")
        self.__end_time = self.parameter("end_time", "18:00")
        self.__count = 0
        self.__error = None

    def __outside_visible_hours(self):
        now = datetime.now()
        start = datetime.strptime(self.__start_time, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        end = datetime.strptime(self.__end_time, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        return now < start or now > end

    def hidden(self):
        return self.__outside_visible_hours()

    def full_text(self, widgets):
        if not self.__url or not self.__api_key:
            return "woub: config missing"

        if self.__error:
            return self.__error

        return " {}".format(self.__count)

    def state(self, widget):
        return self.threshold_state(self.__count, 5, 15)

    def update(self):
        try:
            resp = requests.get(
                "{}/api/v1/chats".format(self.__url.rstrip("/")),
                headers={"Authorization": "ApiKey {}".format(self.__api_key)},
                timeout=30,
            )
            resp.raise_for_status()
            chats = resp.json()
            self.__count = sum(
                chat.get("count_new_messages", 0) for chat in chats
            )
            self.__error = None
        except requests.exceptions.HTTPError as e:
            self.__count = 0
            self.__error = "woub: {}".format(e.response.status_code)
        except requests.exceptions.ConnectionError:
            self.__count = 0
            self.__error = "woub: offline"
        except requests.exceptions.Timeout:
            self.__count = 0
            self.__error = "woub: timeout"
        except Exception as e:
            self.__count = 0
            self.__error = "woub: {}".format(type(e).__name__)
