# Script works only on Linux platforms.
# This shall be run from the root of the VRIOT repo folder
from subprocess import call, Popen, PIPE
import os
from image_gen import ImageGen
from image_push import ImagePush


def build():
    # if built in ci these variables form appropriate tag.
    # else a default oooo.____.UT will be created
    circle_ci_build = os.environ.get("CIRCLE_BUILD_NUM", "UT")
    git_user = os.environ.get("CIRCLE_USERNAME", "___")[:3]
    git_commit = os.environ.get("CIRCLE_SHA1", "oooo")[:4]
    git_branch = os.environ.get("CIRCLE_BRANCH", "local")
    git_tag = os.environ.get("CIRCLE_TAG", "local")
    # appropriate tag forms
    docker_tag = git_commit+'.'+git_user+'.'+circle_ci_build

    # create required  directories
    print('creating directories..')
    call(['mkdir', '-p', 'vriot-builder'])
    call(['mkdir', '-p', 'vriot-builder/certs'])
    call(['mkdir', '-p', 'vriot-builder/oldlogs'])
    # copy content to required folder structure
    print('Adding content to directories..')
    call(['cp', '-r', 'VRIOT', 'vriot-builder'])
    call(
        ['cp',
         'VRIOT/ops/docker/global_container/Dockerfile',
         'vriot-builder'])
    # Create Mosquitto Config file
    print('creating mosquitto.conf ..')
    call(
        ['cp',
         'VRIOT/ops/configurations/'+git_branch+'/mosquitto.conf',
         'vriot-builder/mosquitto.conf'])

    # Create Mongo DB config file
    print('creating mongo.conf ..')
    call(
        ['cp',
         'VRIOT/ops/configurations/'+git_branch+'/mongod.conf',
         'vriot-builder/mongod.conf'])

    print('creating logrotate.conf ..')
    call(
        ['cp',
         'VRIOT/ops/configurations/'+git_branch+'/logrotate.conf',
         'vriot-builder/logrotate.conf'])

    print('copying logrotate.d ..')
    call(
        ['cp',
         '-rf',
         'VRIOT/ops/configurations/'+git_branch+'/logrotate.d',
         'vriot-builder/logrotate.d'])

    # Create nginx config file
    print('creating nginx.conf ..')
    call(
        ['cp',
         'VRIOT/ops/configurations/' + git_branch + '/nginx.conf',
         'vriot-builder/nginx.conf'])

    # create cert files.
    print('creating certs..')
    f = open('vriot-builder/certs/ca.crt', 'w')
    f.write(CA_CRT)
    f.close()
    f = open('vriot-builder/certs/ca.key', 'w')
    f.write(CA_KEY)
    f.close()
    f = open('vriot-builder/certs/server.key', 'w')
    f.write(SERVER_KEY)
    f.close()
    f = open('vriot-builder/certs/server.crt', 'w')
    f.write(SERVER_CRT)
    f.close()

    # Build the container.
    print('Building Image..')
    call(['docker', 'build', '-t', 'vriothub/comprehensive:'+docker_tag,
          'vriot-builder/'])

    # clean up the temp folder
    print('Cleaning up directories..')
    call(['rm', '-rf', 'vriot-builder'])

    if  git_branch == 'local':
        # don't try to create installer for local builds.
        return

    img_gen = ImageGen()
    # Create Installer package
    print('Generating Installer..')
    # Get the docker image id and save it as tar
    a = Popen(['docker', 'images'], stdout=PIPE, stdin=PIPE)
    b = Popen(['grep', 'vriothub/comprehensive'], stdin=a.stdout, stdout=PIPE)
    c = Popen(["awk '{{print $3}}'"], stdin=b.stdout, stdout=PIPE, shell=True)
    res, err = c.communicate()
    docker_img_id = res.decode('ascii').strip()
    call(['docker', 'save', '-o', 'image.tar', 'vriothub/comprehensive:'+docker_tag])
    call(['cp', 'VRIOT/ops/scripts/dockerinit', '.'])
    call(['cp', 'VRIOT/ops/scripts/installer.py', '.'])
    installer_file = img_gen.generate_installer(['installer.py', 'dockerinit', 'image.tar'])

    # Create OVA Package
    print('Generating OVA..')
    img_file = img_gen.generate_raw(['vriot-disk.vmdk'])
    call(['rm', '-rf', 'vriot-disk.vmdk'])
    if img_file:
        # create a mount for existing image in source
        Popen(['mount','-o','loop,offset=1048576','vriot-disk.img','/mnt/']).wait()
        # Copy VRIOT into the mount
        call(['cp','VRIOT','/mnt/'])
        # Copy init script to /etc/init.d
        call (['cp','VRIOT/ops/scripts/vminit','/mnt/etc/init.d/vriot'])
        # Unmount the image.
        call(['umount','/mnt'])

    print('Converting raw image to vmdk..')
    vmdk_file = img_gen.generate_vmdk(['vriot-disk.img'])
    if vmdk_file:
        print('Converting vmdk to ova..')
        call(['cp', 'VRIOT/ops/scripts/ovf_template', '.'])
        ova_file = img_gen.generate_ova(['vriot-disk.vmdk'])

    # Start pushing the images to S3
    img_push = ImagePush()

    if git_tag == "local":
        image_path = "{}.{}.{}".format(git_commit, git_branch, circle_ci_build)
    else:
        image_path = git_tag

    files_to_push = []
    base_image_name = "vriot-{}.".format(image_path)
    if installer_file:
        file = base_image_name+'installer'
        call(['mv','image.installer',file])
        files_to_push.append(file)
    if ova_file:
        file = base_image_name+'ova'
        call(['mv','vriot-disk.ova',file])
        files_to_push.append(file)
    if vmdk_file:
        file = base_image_name+'vmdk'
        call(['mv','vriot-disk.vmdk',file])
        files_to_push.append(file)

    img_push.upload(git_branch, image_path, files_to_push)

