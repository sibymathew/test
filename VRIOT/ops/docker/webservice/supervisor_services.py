supervisor_settings = {
'base' : """
[unix_http_server]
file=/tmp/supervisor.sock   ; (the path to the socket file)

[inet_http_server]
port=0.0.0.0:9001

[supervisord]
nodaemon=true
logfile=/var/log/supervisord.log
loglevel=debug
logfile_maxbytes=5000000
logfile_backups=5

[supervisorctl]
serverurl = http://localhost:9001
prompt = mysupervisor

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

""",

'mqtt_listner': """
[program:mqtt_service]
user=root
directory=/VRIOT/backend/
command=python3 manage.py mqtt_service
stdout_logfile=NONE
redirect_stderr=true
priority=60
""",

'dm_api': """
[program:gunicorn]
user=root
directory=/VRIOT/backend/
command=gunicorn --workers=3 settings.wsgi:application --bind 0.0.0.0:8000
stdout_logfile=NONE
redirect_stderr=true
priority=70
""",

'celery': """
[program:celery]
user=root
directory=/VRIOT/backend/
command=celery worker -A services.integration.celery.celery -l info -Q mqtt_normal,mqtt_priority
stdout_logfile=NONE
redirect_stderr=true
priority=40
""",

'aa_listner':"""
[program:aa_service]
user=root
directory=/VRIOT/backend/
command=python3 manage.py assaabloy_service
stdout_logfile=NONE
redirect_stderr=true
""",

"rabbitmq":"""
[program:rabbitmq]
user=root
directory=/
command = rabbitmq-server start
stdout_logfile=NONE
redirect_stderr=true
priority=30
""",

'mongo_db': """
[program:mongodb]
user=root
directory=/
command=mongod --config /etc/mongod.conf
stdout_logfile=NONE
redirect_stderr=true
priority=10
""",

'mqtt_broker':"""
[program:mqtt]
user=root
directory=/mqtt-broker
command=mosquitto -c mosquitto.conf
stdout_logfile=NONE
redirect_stderr=true
priority=50
""",

'auth_api': """
[program:auth_server]
user=root
directory=/VRIOT/authServer/app
command=gunicorn baseapp.wsgi:application --bind 0.0.0.0:8080
stdout_logfile=NONE
redirect_stderr=true
""",

'mongo_defaults': """
[program:mongo_default_service]
user=root
directory=/VRIOT/backend/
command=python3 manage.py mongo_default_service
stdout_logfile=NONE
redirect_stderr=true
priority=20
""",

'nginx': """
[program:nginx]
user=root
directory=/
command=nginx
stdout_logfile=NONE
redirect_stderr=true
priority=80
""",
}