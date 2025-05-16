
# automations

A toolkit containing a minimal llm server for running persistent automations.


## Description

What it does - provided automation name, config, run() method, it:
    1. persistently runs automation, wrapping run in try catch with basic email and restart handling
    2. contains a minimal llm server with an (Fast)API to submit, cancel and retrieve job (results)
    3. deals with logs, control automations, communication with automation through any terminal (systemd.service running socket server)


## Getting Started

### Dependencies


sudo apt install xvfb
pip install xvfbwrapper

pip install uvicorn
pip install fastapi
pip install pandas

* Describe any prerequisites, libraries, OS version, etc., needed before installing program.
* ex. Windows 10

### Installing

* How/where to download your program
* Any modifications needed to be made to files/folders

------------------
(Ubuntu 20.04) 

* Installation instructions:

1. Set up (python) virtual environment
    conda env create -f conda_env.yml
    conda activate web_automations

2. Get llama-cpp-python from pypi, ensuring the right version of glibc, openmp <---WHICH VERSIONS??
    export LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
    conda install -c conda-forge libgomp
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
    export CMAKE_ARGS="-DLLAMA_BLAS=OFF -DLLAMA_OPENBLAS=OFF"
    pip install --force-reinstall --no-cache-dir llama-cpp-python


* Tests

1. Check llama-cpp installed ok
    ldd $(find $(python -c "import llama_cpp; print(llama_cpp.__path__[0])") -name "*.so")
----------------------



### Executing program

* How to run the program
* Step-by-step bullets
```
code blocks for commands
```

## Help

No help as of yet.

## Authors

* spraitazz

## Version History

* 0.2
    * Various bug fixes and optimizations
    * See [commit change]() or See [release history]()
* 0.1
    * Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)

## Build

1. Check code style with black
2. Check types with mypy
3. Check imports with isort
4. lint with flake8
5. lint with pylint
6. test with pytest

---------------------------
TO DO:

1. # Install Xvfb if it's not installed
    sudo apt-get install xvfb

    # Start a virtual display (for example, display 99)
    # this command is most likely executed by systemd.service before controller.py is ran
    Xvfb :99 &

    # Set DISPLAY to use the virtual display
    export DISPLAY=:99

2. make easy to use chrome user profile, already with cookies accepted etc.
    web_automations start/stop driver <--- can have multiple drivers (different browser configs) e.g. start driver main_driver driver_config.ini
    web_automations start bot_name config_fname <--- this should pass driver to bot, so bot starts in new tab(s) #with multiple drivers, can pass chosen driver as arg

---------------------------
other



for comms through terminal, using systemd.service:
    socket server is in controller.py
    socket client (run/web_automations/comms.sock) is in the web_automations file (calling ./setup.py copies this file to ???)

check systemd.service status:
    systemctl status web_automations

check systemd.service logs:
    sudo journalctl -u web_automations.service -f
    journalctl --user -u automations.service -f
---------------------------
usage

1. web_automations start/stop llm_server
2. web_automations list bots
3. web automations start bot_name config_fname (config_fname is optional, otherwise will use the default set in controller.py)
4. web automations status/stop bot_name



---------------------------
setup

chmod +x setup.sh
#superuser needed for systemd service
source setup.sh 


----------------------------
cleanup

chmod +x cleanup.sh
#superuser needed for systemd service
./cleanup.sh





--------------------
requirements:

glibc >=2.32

#!/usr/bin/env python3

?? ####sudo apt-get install chromium-browser chromium-chromedriver


--------------------




