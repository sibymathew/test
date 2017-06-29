import errno
import json
import os
from subprocess import Popen, call, PIPE

import validations
from flask import Flask, render_template, request, Response
from flask import redirect, url_for
from rabbitmq_settings import rabbitmq_settings
from supervisor_services import supervisor_settings

app = Flask(__name__)


def is_vm():
    import os
    return os.file.exists('/VRIOT/is_vm')


SUPERVISORD_CONF_PATH = '/etc/supervisord.conf'
VISIONLINE_IP = '/etc/visionline.conf'
USER_CONFIG_PATH = '/vriot.conf.d/user_config'
IS_VM_PATH = '/vriot.conf.d/is_vm'
IS_STARTED = False


@app.route("/start", methods=['POST'])
def service_start():
    """
        expects the domain name to be a valid hostname.
    """

    supervisor_conf = supervisor_settings['base']
    aa_ip = None

    # if SSL is turned on.
    ## parse domain name accordingly
    if 'create_ssl' in request.form and request.form.get('ssl_cn'):
        # 
        domain_name = request.form.get('ssl_cn').strip()
        f = open('/VRIOT/backend/settings/environments/default.py', 'a+')
        f.write('MQTT_SSL_ENABLED = True\n')
        f.close()
        f = open('/mqtt-broker/mosquitto.conf', 'w')
        f.write(mosquitto_conf_ssl)
        f.close()
    else:
        domain_name = 'local-mqtt.video54.local'
    # generate certs for the domain name.
    cert_generator(domain_name)
    # for wildcard domain name, add a subdomain to reach internally
    if domain_name[0] == '*':
        domain_name = 'mqtt' + domain_name[1:]

    f = open('/etc/hosts', 'a+')
    f.write('127.0.0.1    %s\n' % (domain_name))
    f.close()
    f = open('/VRIOT/backend/settings/environments/default.py', 'a+')
    f.write('\nMQTT_HOST="{}"\n'.format(domain_name))
    f.close()

    call(['cp', '/cafiles/domains/server.key', '/etc/mosquitto/certs/'])
    call(['cp', '/cafiles/domains/server.crt', '/etc/mosquitto/certs/'])
    call(['cp', '/cafiles/ca.crt', '/etc/mosquitto/certs/'])

    # Add appropriate services to supervisor configuration
    for service in supervisor_settings.keys():
        if service is 'aa_listner' and request.form.get('aa_listner'):
            # make sure there is an ip provided and it is a valid ip.
            aa_ip = request.form.get('aa_ip', '')
            if not validations.is_valid_ipv4(aa_ip):
                continue
            f = open('/VRIOT/backend/settings/environments/default.py', 'a+')
            f.write('\nVISIONLINE_SERVER="{}"\n'.format(aa_ip))
            f.close()

            f = open(VISIONLINE_IP, 'w')
            f.write(aa_ip)
            f.close()
        if service in request.form:
            supervisor_conf += supervisor_settings[service]

    # write the supervisord.conf file
    f = open(SUPERVISORD_CONF_PATH, 'w')
    f.write(supervisor_conf)
    f.close()
    f = open('/etc/rabbitmq/rabbitmq.config', 'w')
    f.write(rabbitmq_settings)
    f.close()

    process = Popen(['/usr/bin/supervisord', '-c',
                     SUPERVISORD_CONF_PATH]).pid

    return render_template('success.html', aa_ip=aa_ip,
                           domain_name=domain_name)


@app.route("/stop-vriot-service", methods=['GET'])
def stop_service():
    ## this is called by VM based vminit. 
    ## when service vriot stop is called.
    return Response(str(is_vm()), 200)


## Server side rendered HTML code server.
@app.route("/")
def index():
    if IS_STARTED:
        return redirect(url_for('.manage_page'))
    return render_template('indexv2.html', **{
        'is_vm': False, 'not_started': False})


