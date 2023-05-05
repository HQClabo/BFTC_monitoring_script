# Cryostat monitoring
Cryostat monitoring is a program that monitors cooldown and warmup processes and
sends messages on a Discord channel when the desired temperatures have been reached.
A logging functionality is also implemented, which is separated in two different types
of log files. One contains information about the status of the cryostat (cooldown times,
warm up time etc.), the other contains snapshots of the sensor readings at important moments.


## Installation
Install the necessary packages by running:

pip install -r requirements.txt


## Config file
The config file contains the necessary information about the system. The available template
should be adapted by the user to the specific system and then saved as config.ini in the
folder of the program. The config file is organized in several sections. The user should
check and adjust the following entries:
 - Default temperatures for monitoring in the different program modes
 - Temperature sensor channels for magnet or FSE sensor if available
 - File path of the Bluefors log files
 - The list of avaliable program modes
 - The hostname of the Bluefors temperature controller
 - the Discord server address and access token
	
Infos about how to find the channel id and the access token can be found here:
[Video](https://youtu.be/DArlLAq56Mo)


## Usage
Open a terminal, change to the directory of the program and run:
python cryostat_monitoring.py

It will start a simple user interface that asks you to choose which
program mode you want to start. The modes currently available are:
	Full Cooldown
        Cooldown to 4K
        Warmup
        Condensing
        FSE Cold Insert
        FSE Cold Insert 4K
        FSE Warmup
        Circulation Mode
	Reading Snapshot

These modes (except for Reading Snapshot) monitor the temperatures until they reach the
specified threshold and then send a message. For example, Full Cooldown monitors the
still temparture until it is cold enough for condensation, then the MXC until it reaches
base temperature. After that, it enters a Circulation Mode, which continually monitors
the MXC temperature and return a warning when it heats up too much. The modes visible in
the terminal ui and their specific order can be changed in the config file.


## Setup a batch file
To make it easier to run the program, you can create a simple batch file.
If you use an anaconda environment, create a .bat file that contains:
cd <Path to the program>
call C:\Users\<Username>\Anaconda3\Scripts\activate.bat base
call cryostat_monitoring.py

