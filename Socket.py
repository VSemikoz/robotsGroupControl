import socket
import Queue
from threading import Thread
from Threads import Threads

class Socket:
    def __init__(self):
        self.host = '192.168.1.243'
        self.port = 261
        self.address = (self.host, self.port)

        self.threads = Threads()


class Server(Socket):

    def run_server(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(self.address)
        udp_socket.settimeout(1)

        server_thread = Thread(target=self.threads.server_main_cycle_thread, args=(udp_socket,))
        server_thread.start()

        while self.threads.server_connection:
            user_input = raw_input("Input command: ")
            self.process_server_input(user_input)
        server_thread.join()
        udp_socket.close()


    def process_server_input(self, user_input):
        print user_input
        if user_input == "quit":
            self.threads.server_connection = False


class Client(Socket):
    def run_client(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(1)

        udp_socket.sendto(str.encode("Hello"), self.address)
        print "start request_thread"
        request_thread = Thread(target=self.threads.request_waiting_thread, args=(udp_socket,))
        request_thread.start()

        while self.threads.client_connection:
            user_input = raw_input("Input command: ")
            self.process_user_input(user_input, udp_socket)
        request_thread.join()



    def process_user_input(self, user_input, udp_socket):
        print user_input
        if user_input == "quit":
            self.threads.client_connection = False
        if user_input == "get_map":
            map = self.get_map()
            print map
        if user_input == "send_map":
            self.send_map(udp_socket)

    def get_map(self):
        handle = open("map.mapAI", "r")
        data = handle.read()
        handle.close()
        return data

    def send_map(self, udp_socket):
        print "sending", self.address
        map_data = self.get_map()
        udp_socket.sendto(str.encode(map_data), self.address)
