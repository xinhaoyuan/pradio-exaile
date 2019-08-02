# -*- coding: utf-8 -*-
"""
PRadio implementation as an Exaile plugin

Author: Xinhao Yuan <xinhaoyuan@gmail.com>
"""
import logging

logger = logging.getLogger(__name__)
import os
from xl import settings, event, main, playlist, xdg, trax
from xl.radio import RadioStation, RadioList, RadioItem
from xl.nls import gettext as _
from xlgui.panel import radio

import subprocess
import json
import sys

STATION = None

def enable(exaile):
    if exaile.loading:
        event.add_callback(_enable, 'exaile_loaded')
    else:
        _enable(None, exaile, None)

def _enable(o1, exaile, o2):
    global STATION

    STATION = PRadioStation()
    exaile.radio.add_station(STATION)

def disable(exaile):
    global STATION
    exaile.radio.remove_station(STATION)
    STATION = None

def set_status(message, timeout=0):
    radio.set_status(message, timeout)

def get_next_track_from_proc(proc, channel_id):
    try:
        proc.stdin.write(json.dumps({ "type" : "cmd_next", "channel_id" : channel_id }).encode("utf-8"))
        proc.stdin.write(b"\n")
        proc.stdin.flush()
        resp = json.loads(proc.stdout.readline().decode("utf-8"))
        assert(resp["type"] == "reply_ok")
        assert("data" in resp)
        assert("url" in resp["data"])

        data = resp["data"]
        url = data["url"]

        tr = trax.Track(uri = url)
        tags = {}
        if "title" in data:
            tags["title"] = data["title"]
            pass
        if "album" in data:
            tags["album"] = data["album"]
            pass
        if "singers" in data:
            tags["artist"] = "/".join(data["singers"])
            pass
        tr.set_tags(**tags)
        return tr
    except Exception as e:
        print("Got error playing next song: %s" % repr(e))
        return None
    pass

def get_channel_lists_from_proc(proc):
    try:
        proc.stdin.write(json.dumps({ "type" : "cmd_list_channels" }).encode("utf-8"))
        proc.stdin.write(b"\n")
        proc.stdin.flush()
        resp = json.loads(proc.stdout.readline().decode("utf-8"))
        assert(resp["type"] == "reply_ok")
        assert("channels" in resp)

        return resp["channels"]
    except Exception as e:
        print("Got error getting channel list: %s" % repr(e))
        return []
    pass

class PRadioStation(RadioStation):

    name = "PRadio"

    def __init__(self):
        channels = settings.get_option("plugin/pradio/enabled", [])
        self._radios = []
        for c in channels:
            cmds = settings.get_option("plugin/pradio/" + c, [])
            self._radios.append(PRadioList(c, cmds, self))
            pass
        pass

    def get_lists(self, no_cache=False):
        return self._radios

class PRadioList(RadioList):

    def __init__(self, name, cmd, station):
        super(PRadioList, self).__init__(name, station)
        self._cmd = cmd
        self._proc = None
        pass

    def proc(self):
        if self._proc is None:
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags = subprocess.STARTF_USESHOWWINDOW
            except:
                si = None
                pass

            self._proc = subprocess.Popen(
                self._cmd,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                startupinfo = si)
            pass
        return self._proc

    def get_items(self, no_cache=False):
        channel_list = get_channel_lists_from_proc(self.proc())
        items = []
        for c in channel_list:
            items.append(PRadioItem(c["name"], c["id"], self.station, self))
            pass
        return items

class PRadioPlaylist(playlist.Playlist):

    def __init__(self, name, ritem):
        super(PRadioPlaylist, self).__init__(name, [ritem.get_next_track()])
        self._ritem = ritem
        pass

    def _auto_expand(self):
        """
        Make sure we are on normal mode and auto-expand the playlist.
        """
        self.shuffle_mode = 'disabled'
        self.repeat_mode = 'disabled'
        if self.get_current_position() == len(self) - 1:
            self.extend([self._ritem.get_next_track()])
            pass
        pass

    def get_next(self):
        self._auto_expand()
        return super(PRadioPlaylist, self).get_next()

    def next(self):
        self._auto_expand()
        return super(PRadioPlaylist, self).next()

    pass

class PRadioItem(RadioItem):

    def __init__(self, name, channel_id, station, rlist):
        super(PRadioItem, self).__init__(name, station)
        self._rlist = rlist
        self._channel_id = channel_id
        self._playlist = None
        pass

    def get_next_track(self):
        return get_next_track_from_proc(self._rlist.proc(), self._channel_id)

    def get_playlist(self):
        if self._playlist is None:
            self._playlist = PRadioPlaylist(self.name, self)
        return self._playlist
