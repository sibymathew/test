import subprocess
import os
import sys
import optparse

def main():
    # check for platform
    import platform
    if platform.system() == 'Linux':
        runLinuxInstallation()
    elif platform.system() == 'Darwin':
        runMacOSInstallation()
    elif platform.system() == 'Windows':
        runWindowsInstallation()
    # exit()
    return 0


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def runLinuxInstallation():
    from subprocess import call, Popen
    import optparse

    usage = """
    
    vriot -v <path>

    Please provide valid path to data base volume.
    Data base volume is where all the data will be stored.
    Please ensure you have appropriate permission to read and 
    write at the path provided.

    """
    p = optparse.OptionParser(usage)
    p.add_option('-v',dest='db_path',
                 help="File path for DB volume")
    (optionz, args) = p.parse_args()

    # Check if the path folder exists.
    if not optionz.db_path:
        p.error('DB Volume path not provided')
    print optionz.db_path
    print args
    (path_head, path_tail) = os.path.split(optionz.db_path)

    if not os.path.exists(path_head):
        p.error(path_head + ' does not exist.'+
                'Please create appropriate folders')

    try :
        f = open('/vriot.conf','w')
        f.write('DB-Storage-Path:'+optionz.db_path+'\n')
        f.close()
    except :
        print(
            'Unable to create file at / path. vriot needs access to '
            'this path to create configuration files.')

    call(['apt-get', 'update'])
    call(['apt-get', 'install', '-y', 'docker.io'])
    print('loading docker')
    call(['docker', 'load','-i', resource_path('image.tar')])

    # creating init script and vriot as a service
    call(['cp',resource_path('dockerinit'),'/etc/init.d/vriot'])
    call(['chmod','+x','/etc/init.d/vriot'])
    call(['update-rc.d','vriot','defaults'])
    call(['systemctl','daemon-reload'])
    print('Installation complete. Please Reboot system.')
    

def runMacOSInstallation():
    pass


def runWindowsInstallation():
    pass


if __name__ == '__main__':
    main()