@app.route("/manage")
def manage_page():
    # manage page is reached only when the VM is already initialized.
    # So, expect a file in User config path.
    f = open(USER_CONFIG_PATH, 'r')
    contents = json.load(f)
    f.close()

    # parse configurations.
    template_vars = {
        "ssl_enabled": contents['configurations'].get('ssl-enabled'),
        "fqdn": contents['configurations'].get('fqdn'),
        "visionline_ip": contents["configurations"].get('visionline-ip'),
        "aa_enabled": 'aa_service' in contents.get('modules_list', []),
        "hostname": contents['configurations'].get('hostname'),
        "gateway": contents['configurations'].get('gateway'),
        'ip_mode_static': False
    }

    # template_vars={
    #     "ssl_enabled":True,
    #     "fqdn":"asd.acas.asa.ass",
    #     "visionline_ip":"1232.,234.1232,123",
    #     "aa_enabled":'aa_service' in ['aa_service'],
    #     "hostname":"hosty",
    #     "gateway":"getsy",
    #     'ip_mode_static':False
    # }  


    return render_template('manage.html', **template_vars)


###########################################################################

## API related routes
@app.route("/service/status", methods=['GET'])
def service_status():
    comm = Popen(['supervisorctl', 'status', 'all'], stdout=PIPE, stderr=PIPE)
    res, err = comm.communicate()
    modulesStatuses = dict(map(lambda x: (x.split()[0], x.split()[1]),
                               res.decode('ascii').splitlines()))

    modulesTemplate = [
        {
            "name": "Nginx",
            "sname": "nginx",
            "status": "running",
            "uptime": 0
        },
        {
            "name": "Mongo DB",
            "sname": "mongodb",
            "status": "running",
            "uptime": 0
        },
        {
            "name": "MQTT Broker",
            "sname": "mqtt",
            "status": "running",
            "uptime": 0
        },

        {
            "name": "Rabbit MQ",
            "sname": "rabbitmq",
            "status": "running",
            "uptime": 0
        },
        {
            "name": "Device Manager API",
            "sname": "gunicorn",
            "status": "running",
            "uptime": 0
        },
        {
            "name": "MQTT Listener",
            "sname": "mqtt_service",
            "status": "running",
            "uptime": 0
        },

        {
            "name": "Celery",
            "sname": "celery",
            "status": "stopped",
            "uptime": 0
        },
        {
            "name": "Assa Abloy",
            "sname": "aa_service",
            "status": "running",
            "uptime": 0
        },

        {
            "name": "Auth API",
            "sname": "auth_server",
            "status": "absent",
            "uptime": 0
        },
        {
            "name": "DB Defaults Populator",
            "sname": "mongo_default_service",
            "status": "completed",
            "uptime": 0
        }
    ]

    for module in modulesTemplate:
        status = modulesStatuses.get(module['sname'], 'absent').lower()
        if status == 'exited':
            # renaming exited to completed. provides a soothing language
            status = 'completed'
        module['status'] = status

    import time
    time.sleep(1)

    responseData = {
        "modules": modulesTemplate
    }

    return Response(json.dumps(responseData), 200)


