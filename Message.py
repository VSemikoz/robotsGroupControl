class Message:
    def __init__(self, response_type, msg_type, msg_data):
        self.response_type = response_type
        self.msg_type = msg_type
        self.msg_data = msg_data

        self.header = str(self.response_type) + '/ ' + str(self.msg_type)
        self.body = str(self.msg_data)

    def __str__(self):
        return self.header + '/ ' + self.body

