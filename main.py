import requests
import json
import inspect

import rasp_cluster.services.service_discovery as d
import rasp_cluster.services.service_configurator as c
import rasp_cluster.services.service_connector as con
import rasp_cluster.services.cluster_publisher as pub
import rasp_cluster.services.cluster_subscriber as sub
import rasp_cluster.services.service_registry_share as share

services = [
    sub,
    pub,
    share,
    c,
    con,
    d
]

def deploy(ip, port, auth, module):
    config  = module.config
    config.pop('handler', None)
    config['module'] = "".join(inspect.getsourcelines(module)[0])
    msg = json.dumps(config)
    url = "http://%s:%s/builtin/service_starter" % (ip, port)
    r = requests.post(url, data={'config': msg, 'authentication': auth})
    print(r.status_code, r.reason, r.text)


file = open('rasp_cluster/auth.key', 'r')
auth = file.read()
file.close()
for service in services:
    deploy('192.168.2.1', 8080, auth, service)

