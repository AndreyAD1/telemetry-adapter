from abc import ABC, abstractmethod
from typing import Mapping, Any


class QueueClient(ABC):
    @abstractmethod
    def get_messages(self) -> Mapping[str, Any]:
        pass

    @abstractmethod
    def delete_message(self, id_):
        pass
