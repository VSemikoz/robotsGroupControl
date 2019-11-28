class Message:
    def __init__(self, mes):
        self.id = mes[0]
        self.response_type = mes[1]
        self.msg_type = int(mes[2])
        self.msg_data = mes[3]

        self.header = str(self.id) + '/ ' + str(self.response_type) + '/ ' + str(self.msg_type)
        self.body = str(self.msg_data)

    def __str__(self):
        return self.header + '/ ' + self.body

    def get_mes(self):
        return self.header + '/ ' + self.body