"""

Image Generation Framework
==========================

This part of code, will be used to generate an OVA image.
I/P image types: VMDK, OVA, FILES.
O/P image types: VMDK, OVA, INSTALLER.

Contact: Siby Mathew siby.mathew@ruckuswireless.com
Copyright (C) 2017 Ruckus Wireless, Inc.
All Rights Reserved.

"""

from subprocess import call, Popen, PIPE
import re
import os


class ImageGen(object):
    def __init__(self):
        #QEMU
        self.QEMU_PKG = 'qemu-utils'
        self.QEMU_RAW2VMDK = ['sudo', 'qemu-img', 'convert', '-f', 'raw', '-O', 'vmdk', '-o', 'adapter_type=lsilogic,subformat=streamOptimized,compat6']
        self.QEMU_VMDK2RAW = ['qemu-img', 'convert', '-f', 'vmdk', '-O', 'raw']

        #PYINSTALLER
        self.PYINSTALLER_PKG = 'pyinstaller'
        self.PYINSTALLER_CMD = ['pyinstaller', '--clean', '-F']

        #OVA
        self.OVA_PKG = ['tar', 'openssl']

        #FileTypes
        self.VMDK = 'vmdk'
        self.RAW = 'img'
        self.INSTALLER = 'installer'
        self.OVA = 'ova'

    def check_package(self, package):
        hdlr = Popen(['apt', '-qq', 'list', package], stdout=PIPE, stderr=PIPE)
        o, e = hdlr.communicate()

        pkg = re.compile('.*({}).*'.format(package))
        if re.search(pkg, str(o)):
            return True

        hdlr = Popen(['which', package], stdout=PIPE, stderr=PIPE)
        o, e = hdlr.communicate()

        pkg = re.compile('.*({}).*'.format(package))
        print(str(o))
        if re.search(pkg, str(o)):
            return True

        return False

    def check_files(self, files, type):
        if type == "vmdk":
            if not len(files) == 1:
                return False
            if not re.search(r'.*\.img$', files[0]):
                return False
            return True
        elif type == "img" or type == "ova":
            if not len(files) == 1:
                return False
            if not re.search(r'.*\.vmdk$', files[0]):
                return False
            return True
        elif type == "installer":
            if not len(files) == 3:
                return False
            for file in files:
                if re.search(r'.*\.tar$', file):
                    self.docker_image = file
                elif re.search(r'.*\.py$', file):
                    self.installer_script = file
                else:
                    self.init_script = file
            if not self.docker_image or not self.installer_script:
                return False
            else:
                return True

    def generate_vmdk(self, iFiles=[]):
        if not self.check_package(self.QEMU_PKG):
            return False

        if not isinstance(iFiles, list) or not iFiles:
            return False

        if not self.check_files(iFiles, self.VMDK):
            return False
        else:
            oFile = iFiles[0].replace('.img', '.vmdk')

        command = []
        self.command = list(self.QEMU_RAW2VMDK)
        self.command.extend([iFiles[0], oFile])
        if not call(self.command):
            return False

        return oFile

    def generate_raw(self, iFiles=[]):
        if not self.check_package(self.QEMU_PKG):
            return False

        if not isinstance(iFiles, list) or not iFiles:
            return False

        if not self.check_files(iFiles, self.RAW):
            return False
        else:
            oFile = iFiles[0].replace('.vmdk', '.img')

        command = []
        self.command = list(self.QEMU_VMDK2RAW)
        self.command.extend([iFiles[0], oFile])
        if not call(self.command):
            return False

        return oFile

    def generate_installer(self, iFiles=[]):
        if not self.check_package(self.PYINSTALLER_PKG):
            return False

        if not isinstance(iFiles, list) or not iFiles:
            return False

        if not self.check_files(iFiles, self.INSTALLER):
            return False
        else:
            oFile = self.docker_image.replace('.tar', '.installer')
            docker_image = "{}:.".format(self.docker_image)
            init_script = "{}:.".format(self.init_script)
            binary_location = "dist/{}".format(self.installer_script.replace(".py",""))

        command = []
        self.command = list(self.PYINSTALLER_CMD)
        self.command.extend(['--add-data', docker_image, '--add-data', init_script, self.installer_script])
        call(self.command)
        call(['cp', binary_location, oFile])
        call(['rm', '-rf', 'build', 'dist'])

        return oFile

    def generate_ova(self, iFiles=[], **ovf_args):
        for pkg in self.OVA_PKG:
            if not self.check_package(pkg):
                return False

        if not isinstance(iFiles, list) or not iFiles:
            return False

        if not self.check_files(iFiles, self.OVA):
            return False
        else:
            filesize = str(os.path.getsize(iFiles[0]))
            oFile = iFiles[0].replace('.vmdk', '.ova')
            mfFile = iFiles[0].replace('.vmdk', '.mf')
            ovfFile = iFiles[0].replace('.vmdk', '.ovf')

        cpu = str(ovf_args.get('cpu', 4))
        ram = str(ovf_args.get('ram', 8))
        hdd = str(ovf_args.get('hdd', 8))

        #Bug Fix for VMWare https://bugs.launchpad.net/ubuntu/+source/qemu/+bug/1646240
        command = "sudo printf '\x03' | sudo dd conv=notrunc of=" + iFiles[0] + " bs=1 seek=$((0x4))"
        os.system(command)

        #Generate the OVF from ovf_template
        rhdlr = open("ovf_template", 'r')
        whdlr = open(ovfFile, 'w')
        for lines in rhdlr.readlines():
            lines = lines.replace("VRIOT_VMDK_FILENAME", iFiles[0])
            lines = lines.replace("VRIOT_VMDK_FILESIZE", filesize)
            lines = lines.replace("VRIOT_HDD_SIZE", hdd)
            lines = lines.replace("VRIOT_CPU_COUNT", cpu)
            lines = lines.replace("VRIOT_RAM_SIZE", ram)

            whdlr.write(lines)
        rhdlr.close()
        whdlr.close()

        #Generate SHA1
        whdlr = open(mfFile, 'w')
        call(['openssl', 'dgst', '-sha1', ovfFile], stdout=whdlr)
        call(['openssl', 'dgst', '-sha1', iFiles[0]], stdout=whdlr)
        whdlr.close()

        #Generate OVA
        call(['tar', '-cf', oFile, ovfFile, iFiles[0], mfFile])

        return oFile
