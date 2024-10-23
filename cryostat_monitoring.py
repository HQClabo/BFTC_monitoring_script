# -*- coding: utf-8 -*-
"""
Created on Sat Dec 31 01:38:18 2022

@author: Fabian Oppliger, fabian.oppliger@epfl.ch
version: 1.0

Main program that contains a simple user interface that asks which monitoring
process should be run. It then monitors the specific temperatures sends messages
to a Discord channel.
The default temperature thresholds can be changed in the config.ini file.
"""


import time
import configparser
from textwrap import dedent
import traceback
import mqtt_interface as mqtt
import discord_access as discord
import logs

class UI():
    def __init__(self):
        # Read config file to define default threshold parameters and channel nr
        config = configparser.ConfigParser()
        config.read('config.ini')
        config_defaults = config['DEFAULTS']
        self.def_still_val = float(config_defaults['still_full_cd'])
        self.def_still_val_4K_cd = float(config_defaults['still_4K_cd'])
        self.def_still_val_coldinsert = float(config_defaults['still_coldinsert'])
        self.def_baseT_val = float(config_defaults['baseT'])
        self.def_circ_val = float(config_defaults['circ_warning'])
        self.def_warmup_val = float(config_defaults['warmup'])
        
        # define channel numbers of temperature sensors
        self.temp_channels = {'50K': 1,
                              '4K': 2,
                              'Still': 5,
                              'MXC': 6
            }
        if config_defaults['channel_nr_still']: self.temp_channels['Still']=int(config_defaults['channel_nr_still'])
        if config_defaults['channel_nr_mxc']: self.temp_channels['MXC']=int(config_defaults['channel_nr_mxc'])
        if config_defaults['channel_nr_magnet']: self.temp_channels['Magnet']=int(config_defaults['channel_nr_magnet'])
        if config_defaults['channel_nr_fse']: self.temp_channels['FSE']=int(config_defaults['channel_nr_fse'])
        
        if config_defaults['snapshot_time_hrs']:
            self.snapshot_time_hrs = float(config_defaults['snapshot_time_hrs'])
        else:
            self.snapshot_time_hrs = 0
        
        config_program_modes = config['PROGRAM_MODES']['available_modes'].split('\n')
        self.user_available_programs = [mode for mode in config_program_modes if mode != '']
        
        # create objects for mqtt client and discord server
        self.bftc = mqtt.Client_bftc()
        self.discord_server = discord.Discord_access()
        
        # setup object for reading and writing pressure and temperature values
        self.log = logs.ReadLogfiles(self.temp_channels)
        
    # Function definitions for different cooldown and warmup scenarios
    
    # Subscribes to temp sensors and checks them until the temp of temp_channel
    # is below (or above for cooling=False) the threshold.
    def monitor_temp(self,temp_channel, threshold, cooling=True, time_threshold=0):
        self.bftc.monitor_temp(temp_channel,threshold,cooling,time_threshold)
        
    # Monitors still temperature and returns a message with the time it took
    # to reach the threshold.
    def still_temp(self,time_start, threshold=5, cooling=True):
        self.monitor_temp(self.temp_channels['Still'],threshold, cooling)
        time_passed = time.time() - time_start
        hours = time_passed//3600
        minutes = (time_passed-hours*3600)//60
        # check if threshold was reached, otherwise repeat monitoring
        if not self.bftc.threshold_reached:
            self.check_disconnect(time_passed)
            self.still_temp(time_start,threshold,cooling)
            return 1
        msg = f'Still reached {threshold} K after %.0f h ' %(hours) + '%.0f min' %(minutes)
        self.discord_server.send_message(msg)
        return 1
    
    # Monitors mxc temperature and returns a message with the time it took
    # to reach the threshold.
    def mxc_temp(self,time_start, threshold, cooling=True):
        self.monitor_temp(self.temp_channels['MXC'],threshold,cooling)
        time_passed = time.time() - time_start
        hours = time_passed//3600
        minutes = (time_passed-hours*3600)//60
        # check if threshold was reached, otherwise repeat monitoring
        if not self.bftc.threshold_reached:
            self.check_disconnect(time_passed)
            self.mxc_temp(time_start,threshold,cooling)
            return 1
        msg = f'MXC reached {threshold*1000} mK after %.0f h ' %(hours) + '%.0f min' %(minutes)
        self.discord_server.send_message(msg)
        return 1
    
    def circulation_mode(self,threshold):
        # Monitors mxc temperature and returns a warning when it goes above threshold.
        print('Entered circulation mode')
        if self.snapshot_time_hrs:
            print(f'A snapshot of the readings will be taken every {self.snapshot_time_hrs} hours')
        print('Press Ctrl+C to exit the program')
        time_threshold = 3600*self.snapshot_time_hrs
        self.monitor_temp(self.temp_channels['MXC'], threshold, cooling=False, time_threshold=time_threshold)
        # check if threshold was reached, otherwise repeat monitoring
        # if the time threshold was reached, take a snapshot of the readings and continue monitoring
        while not self.bftc.threshold_reached:
            if self.bftc.time_threshold_reached:
                self.log.write_values('Base Temperature')
            else:
                self.check_disconnect()
            self.monitor_temp(self.temp_channels['MXC'], threshold, cooling=False, time_threshold=time_threshold)
            return 1
        msg = f'MXC surpassed {threshold*1000} mK '
        self.discord_server.send_warning(msg)
        self.log.write_values('Unexpected Warmup')
        return 1
    
    # Starts full cooldown and reports when still is cold enough for ciculation
    # and when reaching base temperature and then enters circulation mode.
    def full_cooldown(self,still_val,baseT_val,circ_val,msg):
        self.log.write_values('Before Cooldown')
        # msg = 'Started full cooldown'
        # if msg_ext:
        #     msg+=' - Comment: ' + msg_ext
        self.discord_server.send_message(msg)
        self.still_temp(self.start,still_val)
        self.mxc_temp(self.start,baseT_val)
        time.sleep(3600*2)
        self.log.write_values('Base Temperature')
        self.circulation_mode(circ_val)

    # Starts cooldown to 4K and reports when still is cold enough.
    def cooldown_4K(self,still_val,msg):
        self.log.write_values('Before Cooldown')
        # msg = 'Started cooldown to 4K'
        # if msg_ext:
        #     msg+=' - Comment: ' + msg_ext
        self.discord_server.send_message(msg)
        self.still_temp(self.start,still_val)    
    
    # starts condensing and reports when reaching base temperature
    # and then enters circulation mode
    def condense(self,baseT_val,circ_val,msg):
        # msg = 'Started mixture condensation'
        # if msg_ext:
        #     msg+=' - Comment: ' + msg_ext
        self.discord_server.send_message(msg)
        if self.mxc_temp(self.start,baseT_val):
            time.sleep(3600*2)
            self.log.write_values('Base Temperature')
            self.circulation_mode(circ_val)
    
    # Starts cold insert and reports when still is cold enough for ciculation
    # and when reaching base temperature and then enters circulation mode.
    def cold_insert(self,still_val,baseT_val,circ_val,msg):
        self.log.write_values('Save Circulation')
        # msg = 'Started cold insert'
        # if msg_ext:
        #     msg+=' - Comment: ' + msg_ext
        self.discord_server.send_message(msg)
        time.sleep(3600*3)
        self.still_temp(self.start,still_val)
        if self.mxc_temp(self.start,baseT_val):
            time.sleep(3600*2)
            self.log.write_values('Base Temperature')
            self.circulation_mode(circ_val)
    
    # Starts cold insert and reports when still is cold enough for ciculation
    # and when reaching base temperature and then enters circulation mode.
    def cold_insert_4K(self,still_val,msg):
        self.log.write_values('Save Circulation')
        # msg = 'Started cold insert to 4K'
        # if msg_ext:
        #     msg+=' - Comment: ' + msg_ext
        self.discord_server.send_message(msg)
        time.sleep(3600*3)
        self.still_temp(self.start,still_val)
    
    # Starts warm-up and reports when still is warm enough.
    def warmup(self,still_val,msg):
        self.log.write_values('Before Warmup')
        # msg = 'Started warmup'
        # if msg_ext:
        #     msg+=' - Comment: ' + msg_ext
        self.discord_server.send_message(msg)
        self.still_temp(self.start, still_val, cooling=False)
        self.log.write_values('Room Temperature')
    
    # Starts FSE warm-up.
    def fse_warmup(self,msg):
        self.log.write_values('Before FSE Warmup')
        # msg = 'FSE warmup started'
        # if msg_ext:
        #     msg+=' - Comment: ' + msg_ext
        self.discord_server.send_message(msg)

    # Returns a message, that the API was disconnected unexpectedly
    def check_disconnect(self,time=None):
        if time:
            msg_time = 'after %.2f h '
        else:
            msg_time = ''
        msg = 'Disconnected from API ' + msg_time + 'before temperature threshold was reached.'
        self.discord_server.send_message(msg)

    #%% User interface setup

    # Converts the ui input to a float if possible, otherwise return None.
    def get_cmd_value(self,msg):
        cmd = input(msg)
        if cmd:
            cmd_val = float(cmd)
        else:
            cmd_val = None
        return cmd_val
    
    def ui_snapshot(self):
        print('User selected -> Reading Snapshot')
        print('')
        status=input('Enter the current status of the cryostat (default is "Base Temperature"): ')
        print('')
        if not status: status='Base Temperature'
        self.log.write_values(status)
        print(f'Snapshot of the readings was taken with the status {status}.')
    
    def ui_circulation_mode(self):
        print(dedent('''\
                     User selected Circulation Mode
                     
                     Please enter temperature thresholds (in K) at which notifications should be sent.
                     Leave empty to use default values.'''))
        circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
        print('')
        if not circ_val: circ_val=self.def_circ_val
        self.circulation_mode(circ_val)
        
    def ui_full_cooldown(self):
        print(dedent('''\
                     User selected -> Full Cooldown
                     
                     Please enter temperature thresholds (in K) at which notifications should be sent.
                     Leave empty to use default values.'''))
        comment=input('Add comment (otherwise leave blank): ')
        still_val=self.get_cmd_value(f'Still temp before condensing (default is {self.def_still_val}): ')
        baseT_val=self.get_cmd_value(f'Base temp of MXC (default is {self.def_baseT_val}): ')
        circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
        print('')
        if not still_val: still_val=self.def_still_val
        if not baseT_val: baseT_val=self.def_baseT_val
        if not circ_val: circ_val=self.def_circ_val
        msg = 'Started full cooldown'
        if comment:
            msg+=' - Comment: ' + comment
        self.full_cooldown(still_val,baseT_val,circ_val,msg)
        
    def ui_cooldown_4K(self):
        print(dedent('''\
                     User selected Cooldown to 4K
                     
                     Please enter temperature thresholds (in K) at which notifications should be sent.
                     Leave empty to use default values.'''))
        comment=input('Add comment (otherwise leave blank): ')
        still_val=self.get_cmd_value(f'Still temp when cold (default is {self.def_still_val_4K_cd}): ')
        print('')
        if not still_val: still_val=self.def_still_val_4K_cd
        msg = 'Started cooldown to 4K'
        if comment:
            msg+=' - Comment: ' + comment
        self.cooldown_4K(still_val,msg)
        
    def ui_condense(self):
        print(dedent('''\
                     User selected Condensing
                     
                     Please enter temperature thresholds (in K) at which notifications should be sent.
                     Leave empty to use default values.'''))
        comment=input('Add comment (otherwise leave blank): ')
        baseT_val=self.get_cmd_value(f'Base temp of MXC (default is {self.def_baseT_val}): ')
        circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
        print('')
        if not baseT_val: baseT_val=self.def_baseT_val
        if not circ_val: circ_val=self.def_circ_val
        msg = 'Started mixture condensation'
        if comment:
            msg+=' - Comment: ' + comment
        self.condense(baseT_val,circ_val,msg)
        
    def ui_cold_insert(self):
        print(dedent('''\
                     User selected FSE Cold Insert
                     
                     Please enter temperature thresholds (in K) at which notifications should be sent.
                     Leave empty to use default values.'''))
        comment=input('Add comment (otherwise leave blank): ')
        still_val_coldinsert=self.get_cmd_value(f'Still temp before condensing (default is {self.def_still_val_coldinsert}): ')
        baseT_val=self.get_cmd_value(f'Base temp of MXC (default is {self.def_baseT_val}): ')
        circ_val=self.get_cmd_value(f'Warning temp during circulation (default is {self.def_circ_val}): ')
        print('')
        if not still_val_coldinsert: still_val_coldinsert=self.def_still_val_coldinsert
        if not baseT_val: baseT_val=self.def_baseT_val
        if not circ_val: circ_val=self.def_circ_val
        msg = 'Started cold insert'
        if comment:
            msg+=' - Comment: ' + comment
        self.cold_insert(still_val_coldinsert,baseT_val,circ_val,msg)
    
    def ui_cold_insert_4K(self):
        print(dedent('''\
                     User selected FSE Cold Insert 4K
                     
                     Please enter temperature thresholds (in K) at which notifications should be sent.
                     Leave empty to use default values.'''))
        comment=input('Add comment (otherwise leave blank): ')
        still_val_coldinsert=self.get_cmd_value(f'Still temp (default is {self.def_still_val_coldinsert}): ')
        print('')
        if not still_val_coldinsert: still_val_coldinsert=self.def_still_val_coldinsert
        msg = 'Started cold insert to 4K'
        if comment:
            msg+=' - Comment: ' + comment
        self.cold_insert_4K(still_val_coldinsert,msg)
    
    def ui_warmup(self):
        print(dedent('''\
                     User selected Warmup
                     
                     Please enter temperature thresholds (in K) at which notifications should be sent.
                     Leave empty to use default values.'''))
        comment=input('Add comment (otherwise leave blank): ')
        warmup_val=self.get_cmd_value(f'Still temp when warm (default is {self.def_warmup_val}): ')
        print('')
        if warmup_val: warmup_val=float(warmup_val)
        else: warmup_val=self.def_warmup_val
        msg = 'Started warmup'
        if comment:
            msg+=' - Comment: ' + comment
        self.warmup(warmup_val,msg)
        
    def ui_fse_warmup(self):
        print(dedent('''\
                     User selected FSE Warmup'''))
        comment=input('Add comment (otherwise leave blank): ')
        print('')
        msg = 'FSE warmup started'
        if comment:
            msg+=' - Comment: ' + comment
        self.fse_warmup(msg)
        
    
    #%% User interface
    
    # Runs the program interface that asks the user to select the program mode
    # and the desired temperature thresholds. The timer is started once the
    # program has been selected.
    def program_interface(self):
        
        existing_programs = {
            'Circulation Mode': self.ui_circulation_mode,
            'Full Cooldown': self.ui_full_cooldown,
            'Cooldown to 4K': self.ui_cooldown_4K,
            'Condensing': self.ui_condense,
            'FSE Cold Insert': self.ui_cold_insert,
            'FSE Cold Insert 4K': self.ui_cold_insert_4K,
            'Warmup': self.ui_warmup,
            'FSE Warmup': self.ui_fse_warmup,
            'Reading Snapshot': self.ui_snapshot,
            }
        
        print('')
        print('Available commands are:')
        [print('    '+str(i+1)+' -> '+program) for i,program in enumerate(self.user_available_programs)];
        print('    Nothing -> Exit')
        cmd=input('Please select which program to start: ')
        print('')
        self.start = time.time()
        
        if not cmd:
            print('User quited the program')
            return
        try:
            program_nr = int(cmd)-1
            if program_nr in range(len(self.user_available_programs)):
                program = self.user_available_programs[program_nr]
                existing_programs[program]()
            else:
                print(f'User input {cmd} is invalid.')
                print('')
        except KeyboardInterrupt:
            print('User interrupted the program.')
        except Exception:
            traceback.print_exc()
            print(f'User input {cmd} is invalid.')
            print('')
            
        self.program_interface()

# Run the interface
ui = UI()
ui.program_interface()



