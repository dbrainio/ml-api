from enum import Enum
from typing import Tuple

import imageio
from fastapi import File, UploadFile
from pydantic import BaseModel

import service
from common import app


class DocType(Enum):
    passport_main = "passport_main"
    inn_person = "inn_person"


class RecognizeResult(BaseModel):
    doc_type: DocType
    result: Tuple[int, int, int]


@app.post("/recognize", response_model=RecognizeResult)
async def recognize(
        doc_type: DocType,
        image: UploadFile = File(...),
):
    img = imageio.imread(await image.read())
    return RecognizeResult(
        doc_type=doc_type,
        result=service.recognize.rpc_call(img)
    )
