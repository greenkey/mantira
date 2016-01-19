#!/usr/bin/env python3

"""
This library is used to fetch, ask or save local config

"""
__author__ = "Lorenzo Mele"
__credits__ = ["Lorenzo Mele"]
__license__ = "GPL"
__version__ = "0.1"
__email__ = "coding@loman.it"


from suds.client import Client
import os, sys

class Mantis:

    def __init__(self,url,username,password):
        self.url = url
        self.username = username
        self.password = password
        self.client = Client(url)
        #try a simple call to check username/password
        self.mc_enum_status()

    def __getattr__(self, name):
        if name.startswith('mc_'):
            self.lastmethod = getattr(self.client.service, name)
            return self.genericMethod
        else:
            return super.__getattr__(name)

    def genericMethod(self,*args,**kwargs):
        kwargs['username'] = self.username
        kwargs['password'] = self.password
        try:
            # prevent printing
            sys.stdout = open(os.devnull, "w")
            sys.stderr = open(os.devnull, "w")
            ret = self.lastmethod(*args,**kwargs)
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            return ret
        except:
            raise


