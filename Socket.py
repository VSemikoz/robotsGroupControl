import socket
import Queue
import os
from threading import Thread
from Threads import Threads, send_message
from map_storage import Map
from MatrixCalcModule import MatrixCalcModule
from MessageType import MessageType as MT


class Socket:
    def __init__(self):
        self.host = '192.168.1.243'
        self.port = 263
        self.address = (self.host, self.port)

        self.threads = Threads()


class Server(Socket):

    def run_server(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(self.address)
        udp_socket.setblocking(False)
        udp_socket.settimeout(1)

        server_thread = Thread(target=self.threads.server_main_cycle_thread, args=(self, udp_socket,))
        server_thread.start()

        while self.threads.server_connection:
            user_input = raw_input("Input command: ")
            self.process_server_input(user_input, udp_socket)
        server_thread.join()
        udp_socket.close()

    def process_server_input(self, user_input, udp_socket):
        if user_input == "quit":
            self.threads.close_server_connection(udp_socket)
            self.threads.server_connection = False


class Client(Socket):
    def __init__(self):
        Socket.__init__(self)
        self.start_flows_immediately = True  # change to False if need start flows by command
        self.map_name = None
        self.id = None
        self.pos = None
        self.target_list = []
        self.map_storage = Map()
        self.target_dstr_storage = MatrixCalcModule()
        self.drone_ids = []
        self.trg_path = {}

        self.update_traffic_flow_thread = None
        self.target_distribution_flow_thread = None

    def run_client(self):
        return_queue = Queue.Queue()
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(1)
        self.map_name = select_map_file()

        self.map_storage.getChunkGridFormFile(self.map_name)
        self.target_list, self.pos = self.map_storage.getBotTargetCoords()
        send_message(udp_socket, self.address, self.id, 'server', MT.CLIENT_HELLO_REQUEST, 'client_hello_msg')
        print "Hello msg to server sent"

        print "start request_thread"
        request_thread = Thread(target=self.threads.request_waiting_thread,
                                args=(self, udp_socket, return_queue,))
        request_thread.start()
        self.start_flows(udp_socket)

        while self.threads.client_connection:
            user_input = raw_input("Input command: ")
            self.process_user_input(user_input, udp_socket)
        request_thread.join()

    def process_user_input(self, user_input, udp_socket):
        if user_input == "quit":
            send_message(udp_socket, self.address, self.id, 'server', MT.CLIENT_QUIT, "quit")
            self.threads.client_connection = False
            print "close connection client"
            return

        if user_input == "get_map":
            map_data = self.get_map()
            print "current map is: %s\n" % map_data
            return

        if user_input == "send_map":
            self.send_map(udp_socket)
            print 'map send'
            return

        if user_input == "show_trg":
            print 'target list is: %s' % str(self.target_list)
            return

        if user_input == "show_pos":
            print 'self pos is: %s' % str(self.pos)
            return

        if user_input == "update_map":
            self.map_storage.getChunksFromFile(self.map_name)
            self.update_map(udp_socket)
            print "map update request sent"
            return

        if user_input == "trg_dst":
            self.target_distribution(udp_socket)
            return

        if user_input == "start_td_flow":
            if self.threads.target_distribution_flow_thread_is_run:
                print "target distribution is already started"
                return
            self.threads.target_distribution_flow_thread_is_run = True
            self.target_distribution_flow_thread = Thread(target=self.threads.target_distribution_flow_thread,
                                                          args=(self, udp_socket,))
            self.target_distribution_flow_thread.start()
            print "target distribution is start"
            return

        if user_input == "stop_td_flow":
            if not self.threads.target_distribution_flow_thread_is_run:
                print "target distribution is not start"
                return
            self.threads.target_distribution_flow_thread_is_run = False
            self.target_distribution_flow_thread.join()
            print "target distribution is stop"
            return

        if user_input == "start_update_flow":
            if self.threads.update_traffic_flow_thread_is_run:
                print "map update flow is already started"
                return
            self.threads.update_traffic_flow_thread_is_run = True
            self.update_traffic_flow_thread = Thread(target=self.threads.update_traffic_flow_thread,
                                                     args=(self, udp_socket,))
            self.update_traffic_flow_thread.start()
            print "map update flow is start"
            return

        if user_input == "stop_update_flow":
            if not self.threads.update_traffic_flow_thread_is_run:
                print "map update flow is not start"
                return
            self.threads.update_traffic_flow_thread_is_run = False
            self.update_traffic_flow_thread.join()
            print "map update flow is stop"
            return

    def start_flows(self, udp_socket):
        if self.start_flows_immediately:
            self.start_update_flow(udp_socket)
            self.start_target_distribution_flow(udp_socket)

    def start_update_flow(self, udp_socket):
        if self.threads.update_traffic_flow_thread_is_run:
            print "map update flow is already started"
            return
        self.threads.update_traffic_flow_thread_is_run = True
        self.update_traffic_flow_thread = Thread(target=self.threads.update_traffic_flow_thread,
                                                 args=(self, udp_socket,))
        self.update_traffic_flow_thread.start()
        print "map update flow is start"

    def start_target_distribution_flow(self, udp_socket):
        if self.threads.target_distribution_flow_thread_is_run:
            print "target distribution flow is already started"
            return
        self.threads.target_distribution_flow_thread_is_run = True
        self.target_distribution_flow_thread = Thread(target=self.threads.target_distribution_flow_thread,
                                                      args=(self, udp_socket,))
        self.target_distribution_flow_thread.start()
        print "target distribution flow is start"

    def bots_matrix_string_request(self, udp_socket):
        request_data = str(self.target_dstr_storage.getSelfMatrixString())
        send_message(udp_socket, self.address, self.id, 'all', MT.MATRIX_STRING_REQUEST, request_data)

    def get_map(self):
        handle = open(self.map_name, "r")
        data = handle.read()
        handle.close()
        return data

    def send_map(self, udp_socket):
        map_data = self.get_map()
        send_message(udp_socket, self.address, self.id, 'all', MT.SEND_MAP, map_data)

    # sepparate method to send map in delay without logs
    def send_map_flow(self, udp_socket):
        map_data = self.get_map()
        send_message(udp_socket, self.address, self.id, 'all', MT.SEND_MAP_NOLOG, map_data)

    def update_map(self, udp_socket):
        map_chunks = self.map_storage.getChunksGrid()
        send_message(udp_socket, self.address, self.id, 'all', MT.MAP_UPDATE_REQUEST, [map_chunks, self.pos])

    def target_distribution(self, udp_socket):
        self.map_storage.getChunkGridFormFile(self.map_name)
        self.target_list, self.pos = self.map_storage.getBotTargetCoords()

        for trg_pos in self.target_list:
            a_star_wave = self.map_storage.AStar(self.pos, trg_pos, [])
            path = self.map_storage.getPathFromDistance(a_star_wave, trg_pos, [])
            self.trg_path[trg_pos] = path
        self.target_dstr_storage.initSelfMatrixValues(self.drone_ids, self.id, self.target_list, 100)
        self.target_dstr_storage.setDroneTargetsPathTimes(self.trg_path, 10, 45)
        self.target_dstr_storage.selfStringMatrixCalculation(self.id)
        self.bots_matrix_string_request(udp_socket)
        print "bots matrix string request sent"


def select_map_file():
    while True:
        user_input = str(raw_input("input map name: "))
        if os.path.isfile(user_input):
            return user_input
        else:
            print 'no such map name'
            continue
