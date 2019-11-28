import socket
import Queue
from threading import Thread
from Threads import Threads
from Message import Message
from map_storage import Map
from MatrixCalcModule import MatrixCalcModule


class Socket:
    def __init__(self):
        self.host = '192.168.1.243'
        #self.host = '192.168.43.73'
        self.port = 263
        self.address = (self.host, self.port)

        self.threads = Threads()


class Server(Socket):

    def run_server(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(self.address)
        udp_socket.setblocking(False)
        udp_socket.settimeout(1)

        server_thread = Thread(target=self.threads.server_main_cycle_thread, args=(self,
                                                                                   udp_socket,))
        server_thread.start()

        while self.threads.server_connection:
            user_input = raw_input("Input command: ")
            self.process_server_input(user_input)
        server_thread.join()
        udp_socket.close()

    def process_server_input(self, user_input):
        if user_input == "quit":
            self.threads.server_connection = False


class Client(Socket):
    def __init__(self):
        Socket.__init__(self)
        self.map_name = "1"
        self.id = None
        self.pos = None
        self.target_list = []
        self.map_storage = Map()
        self.target_dstr_storage = MatrixCalcModule()
        self.drone_ids = []
        self.trg_path = {}

    def run_client(self):
        return_queue = Queue.Queue()
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(1)

        user_input = str(input("input map name: "))
        self.map_name = user_input

        self.map_storage.getChunkGridFormFile(self.map_name)
        self.target_list, self.pos = self.map_storage.getBotTargetCoords()
        msg = Message([self.id, 'server', 4, 'client_hello_msg'])
        udp_socket.sendto(str(msg), self.address)
        print "Hello msg to server sent"

        print "start request_thread"
        request_thread = Thread(target=self.threads.request_waiting_thread, args=(self,
                                                                                  udp_socket,
                                                                                  return_queue,))
        request_thread.start()

        while self.threads.client_connection:
            user_input = raw_input("Input command: ")
            self.process_user_input(user_input, udp_socket)
        request_thread.join()

    def process_user_input(self, user_input, udp_socket):
        if user_input == "quit":
            msg = Message([self.id, 'server', 1, "quit"])
            udp_socket.sendto(str(msg), self.address)
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

            for trg_pos in self.target_list:
                a_star_wafe = self.map_storage.AStar(self.pos, trg_pos, [])
                path = self.map_storage.getPathFromDistance(a_star_wafe, trg_pos, [])
                self.trg_path[trg_pos] = path

            self.target_dstr_storage.initSelfMatrixValues(self.drone_ids, self.id, self.target_list, 100)
            self.target_dstr_storage.setDroneTargetsPathTimes(self.trg_path, 10, 45)
            self.target_dstr_storage.selfStringMatrixCalculation(self.id)
            self.bots_matrix_tring_request(udp_socket)
            print "bots matrix string request sent"
            return

    def bots_matrix_tring_request(self, udp_socket):
        request_data = str(self.target_dstr_storage.getSelfMatrixString())
        msg = Message([self.id, 'all', 7, request_data])
        udp_socket.sendto(str(msg), self.address)

    def get_map(self):
        handle = open(self.map_name, "r")
        data = handle.read()
        handle.close()
        return data

    def send_map(self, udp_socket):
        map_data = self.get_map()
        msg = Message([self.id, 'all', 3, map_data])
        udp_socket.sendto(str(msg), self.address)

    def update_map(self, udp_socket):
        map_chunks = self.map_storage.getChunksGrid()
        msg = Message([self.id, 'all', 2, [map_chunks, self.pos, self.id]])
        udp_socket.sendto(str(msg), self.address)
