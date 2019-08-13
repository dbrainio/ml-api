from pydantic import BaseModel

import service
from common import app


class SquareResult(BaseModel):
    result: int


@app.get("/square/{value}", response_model=SquareResult)
def get_square(value: float):
    return SquareResult(
        result=service.square.rpc_call(value)
    )
