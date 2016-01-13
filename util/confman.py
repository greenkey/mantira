#!/usr/bin/env python2.7

"""
This library is used to fetch, ask or save local config

"""
__author__ = "Lorenzo Mele"
__credits__ = ["Lorenzo Mele"]
__license__ = "GPL"
__version__ = "0.1"
__email__ = "lorenzo.mele@agavee.com"

import os, json

class Confman:

    askQuestion = 'Please provide a value for {}/{}: '
    cfgPath = os.path.expanduser('~')

    def __init__(self, cfgFile="config.json", autosave=False, autoask=False):
        self.autosave = autosave
        self.autoask = autoask
        self.cfgFile = os.path.join(self.cfgPath,cfgFile)
        self.loadConfig()

    def loadConfig(self):
        if os.path.isfile(self.cfgFile):
            with open(self.cfgFile) as f:
                self.config = json.load(f)
        else:
            self.config = dict()
            if self.autosave:
                self.saveConfig()

    def saveConfig(self):
        with open(self.cfgFile,'w') as f:
            json.dump(self.config, f)

    def setAutosave(self, autosave):
        self.autosave = autosave

    def setAutoask(self, autoask):
        self.autoask = autoask

    def getCfgFile(self):
        return self.cfgFile

    def get(self, section, option, message=None):
        try:
            return self.config[section][option]
        except (KeyError):
            if self.autoask:
                return self.askOption(section,option,message)
            else:
                raise
        except:
            raise

    def put(self, section, option, value):
        if section not in self.config:
            self.config[section] = dict()

        self.config[section][option] = value

        if self.autosave:
            self.saveConfig()

    def askOption(self, section, option, message=None):
        if message == None:
            message = self.askQuestion.format(section, option)
        value = input(message)
        self.put(section,option,value)
        return value
