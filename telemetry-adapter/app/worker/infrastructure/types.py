from datetime import datetime
from typing import List

from pydantic import BaseModel, IPvAnyAddress, PositiveInt, UUID4


class EventStreamerException(Exception):
    pass


class NewProcess(BaseModel):
    cmdl: str
    user: str


class NetworkConnection(BaseModel):
    source_ip: IPvAnyAddress
    destination_ip: IPvAnyAddress
    destination_port: PositiveInt


class Events(BaseModel):
    new_process: List[NewProcess]
    network_connection: List[NetworkConnection]


class Submission(BaseModel):
    submission_id: UUID4
    device_id: UUID4
    time_created: datetime
    events: Events
