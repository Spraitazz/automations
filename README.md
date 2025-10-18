# automations

A tool for running persistent python automations with email exception 
handling and logging included. It is for linux only due 
to relying on systemd.service and Xvfb.

---------------

## Description

What the tool does:

1. Persistently runs automation, wrapping its run() method in a try/catch 
with email and restart handling for exceptions not handled by the automation.

2. Deals with logs, allows control of automations through terminal.

The user ideally only modifies the files under config to specify 
their configuration, linking their automation in config/controller.py.

After setup, a systemd user service "automations" is created. It starts 
a socket server on which the user communicates with the automation 
controller through the terminal.
```bash
automations command
```

An example Selenium web automation is provided in *automations/skelbiu*.

-----------------------

## Setup Instructions

Tested on Ubuntu 20.04.6 LTS.

### Prerequisites

- Python 3.12
- [uv](https://github.com/astral-sh/uv) package manager (uv-0.8.23 used here)
- Xvfb (Version: 2:1.20.13-1ubuntu1~20.04.20 tested)

### Setup

1. **Install uv**
   ```bash
   pip install uv
   ```

2. **Create a local virtual environment**
   ```bash
   uv venv
   ```

3. **Activate the virtual environment**

   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies with uv**
   ```bash
   uv sync
   ```

5. **Setup service**
    ```bash
    chmod +x ./setup.sh & ./setup.sh
    ```

----------------

## Usage

Get the list of automations defined and a list of those running:

```bash
automations list 
```

Start or stop an automation with name and configuration in config/controller.py:

```bash
automations start/stop name
```

On any code change, it is necessary to do ./cleanup and ./setup, otherwise 
configuration that can be applied on re-starting via terminal an individual
automation should be in external configuration files.

