import socket
import Queue
from threading import Thread

class Threads():
    def __init__(self):
        self.server_connection = True
        self.client_connection = True

    def request_waiting_thread(self, client_socket):
        messages_queue = Queue.Queue()

        while self.client_connection:
                try:
                    data, addr = client_socket.recvfrom(10240)
                except:
                    continue
                print('from %s recived %s' % (addr, data))
                messages_queue.put({addr: data})
                if not messages_queue.empty():
                    message_queue_process_thread = Thread(target=self.message_queue_process, args=(messages_queue,))
                    message_queue_process_thread.start()
                    message_queue_process_thread.join()


    def message_queue_process(self, messages_queue):
        new_message = messages_queue.get()
        print new_message,'wowow'

    def server_main_cycle_thread(self, udp_socket):
        adrress_list = []
        messages_queue = Queue.Queue()

        while self.server_connection:
                try:
                    data, addr = udp_socket.recvfrom(10240)
                except:
                    continue
                print('from %s recived %s' % (addr, data))
                messages_queue.put({addr: data.decode("utf-8")})
                if addr not in adrress_list:
                    adrress_list.append(addr)

                new_message = messages_queue.get()
                if new_message:
                    for addr in adrress_list:
                        for sendAddr in adrress_list:
                            if addr != sendAddr:
                                print('Send %s to %s' % (str.encode(data), addr))
                                udp_socket.sendto(str.encode(data), addr)
