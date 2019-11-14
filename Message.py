<<<<<<< HEAD
class Message:
    def __init__(self, ip_dst, msg_type, msg_data):
        self.ip_dst = ip_dst
        self.msg_type = msg_type
        self.msg_data = msg_data

        self.header = str(self.ip_dst) + '/ ' + str(self.msg_type)
        self.body = str(self.msg_data)

    def __str__(self):
        return self.header + '/ ' + self.body
=======
class Message:
    def __init__(self, ip_dst, msg_type, msg_data):
        self.ip_dst = ip_dst
        self.msg_type = msg_type
        self.msg_data = msg_data

        self.header = str(self.ip_dst) + '/ ' + str(self.msg_type)
        self.body = str(self.msg_data)

    def __str__(self):
        return self.header + '/ ' + self.body
>>>>>>> 4205406f1572b76f1e07a83bc6664ef2c2123c55
