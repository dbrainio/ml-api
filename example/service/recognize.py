from typing import List, Any

import numpy as np

from common import rpc


@rpc()
def recognize(imgs: List[np.ndarray]) -> List[Any]:
    return [i.shape for i in imgs]


if __name__ == '__main__':
    recognize.rpc_consume(batch_size=4)