SERVER_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAx66VnnxcvoPuA/+T+i8NeIvh2QzAQa+YmxYns0Id6ag+0oGT
NNnN/H2+ylK84fIrM4587sW7xzytRld7pkZAZHrFdtVnMZFSxKLHfAFqUDUe2Ujp
warlLniFfiZP9NGMdX7A0U15yUonx5ice4GpqIys+ZvEbcSJvz5SQmU116aAa3Pw
QN2Whrta0qCNVQh6XjH1eNwSrVhWuMo5ewlhZNjtNQGVz/5tVcGCtIrpwoVyYOAS
Qcds0TBkcGMbw7IWevQPaymqHinc7wK62JmZ+lRf5yWAHSLj/Z15WoP13GG02VTF
FFLV9inTF4GtKDjXGhyiAV57bfU3UJegparwjQIDAQABAoIBAD2PCPkvBbiGG56H
8Cq0zsZW+W1cjPizFazaC6sruuUJxTRIVgV5EBPDAEqHb0uIyODAEKvbsaQehJym
46vDBJ71amLUL1gMoSOVu0Hzfb70YWpDHC1kbfsBlMXrMcMbxt2CEhd0dxMjFVhn
J/a7Zn5bwAfDia79ZCndIKbvZMXyNtoSK16JekVwhEYfQ3p7IDkY8F1PPfrWADIj
en0XpFhopDqUonq+hCUJpjKUjJWGF+xkhyTQRDKRSuN3DGDVEm8+umT8QEA4foCK
GhpRTsmaI6uE4pNGfpnCaGx5X36Jf/w+slJS7CaxsAy+7CEuikNgNE3rlBVFac4i
whqcYgECgYEA9FGIa/CGfvqzheGBTO8AeiUBeQhKJfERmisIrc8/LmMvZmHlrtxR
9WTNXSPF4Nxj4U4Bcqxv8cXfEUays29wfmvUqbYNsXjICyGahy+C0xpudaBlLRnW
kZUwYY75LW1FyYyDHSJo2BOmy3x71wTn70kPSgJS+iKVybeFMIErq+0CgYEA0Tqy
77PFA2OM2mHY1SGTfzt0leehI39bBaMMCqzttbenCP0QSEVprq8+6fWYFulxONqO
GAo5aay5aMt+122HV9bzfCnmbzAKnDehiqCU6bUpGs9IyYH9/itkGCn+FlXBRBMb
ke+EI16pdp8KLyLTeNjgcU+U7pth32MWY2deAyECgYEAmuOFpUibO60cWugX3Po4
Rzdms6B5wYwPKLnXirk0yOfAiRvPTQgIPZZmS4H+VQvjllapvFVtss1LGdzENdWU
b9FUxTLRg42a5NOs779DJSpAlPnWqr0StsDqJy9I8W+xKpGWHcZOyY3L1H1a1Xoa
wCyFMNpAWKvMYlGicpmxYhECgYB4jnwABfNlCn1kb7DCzb/xNc7teTOuAnnt+466
r/2gERwb38T7/5LvZma35B0oRoZInhX14B5It491xJtngeLUSDSvvGzccDAM5zkb
aX+kUhBHNFzaTx6Mz2+zRK71K6Bamy/tnLbksmyuvuDdXBHBtiVM5PAJtFpmnu+N
g0f2QQKBgDLMyFnPAhDZHb7PqnlDRZctd3KpcUeKqWIWPpAV6I+HkYsCyKUgyMjk
PPCDdy4ou6t4EN5HjgA8B8e/2NmvgWIwoR9EZXL044J1qnv+ztdkxOHMgvR0WjkZ
zEw/YjNqxnLMbko2a80fDt6cRkJLATy3gMdVpjWNyAP/W2+sQcTQ
-----END RSA PRIVATE KEY-----"""

SERVER_CRT = """-----BEGIN CERTIFICATE-----
MIIDTTCCAjUCCQCZDhZJx603FTANBgkqhkiG9w0BAQsFADBkMQswCQYDVQQGEwJV
UzELMAkGA1UECAwCQ0ExEjAQBgNVBAcMCVN1bm55dmFsZTERMA8GA1UECgwIVlJJ
T1QgQ0ExDjAMBgNVBAsMBXZyaW90MREwDwYDVQQDDAhWUklPVCBDQTAeFw0xNzAz
MjAyMzU0MzNaFw0xOTEyMTUyMzU0MzNaMG0xCzAJBgNVBAYTAlVTMQswCQYDVQQI
DAJDQTESMBAGA1UEBwwJU3Vubnl2YWxlMRMwEQYDVQQKDApWcmlvdCBSa3VzMQ4w
DAYDVQQLDAV2cmlvdDEYMBYGA1UEAwwPKi52aWRlbzU0LmxvY2FsMIIBIjANBgkq
hkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx66VnnxcvoPuA/+T+i8NeIvh2QzAQa+Y
mxYns0Id6ag+0oGTNNnN/H2+ylK84fIrM4587sW7xzytRld7pkZAZHrFdtVnMZFS
xKLHfAFqUDUe2UjpwarlLniFfiZP9NGMdX7A0U15yUonx5ice4GpqIys+ZvEbcSJ
vz5SQmU116aAa3PwQN2Whrta0qCNVQh6XjH1eNwSrVhWuMo5ewlhZNjtNQGVz/5t
VcGCtIrpwoVyYOASQcds0TBkcGMbw7IWevQPaymqHinc7wK62JmZ+lRf5yWAHSLj
/Z15WoP13GG02VTFFFLV9inTF4GtKDjXGhyiAV57bfU3UJegparwjQIDAQABMA0G
CSqGSIb3DQEBCwUAA4IBAQBDnJ9IaBc/kzPUoInJ0lrHMYPx8pyHhxQJtXekAcP3
sfUU3AJY7PdeMMmhx/SJFNAtKsf5FqhgD4tglY+9/AdQ22Hj1lrTClumTVvHm5a0
457H87tjsKzRlJv5kc8p6WrSvVnRUrfOAQ1FCWEgBFhH5oyIB3UmWqt394Smh6AH
uXFMOgToHDXFdOcA+d2bW6Ew4FB8YmQ1p4UEYUPVMFGvXq1ABSoyzKE7oqKKDZ21
TTmQMYgwW0T4aWtKRkdPBmwAFqO4iS7upt20szJVVbfrobpjKK2AJr4PZnmBMgMl
62ROBaQyLZXl0eu7TcHq4hJAFWDEWipv/JgEI9MMpYel
-----END CERTIFICATE-----
"""

CA_CRT = """-----BEGIN CERTIFICATE-----
MIIDdTCCAt6gAwIBAgIJAIf/QbEgk+MGMA0GCSqGSIb3DQEBBQUAMIGEMQswCQYD
VQQGEwJVUzELMAkGA1UECBMCQ0ExEjAQBgNVBAcTCVN1bm55dmFsZTERMA8GA1UE
ChMIUnVja3VzQ0ExDjAMBgNVBAsTBXZyaW90MQ8wDQYDVQQDEwZSdWNrdXMxIDAe
BgkqhkiG9w0BCQEWEXZzeWVkQGJyb2NhZGUuY29tMB4XDTE3MDQyMDIzNTc1NloX
DTI3MDQxODIzNTc1NlowgYQxCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJDQTESMBAG
A1UEBxMJU3Vubnl2YWxlMREwDwYDVQQKEwhSdWNrdXNDQTEOMAwGA1UECxMFdnJp
b3QxDzANBgNVBAMTBlJ1Y2t1czEgMB4GCSqGSIb3DQEJARYRdnN5ZWRAYnJvY2Fk
ZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAMXNH6S2yOVQTrn90tdQ
ULfl9JsoJth31iVcVqHSk4hMy1VjmpNVP9eU9p5kLMuSbYQDYE6z3+YmKcB5cJPI
imQnZ4iRhfffAb0/97TfFT9gm+PiZrXjCa5WMVNyQVm6QtTq3CV8q2DDFCfAFg3R
5xEasZfQuMIXH3LOk68E6Z6rAgMBAAGjgewwgekwHQYDVR0OBBYEFEnbScfhSgGt
OBp6ijgMY6K1fkIKMIG5BgNVHSMEgbEwga6AFEnbScfhSgGtOBp6ijgMY6K1fkIK
oYGKpIGHMIGEMQswCQYDVQQGEwJVUzELMAkGA1UECBMCQ0ExEjAQBgNVBAcTCVN1
bm55dmFsZTERMA8GA1UEChMIUnVja3VzQ0ExDjAMBgNVBAsTBXZyaW90MQ8wDQYD
VQQDEwZSdWNrdXMxIDAeBgkqhkiG9w0BCQEWEXZzeWVkQGJyb2NhZGUuY29tggkA
h/9BsSCT4wYwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQUFAAOBgQA9rrFB0dX1
0odlcNLGFEDiQziI/4bKo6DgCtLSOl7So8lNdsSKxAQlncOC6uJjPRNdnLCMBVkr
1PtLx4Q656QI1DfUom9LFueJ1TITT4xu7OgBC+r3gMrX9WeTkBeb8EfOGLYvWf8G
C3hRBj6VaYVLL4S1eFywGmVNg3w4wMJToA==
-----END CERTIFICATE-----"""

CA_KEY = """-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3-CBC,1AEA579C4B7326DB

