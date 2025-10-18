For automation-specific config, see example config file 'skelbiu.ini'

You might have the # character in your password, in which case in the
config.ini file you can escape it like so:

PASS = "3MYFi4^nMs#X2Z"

then, when loading the config, make sure to strip the "" like so:

config = configparser.ConfigParser(interpolation=None)
PASS = config['DEFAULT']['PASS'].strip('"')