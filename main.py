# import requests
# import json
# import cPickle as pickle

from services.service_discovery import config as d
from services.service_configurator import config as c
from services.service_connector import config as con
from services.cluster_publisher import config as pub
from services.cluster_subscriber import config as sub
from services.service_registry_share import config as share

services = [
    sub,
    pub,
    share,
    c,
    con,
    d
]

def deploy(ip, port, auth, config):
    handler = config['handler']
    config['handler'] = pickle.dumps(handler)
    msg = json.dumps(config)
    url = "http://%s:%s/builtin/service_starter" % (ip, port)
    r = requests.post(url, data={'config': msg, 'authentication' auth})
    print(r.status_code, r.reason)


auth
for service in services:
    deploy('192.168.2.1', '8080', auth, service)

