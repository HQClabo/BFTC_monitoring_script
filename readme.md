# Cryostat monitoring
Cryostat monitoring is a program that monitors cooldown and warmup processes and
sends messages on a Discord channel when the desired temperatures have been reached.
A logging functionality is also implemented, which is separated in two different types
of log files. One contains information about the status of the cryostat (cooldown times,
warm up time etc.), the other contains snapshots of the sensor readings at important moments.


## Installation
Clone this github repository to the cryostat control computer.
Run python and install the required packages by running:
```
pip install -r requirements.txt
```

Create the following folders inside the folder of the repository:
```
logfiles/
    readings/
    status/
```
The log files will be created automatically, but not the directories.


## Config file
The config file contains the necessary information about the system. The available template
should be adapted by the user to the specific system and then saved as config.ini in the
folder of the program. The config file is organized in several sections. The user should
check and adjust the following entries:
 - Default temperatures for monitoring in the different program modes
 - Temperature sensor channels for magnet or FSE sensor if available
 - Adjust the still and MXC sensor channels if necessary
 - File path of the Bluefors log files
 - The list of avaliable program modes
 - The hostname (ip address) of the Bluefors temperature controller
 - the Discord server address and access token
	
Infos about how to find the channel id and the access token can be found here:
[Video](https://youtu.be/DArlLAq56Mo)


## Usage
Open a terminal, change to the directory of the program and run:
```
cd <Path-to-the-program>
python cryostat_monitoring.py
```

It will start a simple user interface that asks you to choose which
program mode you want to start. The modes currently available are:
 - Description of the program modes
 - Full Cooldown
 - Cooldown to 4K
 - Warmup
 - Condensing
 - FSE Cold Insert
 - FSE Cold Insert 4K
 - FSE Warmup
 - Circulation Mode
 - Reading Snapshot

These modes (except for Description and Reading Snapshot) monitor the temperatures until they reach the
specified threshold and then send a message. For example, Full Cooldown monitors the
still temparture until it is cold enough for condensation, then the MXC until it reaches
base temperature. After that, it enters a Circulation Mode, which continually monitors
the MXC temperature and return a warning when it heats up too much. The modes visible in
the terminal ui and their specific order can be changed in the config file.


## Setup a batch file
To make it easier to run the program, you can create a simple batch file.
If you use an anaconda environment, create a .bat file that contains:
```
cd <Path-to-the-program>
call <Path-to-anaconda>\Scripts\activate.bat <environment-name>
python cryostat_monitoring.py
```
Adjust the second line if you use a different kind of python environment or remove it
entirely if you just use plain python.

It can be convenient to run the pyhton script in an infinite loop, so the terminal does
not close when there is an error. You can do this in the following way:
```
cd <Path-to-the-program>
call <Path-to-anaconda>\Scripts\activate.bat <environment-name>
:start
python cryostat_monitoring.py
goto start
```

## Troubleshooting

### Script does not start properly
If the script crashes in the beginning, verify the following things
 - The Bluefors control software has access
 to the BFTC and that the ip address of the BFTC in the config.ini is correct
 - The config.ini does not have any syntax errors
 (compare with the shape of the config_template.ini in the reopository)
 - The path to the Bluefors log data is correct
 - The directories for the logfiles exist

### The script is stuck
If the script is stuck in an infinite loop even though the temperature threshold has been reached already,
check that the temperature sensor channels in the config.ini correspond to the ones you see on the BFTC interface.
If is waiting for the wrong channel, it will not obtain the correct information (or none at all) and will be
stuck waiting for the temperature to reach the threshold.