@app.route("/service/start", methods=['POST', 'PATCH'])
def service_start2():
    reqData = json.loads(request.data.decode())
    if not os.path.exists(os.path.dirname(USER_CONFIG_PATH)):
        try:
            os.makedirs(os.path.dirname(USER_CONFIG_PATH))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                return errorResponseFactory(
                    'internal error', status=500)

    if request.method == 'POST':

        # save configuration in USER_CONFIG_PATH

        f = open(USER_CONFIG_PATH,'w')
        f.write(json.dumps(reqData))

        f.close()

        # create the supervisor config. 
        supervisor_conf = supervisor_settings['base']
        aa_ip = None
        try:
            if reqData['configurations']['ssl-enabled']:
                domain_name = reqData['configurations']['fqdn']
                f = open('/VRIOT/backend/settings/environments/default.py', 'a+')
                f.write('MQTT_SSL_ENABLED = True\n')
                f.close()
                f = open('/mqtt-broker/mosquitto.conf', 'w')
                f.write(mosquitto_conf_ssl)
                f.close()
            else:
                domain_name = 'local-mqtt.video54.local'
        except KeyError:
            return errorResponseFactory(
                'improperly configured SSL Settings.', status=400)

        # generate certs for the domain name.
        cert_generator(domain_name)
        # for wildcard domain name, add a subdomain to reach internally
        if domain_name[0] == '*':
            domain_name = 'mqtt' + domain_name[1:]

        f = open('/etc/hosts', 'a+')
        f.write('127.0.0.1    %s\n' % (domain_name))
        f.close()

        f = open('/VRIOT/backend/settings/environments/default.py', 'a+')
        f.write('\nMQTT_HOST="{}"\n'.format(domain_name))
        f.close()

        call(['cp', '/cafiles/domains/server.key', '/etc/mosquitto/certs/'])
        call(['cp', '/cafiles/domains/server.crt', '/etc/mosquitto/certs/'])
        call(['cp', '/cafiles/ca.crt', '/etc/mosquitto/certs/'])

        # Add appropriate services to supervisor configuration
        for service in supervisor_settings.keys():

            # Later, add a check to make sure reqdata has modules key.
            if service in reqData['modules_list']:
                if service is 'aa_listner':
                    # make sure there is an ip provided and it is a valid ip.
                    aa_ip = reqData['configurations']['visionline-ip']
                    if not validations.is_valid_ipv4(aa_ip):
                        continue

                    # create the visionline things. 
                    f = open('/VRIOT/backend/settings/environments/default.py',
                             'a+')
                    f.write('\nVISIONLINE_SERVER="{}"\n'.format(aa_ip))
                    f.close()

                    f = open(VISIONLINE_IP, 'w')
                    f.write(aa_ip)
                    f.close()
                # for all services presend add related program section 
                # in supervisor config.
                supervisor_conf += supervisor_settings[service]

        # write the supervisord.conf file
        f = open(SUPERVISORD_CONF_PATH, 'w')
        f.write(supervisor_conf)
        f.close()
        f = open('/etc/rabbitmq/rabbitmq.config', 'w')
        f.write(rabbitmq_settings)
        f.close()

        process = Popen(['/usr/bin/supervisord', '-c',
                         SUPERVISORD_CONF_PATH]).pid

        return Response(json.dumps({
            'ok': 1,
            'pid': str(process)
        }), 200)
    elif request.method == 'PATCH':
        f = open(USER_CONFIG_PATH, 'r')
        contents = json.load(f)
        f.close()
        # should put everything into the configurations.
        # save configuration in USER_CONFIG_PATH
        f = open(USER_CONFIG_PATH, 'w')
        # expects configurations in request.
        contents['configurations'] = reqData['configurations']
        f.write(json.dumps(contents))
        f.close()

        return Response(json.dumps({"data": {
            "message": "Saved!"
        }}), 200, mimetype='application/json')


@app.route("/module/start", methods=['POST'])
def module_start():
    try:
        process = json.loads(request.data.decode())['process']
    except:
        return errorResponseFactory('bad data', status=400)

    call(['supervisorctl', 'start', process])
    return Response(json.dumps({"message": {
        "ok": 1
    }}), 200)


@app.route("/module/stop", methods=['POST'])
def module_stop():
    try:
        process = json.loads(request.data.decode())['process']
    except:
        return errorResponseFactory('bad data', status=400)

    call(['supervisorctl','stop',process])
    return Response(json.dumps({"message":{
        "ok":1
        }}),200)


@app.route("/module/restart", methods=['POST'])
def module_restart():
    try:
        process = json.loads(request.data.decode())['process']
    except:
        return errorResponseFactory('bad data', status=400)

    call(['supervisorctl', 'restart', process])
    return Response(json.dumps({"message": {
        "ok": 1
    }}), 200)


