from datetime import datetime
from typing import List

from pydantic import BaseModel, IPvAnyAddress, PositiveInt, UUID4


class EventStreamerException(Exception):
    pass


class NewProcesses(BaseModel):
    cmdl: str
    user: str


class NetworkConnections(BaseModel):
    source_ip: IPvAnyAddress
    destination_ip: IPvAnyAddress
    destination_port: PositiveInt


class Events(BaseModel):
    new_process: List[NewProcesses]
    network_connection: List[NetworkConnections]


class Submission(BaseModel):
    submission_id: UUID4
    device_id: UUID4
    time_created: datetime
    events: Events
