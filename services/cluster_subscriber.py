from a_service import ThreadHandler as superClass
from common.event_module import Event as frameworkEvent
import pyaes
import zmq


class Service(superClass):
    def initialize(self, module, stopevent):
        self.module = module
        self.stopevent = stopevent

        self.pub_sub_encryption_key = None

        # subscribe to events of found RaspBoards when thier configuration
        # have been optained:
        found_event = 'RASPBOARD_CONFIGURATION_OPTAINED'
        self.module.add_event_listener(found_event, self.subscribe)
        
        # self.key_change_event_name = 'PUBSUB_KEY_CHANGED'
        # self.module.add_event_listener(self.key_change_event_name, self.encryption_key_changed)
        self.keys = {}

        # init subscriber:
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        topFilter = ""
        self.socket.setsockopt(zmq.SUBSCRIBE, topFilter)

        self.recieve_msg()

    def subscribe(self, event):
        rasp_id = self.try_get(event.data, 'raspboard_id') 
        ip_address = self.try_get(event.data, 'ip_address')
        port = self.try_get(event.data, 'cluster_port')
        encryption_key = self.try_get(event.data, 'publish_key')

        # print('CONFIG', rasp_id, ip_address, port, encryption_key)
        if(port is None or 
           ip_address is None or 
           rasp_id is None or
           rasp_id in self.keys or
           (ip_address is not None and port is not None and 
            ip_address == self.module.ip_address and 
            port == self.module.cluster_port)):
            return
        # print('SUBSCRIBING')
        self.keys[rasp_id] = encryption_key
        sub_url = 'tcp://%s:%s' % (ip_address, port)
        self.socket.connect(sub_url)
        self.module.dispatch_event('SUBSCRIBED_TO_RASPBOARD',
                                   (sub_url, config['service_name']))

    def recieve_msg(self):
        while(not self.stopevent.is_set()):
            msg = self.socket.recv()
            # print(msg)
            isSuccess, raspid, event = self.parse_msg_to_event(msg)
            if(isSuccess):
                if(event.type == 'PUBLISH_KEY_CHANGED'):
                    if(raspid in self.keys and event.data != self.keys[raspid]):
                        self.keys[raspid] = event.data
                        self.module.dispatch_event('LOG', (8, 'CHANGED SUBSCRIBE KEY', raspid, event.data, config['service_name']))
                elif(event.type == 'TERMINATING' and raspid in self.keys):
                    self.keys.pop(raspid, None)
                else:
                    self.module.event_dispatcher.dispatch_event(event)
            else:
                self.module.dispatch_event('LOG', (4, 'FAILED TO PARSE MSG', event, config['service_name']))

    def parse_msg_to_event(self, msg):
        rasp_id, msg = msg.split(' ', 1)
        
        if(rasp_id in self.keys):
            key = self.keys[rasp_id]
            aes = pyaes.AESModeOfOperationCTR(key.decode('base-64'))
            msg = aes.decrypt(msg)
        try:
            e_t, e_org, e_d = msg.split(' ', 2)
            
            try:
                e_d = self.load_message(e_d)
            except:
                return False, rasp_id, e_d

            event = frameworkEvent(e_t, e_org, e_d)
            return True, rasp_id, event
        except:
            return False, rasp_id, msg


    def try_get(self, obj, field, default=None):
        if(field in obj):
            return obj[field]
        else:
            return default

config = {
    "service_name": "builtin/cluster_subscriber",
    "handler": Service,
    "service_type": "thread",
    "service_category": "system",
    "dependencies": [
    ]
}
