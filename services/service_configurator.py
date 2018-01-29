from a_service import RestHandler as superClass


encryption_key = None

def change_key(event):
    global encryption_key
    encryption_key = event.data

class Service(superClass):
    def initialize(self, module):
        self.module = module
        self.module.add_event_listener('PUBLISH_KEY_CHANGED', change_key)
        self.module.dispatch_event('PUBLISH_ENCRYPTION_KEY_REQUEST', None)

    def get(self):
        authentication = self.get_argument('authentication', None)
        remote_port = self.get_argument('port', None)
        remote_ip = self.request.remote_ip

        self.module.dispatch_event('REQUESTED_CONFIGURATION', (remote_ip,
                                                               remote_port,
                                                               authentication))


        if(authentication is None):
            return
        # TODO(SECURITY): This is not a good way, HASH SALT ENCRYPTION!
        if(authentication != self.module.cluster_authentication):
            return

        self.module.dispatch_event('LOG', (8, 'AUTH-OK SHARING CONFUGURATION',
                                           remote_ip, remote_port,
                                           config['service_name']))
        if(remote_port is not None):
            try:
                remote_port = int(remote_port)
            except Exception as e:
                return
            if(remote_port <= 0 or remote_port >= 65535):
                return
            event_type = 'RASPBOARD_DISCOVERED'
            self.module.dispatch_event(event_type, ((remote_ip, ''),  remote_port, False))

        topic = '.*/.*/.*/' + self.module.ip_address
        lsr = [self.module.build_topic(p)
               for p in self.module.get_services(topic)]

        topic = '.*/.*/.*/' + self.module.ip_address
        gsr = [self.module.build_topic(p)
               for p in self.module.get_services(topic)]


        response = {
            'raspboard_id': self.module.raspboard_id,
            'ip_address': self.module.ip_address,
            'webserver_port': self.module.port,
            'discovery_port': self.module.discovery_port,
            'cluster_port': self.module.cluster_port,
            'application_secret': self.module.application_secret,
            'cookie_secret': self.module.cookie_secret,
            'publish_key': encryption_key,
            'local_service_register': lsr,
            'global_service_register': gsr
        }

        response = self.dump_message(response)
        self.write(response)


config = {
    "service_name": "builtin/service_configurator",
    "handler": Service,
    "service_type": "rest",
    "service_category": "system",
    "dependencies": []
}
