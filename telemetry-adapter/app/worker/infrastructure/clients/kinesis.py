import logging
from typing import Union

from aiobotocore.session import get_session
import boto3
from botocore.exceptions import ClientError

from app.worker.infrastructure.clients.exceptions import KinesisClientException

logger = logging.getLogger(__name__)


class KinesisClient:
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url

    async def put_record(
            self,
            stream_name: str,
            data: bytes,
            partition_key: str,
            sequence_number: Union[str, None],
    ) -> str:
        logger.debug(f"put record: {data}: {partition_key}: {sequence_number}")
        kwargs = {
            "StreamName": stream_name,
            "Data": data,
            "PartitionKey": partition_key,
        }
        if sequence_number is not None:
            kwargs["SequenceNumberForOrdering"] = sequence_number

        session = get_session()
        async with session.create_client("kinesis", endpoint_url=self.endpoint_url) as client:
            try:
                response = await client.put_record(**kwargs)
            except ClientError as ex:
                logger.warning(
                    f"Error while sending an event to the stream {stream_name}: "
                    f"the partition key: {partition_key}: "
                    f"the sequence number: {sequence_number}: "
                    f"data: {data}: exception: {ex}"
                )
                raise KinesisClientException from ex

        return response["SequenceNumber"]
