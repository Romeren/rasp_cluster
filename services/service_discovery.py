from a_service import ThreadHandler as superClass
import socket
import time
import zmq


class Service(superClass):
    def initialize(self, module, stopevent):
        self.no_of_broadcasts = 1
        self.broadcast_interval = 3
        self.own_ip_address = module.ip_address
        self.discovery_port = module.discovery_port
        self.discovery_msg = b'ECHO'
        self.discovery_msg_size = len(self.discovery_msg)
        self.broadcast_address = "255.255.255.255"

        self.module = module
        self.stopevent = stopevent

        self.init_connections()
        self.discover()

    def init_connections(self):
        # create socket:
        self.sock = socket.socket(socket.AF_INET,
                                  socket.SOCK_DGRAM,
                                  socket.IPPROTO_UDP)

        # Ask for broadcast networking
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Bind socket for incomming messeges:
        self.sock.bind(('', self.discovery_port))

        # initiate ZMQ
        self.poller = zmq.Poller()
        self.poller.register(self.sock, zmq.POLLIN)

    def discover(self):
        time.sleep(2)
        echo_at = time.time()
        while(not self.module.stop_event.is_set()):
            # listen on port for incomming msg until it is time to send out a
            # broadcast msg
            self.listen_on_network(echo_at)

            # send out a broadcast msg for anyone to anwser:
            echo_at = self.send_echo(echo_at)

    def listen_on_network(self, last_echo):
        timeout = 10
        if(self.no_of_broadcasts > 0):
            timeout = last_echo - time.time()
            if(timeout < 0):
                timeout = 0

        events = dict(self.poller.poll(1000 * timeout))

        # Answers
        if(events is not None and self.sock.fileno() in events):
            msg, addr_info = self.sock.recvfrom(self.discovery_msg_size)
            if(addr_info[0] == self.own_ip_address):
                return
            elif(msg == self.discovery_msg):
                self.handle_incoming_echo(msg, addr_info)
            else:
                self.handle_incoming_discovery(msg, addr_info)

    def handle_incoming_echo(self, msg, addr_info):
        self.sock.sendto(str(self.module.port),
                         0,
                         addr_info)

    def handle_incoming_discovery(self, msg, addr_info):
        self.module.dispatch_event('RASPBOARD_DISCOVERED',
                                   (addr_info, msg, True))

    def send_echo(self, last_echo):
        # broadcast beacon
        if(self.no_of_broadcasts > 0 and time.time() >= last_echo):
            self.no_of_broadcasts -= 1
            self.module.dispatch_event('LOG',
                                       (1,
                                        'SERVICE_BROADCASTING',
                                        self.discovery_msg,
                                        config['service_name']
                                        ))
            self.sock.sendto(self.discovery_msg,
                             0,
                             (self.broadcast_address, self.discovery_port))
            last_echo = time.time() + self.broadcast_interval
        return last_echo

config = {
    "service_name": "builtin/service_discovery",
    "handler": Service,
    "service_type": "thread",
    "service_category": "system",
    "dependencies": []
}