fACNJRpUT8SDeVFn2xpoPiov9sRQkTMnbBMqg2bkYcdZyVZfHlBtSjFffjzpokKf
nU7LtcRZ44zIsjw1XxI/2eF1V+lOCDsEmvYfh6Fh5XNTEEv5FWzbhVgMmoazCCGL
AfQzrkxpqUIKof9zE5A5lNOOy4Y1tlidIwbWwjVDf6BzzShgmpSH25N2Ulq/XUCN
SP4ag3cPAt7vnYoXJEHKqqAaqTQiikAtvHoxcEINvvs9FUubHA+GzG/tuIPar6lf
nuZ3jgHVdIQ6AKzjDIwFCojmGrOqwppfTSyBwhgY8Vb4WUFzR2nzXfMnuE0QUbWW
GXkdOVJl7PPztH5B3QTdKlgBO6+uvb1AviM3nsbhuNEEqDQSiQXIoquwjwdVcq1D
BS+EA2MUt3ToLIn/AbekDsFZGAXyAQ+BUENOYyU7JJ621ZuDWtSSsW4jw1cqiHV1
EqaV/0XbG+De8XaHYlrPKi3h3ShgVRbb8UUfMLOexVIt2+HmVSXkHd0WCrxFBc/0
BUCOghQgZDvemljMUHfY+PO9t9CPt4EEDv5SLrgeKiaC/kebRmSyy6JgfBE7PWzA
j8s0q0bVnclPUlAO8wcKxefzA7pfAItF4n8IVjJ+RMJzIT/a7qByIyh8mMDXqARs
hTciMYVDKgqqwJ1yK+g7S6CsSNg3OMl72Zslv2xDJsWac0Ydj1AGbhSiC2iXnLNy
kK1DQ4fNqQdqlZSniTu3n2iW+gHptpWDxins8ICa0JC0y8mBtIE3+HOCBz/4HWn3
T09rf606cIzBzuac/pl9Zm33Xhx/dDjlNFiHRHg/KT3G8w9YbWeCEw==
-----END RSA PRIVATE KEY-----"""

if __name__ == '__main__':
    build()