## Helper functions.
def vm_changes(config):
    for k, v in json.loads(config).items():
        reboot_flag = False
        if k == 'hostname':
            hostname_new = v
            comm = Popen(['hostname'], stdout=PIPE, stderr=PIPE)
            res, err = comm.communicate()
            hostname_old = res.decode('ascii').strip()

            if not hostname_old == hostname_new:
                command = "s/{}/{}/".format(hostname_old, hostname_new)
                call(['sed', '-i', command, '/etc/hosts'])
                call(['sed', '-i', command, '/etc/hostname'])
                reboot_flag = True
        elif k == 'npwd':
            password_new = ((v + '\n') * 2).encode('utf-8')
            admin = "vriot-admin"

            dev_null = open('/dev/null', 'w')
            comm = Popen(['passwd', admin], stdin=PIPE,
                         stdout=dev_null.fileno(), stderr=PIPE)
            res, err = comm.communicate(password_new)
        elif k == 'timezone':
            timezone_new = v
            comm = Popen([
                'timedatectl', 'status', '|',
                'grep', 'Timezone', '|',
                'awk', '-F"', '"', "'{print $2}'"
            ], stdout=PIPE, stderr=PIPE
            )
            res, err = comm.communicate()
            timezone_old = res.decode('ascii').strip()

            if not timezone_old == timezone_new:
                call(['timedatectl', 'set-timezone', timezone_new])
                reboot_flag = True
        elif k == 'dns':
            file = '/etc/network/interfaces'
            dns_servers_new = " ".join(v)
            call(['sed', '-i', 's/dns-nameservers.*//', file])

            command = "$a\\dns-nameservers {}\\".format(dns_servers_new)
            call(['sed', '-i', '-e', command, file])
            reboot_flag = True

    if reboot_flag:
        call(['reboot'])


def errorResponseFactory(msg, status=400, code=0):
    return Response(json.dumps({
        'error': {
            'message': msg,
            'code': code
        }
    }), status)


def cert_generator(domain_name):
    import os
    import hashlib
    import subprocess
    import datetime

    MYDIR = '/cafiles'
    OPENSSL = '/usr/bin/openssl'
    KEY_SIZE = 1024
    DAYS = 3650
    CA_CERT = 'ca.crt'
    CA_KEY = 'ca.key'

    # Extra X509 args. Consider using e.g. ('-passin', 'pass:blah') if your
    # CA password is 'blah'. For more information, see:
    #
    # http://www.openssl.org/docs/apps/openssl.html#PASS_PHRASE_ARGUMENTS
    X509_EXTRA_ARGS = ('-passin', 'pass:Ruckus2017')

    def openssl(*args):
        cmdline = [OPENSSL] + list(args)
        subprocess.check_call(cmdline)

    def gencert(domain, rootdir=MYDIR, keysize=KEY_SIZE, days=DAYS,
                ca_cert=CA_CERT, ca_key=CA_KEY):

        def dfile(ext):
            return os.path.join('domains', '%s.%s' % ('server', ext))

        os.chdir(rootdir)

        if not os.path.exists('domains'):
            os.mkdir('domains')

        if not os.path.exists(dfile('key')):
            openssl('genrsa', '-out', dfile('key'), str(keysize))

        config = open(dfile('config'), 'w')
        config.write(OPENSSL_CONFIG_TEMPLATE % {'domain': domain})
        config.close()

        openssl('req', '-new', '-key', dfile('key'), '-out', dfile('req'),
                '-config', dfile('config'))

        openssl('x509', '-req', '-days', str(days), '-in', dfile('req'),
                '-CA', ca_cert, '-CAkey', ca_key,
                '-set_serial',
                '0x%s' % hashlib.md5((domain +
                                      str(datetime.datetime.now())).encode('utf-8')).hexdigest(),
                '-out', dfile('crt'),
                '-extensions', 'v3_req', '-extfile', dfile('config'),
                *X509_EXTRA_ARGS)

        print("Done. The private key is at %s, the cert is at %s, and the " \
              "CA cert is at %s." % (dfile('key'), dfile('crt'), ca_cert))

    gencert(domain_name)


mosquitto_conf_ssl = """
listener 8883

cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
"""

OPENSSL_CONFIG_TEMPLATE = """prompt = no
distinguished_name = req_distinguished_name
req_extensions = v3_req

[ req_distinguished_name ]
countryName            = US
stateOrProvinceName    = CA
localityName           = Sunnyvale
0.organizationName     = Ruckus
organizationalUnitName = Ruckus Dev
commonName             = %(domain)s
emailAddress           = vsyed@brocade.com

[ v3_req ]
# Extensions to add to a certificate request
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = %(domain)s
DNS.2 = *.%(domain)s
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5216, debug=True)
