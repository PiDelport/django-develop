import sys

if sys.version_info < (3,):
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser
