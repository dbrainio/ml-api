import logging
from typing import List

from common import rpc


@rpc()
def square(values: List[float]) -> List[float]:
    logging.info(values)
    return [v ** 2 for v in values]


if __name__ == '__main__':
    square.rpc_consume(batch_size=4)
