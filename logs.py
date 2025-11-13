# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 11:37:40 2023

@author: Fabian Oppliger, fabian.oppliger@epfl.ch

This file contains some basic functions to configure and perform event logging.
The setup function is called before every event logging to make sure, the log
appears in the correct logfile (currnet year/month).
The logs are saved in logfiles/YYYY_MM.log
"""
import os
import configparser
import logging
import sys
import csv
from datetime import datetime
from datetime import timedelta

def setup_logging():
    logfile = 'logfiles/status/%4.f_status.log' %datetime.now().year
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


class ReadLogfiles:
    def __init__(self,temp_channels: dict):
        # Read config file to load the logfile path for pressure and temperature readings
        config = configparser.ConfigParser()
        config.read('config.ini')
        config_logging = config['LOGGING']
        date = datetime.today().strftime('%y-%m-%d')
        self.infile_path = os.path.join(os.path.realpath(config_logging['input_logfile_path']),date)
        
        # define filepath for logfiles for pressures, temperatures and flow
        self.pressures_file = os.path.join(self.infile_path, 'maxigauge ' + date + '.log')
        self.temp_channels = temp_channels
        self.temperatures_files = [os.path.join(self.infile_path, f'CH{i} T ' + date + '.log') for i in temp_channels.values()]
        self.heaters_file = os.path.join(self.infile_path, 'Heaters ' + date + '.log')
        self.channels_file = os.path.join(self.infile_path, 'Channels ' + date + '.log')
        self.flow_file = os.path.join(self.infile_path, 'Flowmeter ' + date + '.log')
        self.pressures = [0,0,0,0,0,0]
        self.temperatures = [0 for i in temp_channels.values()]
        self.heaters = [0]
        self.flow = [0]
        
        # define filepath for logging pressure, temperature and flow readings
        self.outfile = 'logfiles/readings/' + datetime.today().strftime('%Y') + '_readings.csv'
        if not os.path.isfile(self.outfile):
            date_time = ['Date','Time','Status']
            pressures = ['p1','p2','p3','p4','p5','p6','p4-p3']
            temperatures = [temp for temp in self.temp_channels.keys()]
            heaters = ['Still Heater']
            flow = ['Flow']
            header = date_time + pressures + temperatures + heaters + flow
            self.write_in_file(header)

    # read and return the last line of a file
    def read_last_line(self,file):
        return self.read_last_n_lines(file,n=1)[0]
    
    # read and return the last line of a file
    def read_last_n_lines(self,file,n):
        with open(file) as f:
            lines = f.readlines()
        lines_no_linebreak = [line.strip('\n') for line in lines]
        return lines_no_linebreak[-n:]

    # read pressure values from pressure logfile
    # looks for presence of 'CHx' in line string and then read the value next to it
    # average values over last n_avg lines to reduce noise
    def read_pressures(self):
        n_avg = 10
        line_string = self.read_last_n_lines(self.pressures_file,n=n_avg)
        self.pressures = [0,0,0,0,0,0]
        for line in line_string:
            line_list = line.split(',')
            for i in range(6):
                index = line_list.index(f'CH{i+1}')
                self.pressures[i] += float(line_list[index+3])
        for i in range(6):
            self.pressures[i] /= n_avg
    
    # read temperature values from temperature logfiles
    # loop through log files and get last temperature readings
    def read_temperatures(self):
        for i,file in enumerate(self.temperatures_files):
            # keep entry empty if the last reading was more than 5 minutes ago
            # or if the file is not found (i.e. it was not generated yet)
            try:
                line_string = self.read_last_line(file)
                line_list = line_string.split(',')
                timestamp = datetime.strptime(line_list[0] + ' ' + line_list[1],'%d-%m-%y %H:%M:%S')
                if timestamp+timedelta(minutes=5) > datetime.now():
                    self.temperatures[i] = line_list[-1]
                else:
                    self.temperatures[i] = ''
            except:
                self.temperatures[i] = ''
    
    # read flow values from heater logfile
    def read_heaters(self):
        try:
            line_string = self.read_last_line(self.channels_file)
            line_list = line_string.split(',')
            ext = line_list[-1]
            if ext == '1':
                line_string = self.read_last_line(self.heaters_file)
                line_list = line_string.split(',')
                self.heaters[0] = line_list[-1]
            else:
                self.heaters[0] = ''
        except:
            self.heaters[0] = ''
    
    # read flow values from flowmeter logfile
    def read_flow(self):
        line_string = self.read_last_line(self.flow_file)
        line_list = line_string.split(',')
        self.flow[0] = line_list[-1]
        
    def write_in_file(self,line):
        # open the file in the write mode
        with open(self.outfile, 'a', newline='') as f:
            # create the csv writer
            writer = csv.writer(f)
            # write a row to the csv file
            writer.writerow(line)
    
    # write readings into a new logfile
    def write_values(self, status):
        self.__init__(self.temp_channels)
        date_time = [datetime.today().strftime('%d-%m-%y'),datetime.today().strftime('%H:%M:%S')]
        self.read_pressures()
        p4_p3 = ['%.2e' % (float(self.pressures[3])-float(self.pressures[2]))]
        self.read_temperatures()
        self.read_heaters()
        self.read_flow()
        line = date_time + [status] + self.pressures + p4_p3 + self.temperatures + self.heaters + self.flow
        self.write_in_file(line)


# temp_channels = {'50K': 1,
#                       '4K': 2,
#                       'Still': 5,
#                       'MXC': 6
#     }
# if '3': temp_channels['Magnet']=int('3')
# if '': temp_channels['FSE']=int('')
        

# read_logs = ReadLogfiles(temp_channels)
# read_logs.write_values('Base Temperature')


# print(os.getcwd())
