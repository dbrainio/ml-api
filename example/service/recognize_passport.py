from typing import List, Any

import numpy as np

from common import rpc


@rpc()
def recognize_passport(imgs: List[np.ndarray]) -> List[Any]:
    return [i.shape[0] / i.shape[1] for i in imgs]


if __name__ == '__main__':
    recognize_passport.rpc_consume(batch_size=4)
