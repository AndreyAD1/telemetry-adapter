import logging


logger = logging.getLogger(__file__)


class KinesisClient:
    def __init__(self, url):
        self.url = url

    def put_record(self, data_blob, partition_key, sequence_number) -> int:
        logger.debug(f"put record: {data_blob}: {partition_key}: {sequence_number}")
        return 1
