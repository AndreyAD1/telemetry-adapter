class QueueClientException(Exception):
    pass


class QueueClientUnexpectedException(QueueClientException):
    def __init__(self, msg=""):
        self.msg = msg


class QueueClientReceivingException(QueueClientException):
    pass
