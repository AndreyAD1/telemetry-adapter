from abc import ABC, abstractmethod
from typing import Mapping, Any, Iterable


class QueueClient(ABC):
    @abstractmethod
    def get_messages(self) -> Iterable[Mapping[str, Any]]:
        pass

    @abstractmethod
    def delete_message(self, id_):
        pass
