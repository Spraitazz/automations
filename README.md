
# automations

A python wrapper for running persistent automations.


## Description

What it does - provided automation name, config, run() method, it:
    1. Persistently runs automation, wrapping run in try catch with basic email and restart handling
    2. Deals with logs, control automations through terminal


## Getting Started

### Dependencies


sudo apt install xvfb
pip install xvfbwrapper

### Installing

Tested on Ubuntu 20.04 

* Installation instructions:

1. Set up (python) virtual environment
    conda env create -f conda_env.yml
    conda activate automations

2. Run ./setup.sh

### Usage

1. automations list 
2. automations start/stop automation_name 








