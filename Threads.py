import Queue
from threading import Thread
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
            if data_list[2] in ['2', '3', '5']:
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
                    client_object.drone_ids = [client_object.id]
                    print 'Get unique id from serve: %s' % client_object.id

    def message_queue_process(self, messages_queue, return_queue, client_object, udp_socket, address):
        new_message = messages_queue.get()
        addr = new_message.keys()[0]
        msg = new_message[addr].split('/ ')
        recive_msg = Message(msg)

        if recive_msg.msg_type == 0:  # server_quit
            self.client_connection = False
            return

        if recive_msg.msg_type == 2:  # map_update_request
            rcv_map, pos, back_ip = ast.literal_eval(recive_msg.msg_data)
            client_object.map_storage.getChunkGridFormFile(client_object.map_name)
            self_map = client_object.map_storage.getChunksGrid()
            map_differ = client_object.map_storage.getDifferBetweenMap(rcv_map, self_map)
            if map_differ:
                print 'differ'
                if client_object.map_storage.updateMapWithDifferUpdate(map_differ, pos):
                    file_map_update(client_object.map_storage, client_object.map_name)
                    print 'differ agreement'
                    return
                else:
                    print 'differ disagreement'
                    file_map_update(client_object.map_storage, client_object.map_name)
                    self_map = client_object.map_storage.getChunksGrid()
                    msg = Message([client_object.id, (client_object.host, back_ip), 5, self_map])
                    udp_socket.sendto(str(msg), address)
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
            msg = Message([client_object.id, "all", 8, response_data])
            udp_socket.sendto(str(msg), address)
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
        adrress_list = []
        bot_ids_list = []
        messages_queue = Queue.Queue()

        while self.server_connection:
            try:
                #TODO delete data_list
                data, addr = udp_socket.recvfrom(102400)
                data_list = data.split('/ ')

                if addr not in adrress_list:
                    adrress_list.append(addr)

                if data_list[3] == "quit":
                    adrress_list.remove(addr)
                    bot_ids_list.remove(str(addr[1]))
                    for send_addr in adrress_list:
                        msg = Message(['server', 'ids_update', 9, str(bot_ids_list)])
                        udp_socket.sendto(str(msg), send_addr)

                if data_list[3] == "client_hello_msg":
                    bot_ids_list.append(str(addr[1]))
                    msg = Message(['server', 'server_response', 6, str(addr[1])])
                    udp_socket.sendto(str(msg), addr)
                    for send_addr in adrress_list:
                        msg = Message(['server', 'ids_update', 9, str(bot_ids_list)])
                        udp_socket.sendto(str(msg), send_addr)
            except:
                continue

            """SERVER RECEIVE LOGS"""
            if data_list[2] in ['2', '3', '5']:
                print('from %s received %s' % (addr, 'map'))
            else:
                print('from %s received %s' % (addr, str.encode(data)))

            messages_queue.put({addr: data.decode("utf-8")})

            new_message = messages_queue.get()
            if new_message and data_list[1] == 'all':
                for sendAddr in adrress_list:
                    if addr != sendAddr:
                        if data_list[2] in ['2', '3', '5']:
                            """SERVER SENDING LOGS"""
                            print('Send %s to %s' % ("map", sendAddr))
                        else:
                            print('Send %s to %s' % (str.encode(data), sendAddr))
                        udp_socket.sendto(str.encode(data), sendAddr)
            elif new_message and data_list[1] == 'server':
                pass
            elif new_message and ast.literal_eval(data_list[1])[0] == server_object.host:
                print 'Send to %s' % data_list[1]
                host, port = ast.literal_eval(data_list[1])
                port = int(port)
                udp_socket.sendto(str.encode(data), (host, port))

        # close server-clinet connections
        for addr in adrress_list:
            msg = Message(['server', "all", 0, "server_quit"])
            udp_socket.sendto(str(msg), addr)


def dict_to_str(dictation):
    result_str = ""
    for key in dictation.keys():
        result_str += str(key) + ' : ' + str(dictation[key]._grid) + ', '
    return result_str


def file_map_update_from_response(map_storage, map_file_name, response_map):
    response_map_dict = ast.literal_eval(response_map)
    map_chunks = map_storage.getChunksDict()

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
