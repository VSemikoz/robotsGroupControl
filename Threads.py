<<<<<<< HEAD
import socket
import Queue
from threading import Thread
from map_storage import Map
from Message import Message
import ast


class Threads():
    def __init__(self):
        self.server_connection = True
        self.client_connection = True

    def request_waiting_thread(self, client_socket, address):
        messages_queue = Queue.Queue()
        map = Map()

        while self.client_connection:
            try:
                data, addr = client_socket.recvfrom(102400)
            except:
                continue
            print('from %s recived %s' % (addr, data))
            messages_queue.put({addr: data})
            if not messages_queue.empty():
                message_queue_process_thread = Thread(target=self.message_queue_process,
                                                      args=(messages_queue, client_socket, address, map))
                message_queue_process_thread.start()
                message_queue_process_thread.join()

    def message_queue_process(self, messages_queue, udp_socket, address, map):
        new_message = messages_queue.get()
        addr = new_message.keys()[0]
        msg = new_message[addr].split('/ ')

        #print addr, msg

        if int(msg[1]) == 0:  # server_quit
            self.client_connection = False
            return

        if int(msg[1]) == 2:  # map_update_request
            map_chunks = Map().getChunkGridFormFile("map1.mapAI")

            msg = Message("all", 5, dict_to_str(map_chunks))
            udp_socket.sendto(str(msg), address)
            return

        if int(msg[1]) == 5:  # map_update_response

            file_map_update(map, "map2.mapAI", msg[2])
            return

    def server_main_cycle_thread(self, udp_socket):
        adrress_list = []
        messages_queue = Queue.Queue()

        while self.server_connection:
            try:
                data, addr = udp_socket.recvfrom(102400)
                data_list = data.split('/ ')
                if addr not in adrress_list:
                    adrress_list.append(addr)
                if data_list[2] == "quit":
                    adrress_list.remove(addr)
            except:
                continue
            print('from %s recived %s' % (addr, data))
            messages_queue.put({addr: data.decode("utf-8")})

            new_message = messages_queue.get()
            if new_message and data_list[0] == 'all':
                for sendAddr in adrress_list:
                    if addr != sendAddr:
                        print('Send %s to %s' % (str.encode(data), sendAddr))
                        udp_socket.sendto(str.encode(data), sendAddr)

        # close server-clinet connections
        for addr in adrress_list:
            msg = Message("all", 0, "server_quit")
            udp_socket.sendto(str(msg), addr)


def dict_to_str(dictation):
    result_str = ""
    for key in dictation.keys():
        result_str += str(key) + ' : ' + dictation[key] + ', '
    return result_str


def file_map_update(map, map_file_name, response_map):
    response_map = '{' + response_map + '}'
    respose_map_dict = ast.literal_eval(response_map)
    map_chunks = map.getChunkGridFormFile(map_file_name)

    for key in respose_map_dict.keys():
        map_chunks[key] = respose_map_dict[key]

    map.updateChunksFromDict(map_chunks)
    map_text = map.printToText()
    for line_number in range(len(map_text)):
        map_text[line_number] = ''.join(map_text[line_number])

    f = open(map_file_name, "w")
    for line in map_text:
        f.write(line)
        f.write('\n')
    f.close()
=======
import socket
import Queue
from threading import Thread
from map_storage import Map
from Message import Message
import ast


class Threads():
    def __init__(self):
        self.server_connection = True
        self.client_connection = True

    def request_waiting_thread(self, client_socket, address):
        messages_queue = Queue.Queue()
        map = Map()

        while self.client_connection:
            try:
                data, addr = client_socket.recvfrom(102400)
            except:
                continue
            print('from %s recived %s' % (addr, data))
            messages_queue.put({addr: data})
            if not messages_queue.empty():
                message_queue_process_thread = Thread(target=self.message_queue_process,
                                                      args=(messages_queue, client_socket, address, map))
                message_queue_process_thread.start()
                message_queue_process_thread.join()

    def message_queue_process(self, messages_queue, udp_socket, address, map):
        new_message = messages_queue.get()
        addr = new_message.keys()[0]
        msg = new_message[addr].split('/ ')

        #print addr, msg

        if int(msg[1]) == 0:  # server_quit
            self.client_connection = False
            return

        if int(msg[1]) == 2:  # map_update_request
            map_chunks = Map().getChunkGridFormFile("map1.mapAI")

            msg = Message("all", 5, dict_to_str(map_chunks))
            udp_socket.sendto(str(msg), address)
            return

        if int(msg[1]) == 5:  # map_update_response

            file_map_update(map, "map2.mapAI", msg[2])
            return

    def server_main_cycle_thread(self, udp_socket):
        adrress_list = []
        messages_queue = Queue.Queue()

        while self.server_connection:
            try:
                data, addr = udp_socket.recvfrom(102400)
                data_list = data.split('/ ')
                if addr not in adrress_list:
                    adrress_list.append(addr)
                if data_list[2] == "quit":
                    adrress_list.remove(addr)
            except:
                continue
            print('from %s recived %s' % (addr, data))
            messages_queue.put({addr: data.decode("utf-8")})

            new_message = messages_queue.get()
            if new_message and data_list[0] == 'all':
                for sendAddr in adrress_list:
                    if addr != sendAddr:
                        print('Send %s to %s' % (str.encode(data), sendAddr))
                        udp_socket.sendto(str.encode(data), sendAddr)

        # close server-clinet connections
        for addr in adrress_list:
            msg = Message("all", 0, "server_quit")
            udp_socket.sendto(str(msg), addr)


def dict_to_str(dictation):
    result_str = ""
    for key in dictation.keys():
        result_str += str(key) + ' : ' + dictation[key] + ', '
    return result_str


def file_map_update(map, map_file_name, response_map):
    response_map = '{' + response_map + '}'
    respose_map_dict = ast.literal_eval(response_map)
    map_chunks = map.getChunkGridFormFile(map_file_name)

    for key in respose_map_dict.keys():
        map_chunks[key] = respose_map_dict[key]

    map.updateChunksFromDict(map_chunks)
    map_text = map.printToText()
    for line_number in range(len(map_text)):
        map_text[line_number] = ''.join(map_text[line_number])

    f = open(map_file_name, "w")
    for line in map_text:
        f.write(line)
        f.write('\n')
    f.close()
>>>>>>> 4205406f1572b76f1e07a83bc6664ef2c2123c55
