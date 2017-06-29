# How to create a linux distributiuon.

This script is used to create a binary distribution for Linux (Ubuntu) Systems.
In order to create a distribution follow the steps below.

1. ** Install Dependencies.**  We have a python script that generates the binary. We will need python 2.7 or above. And, `pyinstaller` package for the python version chosen. Use ` python -m pip install pyinstaller`
2. ** Run pyinstaller.** Create a folder. Place the vriot_bdister.py along with a vriot docker image in that folder. From within the folder (the folder you just created as working directory), run pyinstaller using `pyinstaller -F --add-data '<image_file_name>:.' vriot_bdister.py`

Upon followig the two steps above, pyinstaller shall create a linux binary executable file in the dist folder of your working directory. This shall be a single file that you can give it away to people wanting to install vriot on their systems.


Notes from the Demo

1. Creating an installer
    1. Requires: System with docker, and python and pip, virtualenv
    2. create a new folder, place runscript script and the installer script.
    3. Get the latest or release image from docker. (Make sure proper version number is tagged. Else, retag.)
    4. save the image as image.tar in the folder
    5. run pyinstaller to convert the installer script into executable
2. Running an installer
    1. Works with / without docker installed. So, demo after uninstalling docker.
    2. Expect, installer to install docker, add image, place the service script, create config file.
    3. In the machine to be installed, copy the installer
    4. run the installer with -v to show volume
3. Service running on a Machine
    1. Reboot
