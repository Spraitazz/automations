
# automations

A wrapper for running persistent python automations.


## Description

What it does - provided automation config and run() method, it:

* persistently runs automation, wrapping run in try catch with basic email and restart handling
* deals with logs, control automations, communication with automation through any terminal (systemd.service running socket server)


## Setup

Tested on linux mint 22.1 (xfce)

What you need:

* (mini)conda with its binary in your PATH (tested version 25.3.1) 
* xvfb (sudo apt install xvfb)

after you git clone the project, in project root directory:

conda env create -f environment.yml
mkdir logs

modify the "config_fpath" variable in definitions.py to point to your controller config,
a sufficient example is in configs/controller_example.ini


### Configure automations

For the example "skelbiu" automation included (see configs/skelbiu_example.ini for an example of a sufficient config),
modify the entry for skelbiu at the top of controller.py to point correctly to your config file, and modify there whether you want it to run on startup. 

---------------------------------------------------
Finally
---------------------------------------------------

./setup.sh
source ~/.bashrc

and, if you want to start an automation, just type: "automations start automation_name"
---------------------------------------------------
Note:

Any changes to the configuration in controller.py (or any files affecting automations
except for config.ini files, for which it is enough to stop/start the automation) need to be followed by
./cleanup and ./setup (note: this will kill all running automations)



### Commands


* automations start/stop automation_name
* automations list



