import Queue
import random
import socket
import time
from threading import Thread
from Message import Message
import ast

MAP_TYPE_MESSAGES = [2, 3, 5, 11]
FLOW_TIMEOUT = 5.0

class Threads:
    def __init__(self):
        self.server_connection = True
        self.client_connection = True
        self.map_traffic_flow_thread_is_run = True
        self.update_traffic_flow_thread_is_run = True

        self.address_list = []
        self.bot_ids_list = []

    def request_waiting_thread(self, client_object, client_socket, return_queue):
        messages_queue = Queue.Queue()

        while self.client_connection:
            try:
                data, addr = client_socket.recvfrom(102400)
            except socket.timeout:
                continue

            messages_queue.put({addr: data})
            if not messages_queue.empty():
                message_queue_process_thread = Thread(target=self.message_queue_process_client,
                                                      args=(messages_queue,
                                                            return_queue,
                                                            client_object,
                                                            client_socket,
                                                            addr,))
                message_queue_process_thread.start()
                message_queue_process_thread.join()

                if not return_queue.empty():
                    client_object.id = return_queue.get()
                    client_object.drone_ids = [client_object.id]
                    print 'Get unique id from serve: %s' % client_object.id

    def map_traffic_flow_thread(self, client_object, udp_socket):
        while self.map_traffic_flow_thread_is_run:
            if not self.client_connection:
                break
            time.sleep(FLOW_TIMEOUT + random.randint(0, 2))
            client_object.send_map_flow(udp_socket)

    def update_traffic_flow_thread(self, client_object, udp_socket):
        while self.update_traffic_flow_thread_is_run:
            if not self.client_connection:
                break
            time.sleep(FLOW_TIMEOUT + random.randint(0, 2))
            client_object.map_storage.getChunksFromFile(client_object.map_name)
            client_object.update_map(udp_socket)

    def message_queue_process_client(self, messages_queue, return_queue, client_object, udp_socket, address):
        new_message = messages_queue.get()
        addr = new_message.keys()[0]
        msg = new_message[addr].split('/ ')
        recive_msg = Message(msg)
        receive_log(recive_msg, addr)

        if recive_msg.msg_type == 0:  # server_quit
            self.client_connection = False
            return

        if recive_msg.msg_type == 2:  # map_update_request
            rcv_map, rcv_pos = ast.literal_eval(recive_msg.msg_data)
            client_object.map_storage.getChunkGridFormFile(client_object.map_name)
            self_map = client_object.map_storage.getChunksGrid()
            map_differ = client_object.map_storage.getDifferBetweenMap(rcv_map, self_map)

            if map_differ:
                print 'differ'
                if client_object.map_storage.updateMapWithDifferUpdate(map_differ, rcv_pos, client_object.pos):
                    file_map_update(client_object.map_storage, client_object.map_name)
                    print 'differ agreement'
                    return
                else:
                    print 'differ disagreement'
                    file_map_update(client_object.map_storage, client_object.map_name)
                    self_map = client_object.map_storage.getChunksGrid()
                    send_message(udp_socket, address, client_object.id, "all", 2, [self_map, client_object.pos])
                    print('send new map update')
                    return
            else:
                print 'no differ'
                return

        if recive_msg.msg_type == 3:  # send_map
            print "get map: \n%s\n" % recive_msg.msg_data
            return

        if recive_msg.msg_type == 5:  # map_update_response
            file_map_update_from_response(client_object.map_storage, client_object.map_name, recive_msg.msg_data)
            return

        if recive_msg.msg_type == 6:  # server_hello_response
            return_queue.put(recive_msg.msg_data)
            return

        if recive_msg.msg_type == 7:  # matrix_string_request
            for trg_pos in client_object.target_list:
                a_star_wave = client_object.map_storage.AStar(client_object.pos, trg_pos, [])
                path = client_object.map_storage.getPathFromDistance(a_star_wave, trg_pos, [])
                client_object.trg_path[trg_pos] = path
            print "AStar path ready"
            client_object.target_dstr_storage.initSelfMatrixValues(client_object.drone_ids,
                                                                   client_object.id,
                                                                   client_object.target_list,
                                                                   100)
            client_object.target_dstr_storage.appendMatrixString(ast.literal_eval(recive_msg.msg_data), recive_msg.id)
            client_object.target_dstr_storage.setDroneTargetsPathTimes(client_object.trg_path, 10, 45)
            client_object.target_dstr_storage.selfStringMatrixCalculation(client_object.id)
            client_object.target_dstr_storage.setBotCurrentCharge(recive_msg.id, 100)
            response_data = str(client_object.target_dstr_storage.getSelfMatrixString())
            send_message(udp_socket, address, client_object.id, "all", 8, response_data)
            print 'matrix string send'
            self.matrixCalc(client_object)
            return

        if recive_msg.msg_type == 8:  # send_matrix_string
            client_object.target_dstr_storage.appendMatrixString(ast.literal_eval(recive_msg.msg_data), recive_msg.id)
            client_object.target_dstr_storage.setBotCurrentCharge(recive_msg.id, 100)
            self.matrixCalc(client_object)
            return

        if recive_msg.msg_type == 9:  # ids_update
            client_object.drone_ids = ast.literal_eval(recive_msg.msg_data)
            print 'get new id list', client_object.drone_ids
            return

    def matrixCalc(self, client_object):
        if client_object.target_dstr_storage.checkCountOfDroneTarget():
            client_object.target_dstr_storage.matrixCalc()
            client_object.target_dstr_storage.printTargetForDrone()
            my_target = client_object.target_dstr_storage.getSelfTarget(client_object.id)
            print "My target is: %s" % str(my_target)

    def server_main_cycle_thread(self, server_object, udp_socket):
        messages_queue = Queue.Queue()
        while self.server_connection:
            try:
                data, addr = udp_socket.recvfrom(102400)
            except socket.timeout:
                continue
            messages_queue.put({addr: data.decode("utf-8")})

            if not messages_queue.empty():
                message_queue_process_thread = Thread(target=self.message_queue_process_server,
                                                      args=(messages_queue,
                                                            server_object,
                                                            udp_socket,))
                message_queue_process_thread.start()
                message_queue_process_thread.join()

    def message_queue_process_server(self, messages_queue, server_object, udp_socket):
        new_message = messages_queue.get()
        addr = new_message.keys()[0]
        msg = new_message[addr].split('/ ')
        receive_msg = Message(msg)
        receive_log(receive_msg, addr)

        if receive_msg.response_type == 'server':
            if receive_msg.msg_type == 1:
                self.address_list.remove(addr)
                self.bot_ids_list.remove(str(addr[1]))
                for send_addr in self.address_list:
                    send_message(udp_socket, send_addr, 'server', 'ids_update', 9, str(self.bot_ids_list))
                return

            if receive_msg.msg_type == 4:
                if addr not in self.address_list:
                    self.address_list.append(addr)
                self.bot_ids_list.append(str(addr[1]))
                send_message(udp_socket, addr, 'server', 'server_response', 6, str(addr[1]))
                for send_addr in self.address_list:
                    send_message(udp_socket, send_addr, 'server', 'ids_update', 9, str(self.bot_ids_list))
                return

        if receive_msg.response_type == 'all':
            for sendAddr in self.address_list:
                if addr != sendAddr:
                    message = receive_msg.get_mes()
                    send_log(receive_msg, sendAddr)
                    udp_socket.sendto(str.encode(message), sendAddr)

    def close_server_connection(self, udp_socket):
        # close server-clinet connections
        for addr in self.address_list:
            send_message(udp_socket, addr, 'server', "all", 0, "server_quit")


