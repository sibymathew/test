#!/usr/bin/python
import optparse
import re
import os
from subprocess import Popen,call


SUPERVISORD_CONF_PATH = '/etc/supervisord.conf'
WEBAPP_PATH = '/VRIOT/ops/docker/webservice/web.py'

def main():
    # if supervisord.conf exists, start supervisor
    if os.path.isfile(SUPERVISORD_CONF_PATH):
        print ("The Supervisor conf exists..")
        Popen(['/usr/bin/supervisord','-c',SUPERVISORD_CONF_PATH])
        
    print ('Please visit localhost:5216 or <hostname>:5216 using a web '+
              'browser to start services.\n\n')
    call(['/usr/bin/python3.5',WEBAPP_PATH])

if __name__ == '__main__':
    main()
