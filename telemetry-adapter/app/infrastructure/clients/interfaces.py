from abc import ABC, abstractmethod


class QueueClient(ABC):
    @abstractmethod
    def get_messages(self):
        pass

    @abstractmethod
    def delete_message(self, id_):
        pass