def send_message(udp_socket, addr, bot_id, response_type, msg_type, msg_data):
    msg = Message([bot_id, response_type, msg_type, msg_data])
    send_log(msg, addr)
    udp_socket.sendto(str(msg), addr)


def receive_log(recive_msg, addr):
    if recive_msg.msg_type in MAP_TYPE_MESSAGES:
        print('from %s received %s' % (addr, 'map'))
    else:
        print('from %s received %s' % (addr, recive_msg.msg_data))


def send_log(recive_msg, sendAddr):
    if recive_msg.msg_type in MAP_TYPE_MESSAGES:
        print('Send %s to %s' % ("map", sendAddr))
    else:
        print('Send %s to %s' % (str.encode(recive_msg.get_mes()), sendAddr))


def file_map_update_from_response(map_storage, map_file_name, response_map):
    response_map_dict = ast.literal_eval(response_map)
    map_chunks = {}

    for key in response_map_dict.keys():
        map_chunks[key] = response_map_dict[key]
    map_storage.updateChunksFromDict(map_chunks)

    map_text = map_storage.printToText()
    for line_number in range(len(map_text)):
        map_text[line_number] = ''.join(map_text[line_number])

    f = open(map_file_name, "w")
    for line in map_text:
        f.write(line)
        f.write('\n')
    f.close()


def file_map_update(map_storage, map_file_name):
    map_text = map_storage.printToText()
    for line_number in range(len(map_text)):
        map_text[line_number] = ''.join(map_text[line_number])
    f = open(map_file_name, "w")
    for line in map_text:
        f.write(line)
        f.write('\n')
    f.close()
