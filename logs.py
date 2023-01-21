# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 11:37:40 2023

@author: Fabian Oppliger, fabian.oppliger@epfl.ch

This file contains some basic functions to configure and perform event logging.
The setup function is called before every event logging to make sure, the log
appears in the correct logfile (currnet year/month).
The logs are saved in logfiles/YYYY_MM.log
"""

import logging
import sys
from datetime import datetime

def setup_logging():
    logfile = 'logfiles/%4.f_' %datetime.now().year + '%02.f.log' %datetime.now().month
    logging.root.handlers = []
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S',
                        handlers=[logging.FileHandler(logfile),
                            logging.StreamHandler(sys.stdout)])
    

# Writes info message in logfile. calls setup function every time in order to
# make sure the message is written in the correct file when the date changed.
def info(msg):
    setup_logging()
    logging.info(msg)

# Writes warning message in logfile. calls setup function every time in order to
# make sure the message is written in the correct file when the date changed.    
def warning(msg):
    setup_logging()
    logging.warning(msg)