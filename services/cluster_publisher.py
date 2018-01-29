from a_service import ThreadHandler as superClass
import pyaes
import time
import zmq
import os

class Service(superClass):
    def initialize(self, module, stopevent):
        self.module = module
        self.stopevent = stopevent

        self.key_length = 32
        self.key_name = 'PUBLISH'
        self.encryption_key = os.urandom(self.key_length).encode('base-64')
        self.key_change_event_name = self.key_name + '_KEY_CHANGED'
        self.encryption_key_request = self.key_name + '_ENCRYPTION_KEY_REQUEST'

        self.module.dispatch_event(self.key_change_event_name, (self.encryption_key))

        found_event = '*'
        self.module.add_event_listener(found_event, self.publish)

        # init subscriber:
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        pub_url = 'tcp://%s:%s' % (self.module.ip_address,
                                   self.module.cluster_port)
        self.module.dispatch_event('LOG', (10, pub_url, config['service_name']))
        self.socket.bind(pub_url)

    def publish(self, event):
        event_type = event.type
        event_origin = event.origin_host
        if(event_type == self.encryption_key_request):
            self.module.dispatch_event(self.key_change_event_name, (self.encryption_key))
            return
        
        event_data = self.dump_message(event.data)
        if(event_data is None):
            event_data = event.data

        if(event_origin == self.module.ip_address):
            message = '%s %s %s' % (event_type, event_origin, event_data)
            if(self.encryption_key is not None):
                aes = pyaes.AESModeOfOperationCTR(self.encryption_key.decode('base-64'))
                message = aes.encrypt(message)
            message = '%s %s' % (self.module.raspboard_id, message)
            self.socket.send(message)


config = {
    "service_name": "builtin/cluster_publisher",
    "handler": Service,
    "service_type": "thread",
    "service_category": "system",
    "dependencies": []
}
