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

    def request_waiting_thread(self, client_object, client_socket, return_queue):
        messages_queue = Queue.Queue()

        while self.client_connection:
            try:
                data, addr = client_socket.recvfrom(102400)
            except:
                continue

            """CLIENT LOGS"""
            data_list = data.split('/ ')

            if data_list[1] == '5':
                print('from %s received %s' % (addr, "map"))
            else:
                print('from %s received %s' % (addr, data))

            messages_queue.put({addr: data})
            if not messages_queue.empty():
                message_queue_process_thread = Thread(target=self.message_queue_process,
                                                      args=(messages_queue,
                                                            return_queue,
                                                            client_object,
                                                            client_socket,
                                                            addr,))
                message_queue_process_thread.start()
                message_queue_process_thread.join()

                if not return_queue.empty():
                    client_object.id = return_queue.get()
                    client_object.bot_pos_dict[client_object.id] = client_object.pos
                    print 'Get unique id from serve: %s' % client_object.id

    def message_queue_process(self, messages_queue, return_queue, client_object, udp_socket, address):
        new_message = messages_queue.get()
        addr = new_message.keys()[0]
        msg = new_message[addr].split('/ ')

        if int(msg[1]) == 0:  # server_quit
            self.client_connection = False
            return

        if int(msg[1]) == 2:  # map_update_request
            msg = Message("all", 5, dict_to_str(client_object.map_storage._chunks))
            udp_socket.sendto(str(msg), address)
            return

        if int(msg[1]) == 5:  # map_update_response
            file_map_update(client_object.map_storage, "map2.mapAI", msg[2])
            return

        if int(msg[1]) == 6:  # server_hello_response
            return_queue.put(msg[2])
            return

        if int(msg[1]) == 7:  # position_request
            response_data = "%s.%s" % (client_object.id, client_object.pos)
            msg = Message("all", 8, response_data)
            udp_socket.sendto(str(msg), address)
            print 'position response send'
            return

        if int(msg[1]) == 8:  # position_response

            bot_id_pos = msg[2].split('.')

            client_object.bot_pos_dict[bot_id_pos[0]] = ast.literal_eval(bot_id_pos[1])
            print 'get position response'
            print client_object.bot_pos_dict
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
                if data_list[2] == "client_hello_msg":
                    msg = Message('server_response', 6, str(addr[1]))
                    udp_socket.sendto(str(msg), addr)
            except:
                continue

            """SERVER RECEIVE LOGS"""
            if data_list[1] == '5':
                print('from %s received %s' % (addr, 'map'))
            else:
                print('from %s received %s' % (addr, str.encode(data)))

            messages_queue.put({addr: data.decode("utf-8")})

            new_message = messages_queue.get()
            if new_message and data_list[0] == 'all':
                for sendAddr in adrress_list:
                    if addr != sendAddr:
                        if data_list[1] == '5':

                            """SERVER SENDING LOGS"""
                            print('Send %s to %s' % ("map", sendAddr))
                        else:
                            print('Send %s to %s' % (str.encode(data), sendAddr))

                        udp_socket.sendto(str.encode(data), sendAddr)

        # close server-clinet connections
        for addr in adrress_list:
            msg = Message("all", 0, "server_quit")
            udp_socket.sendto(str(msg), addr)


def dict_to_str(dictation):
    result_str = ""
    for key in dictation.keys():
        result_str += str(key) + ' : ' + str(dictation[key]._grid) + ', '
    return result_str


def file_map_update(map_storage, map_file_name, response_map):
    response_map = '{' + response_map + '}'
    respose_map_dict = ast.literal_eval(response_map)
    map_chunks = map_storage.getChunksDict()

    for key in respose_map_dict.keys():
        map_chunks[key] = respose_map_dict[key]
    map_storage.updateChunksFromDict(map_chunks)

    map_text = map_storage.printToText()
    for line_number in range(len(map_text)):
        map_text[line_number] = ''.join(map_text[line_number])

    f = open(map_file_name, "w")
    for line in map_text:
        f.write(line)
        f.write('\n')
    f.close()
