# Cryostat monitoring
Cryostat monitoring is a program that monitors cooldown and warmup processes and
sends messages on a Discord channel when the desired temperatures have been reached.


## Installation
Install the necessary packages:

pip install -r requirements.txt

Configure the config.ini file. You can start from config_template.ini and change
the MQTT hostname to the IP address of your specific temperature controller API.
Then, enter the URL of the Discord channel to which you want to send the messages
as well as the access token of the Discord user you want to send them with.
Infos about how to find the channel id and the access token can be found here:
[Video](https://youtu.be/DArlLAq56Mo)

If you want, you can also change the default threshold temperatures for the
different steps during the cooldown and warmup processes.


## Usage
Open a terminal, change to the directory of the program and run:
python cryostat_monitoring.py

It will start a simple user interface that asks you to choose which
program mode you want to start. The available modes are:
1. Full Cooldown
2. Cooldown to 4K
3. Warmup
4. Condensing
5. Cold Insert
6. Circulation Mode

These modes all monitor the temperatures until they reach the specified threshold
and then send a message. For example, Full Cooldown monitors the still temparture until
it is cold enough for condensation, then the MXC until it reaches base temperature.
After that, it enters a Circulation Mode, which continually monitors the MXC temperature
and return a warning when it heats up too much.

### Setup a batch file
To make it easier to run the program, you can create a simple batch file.
If you use an anaconda environment,c reate a .bat file that contains:
cd <Path to the program>
call C:\Users\<Username>\Anaconda3\Scripts\activate.bat base
call cryostat_monitoring.py

