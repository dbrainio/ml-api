from typing import Optional

import imageio
from fastapi import File, UploadFile
from pydantic import BaseModel

import service
from common import app


class RecognizePassportField(BaseModel):
    text: str
    confidence: float


class RecognizePassportResult(BaseModel):
    first_name: Optional[RecognizePassportField]
    second_name: Optional[RecognizePassportField]
    sex: Optional[RecognizePassportField]


@app.post("/recognize/passport_main", response_model=RecognizePassportResult)
async def recognize_passport(image: UploadFile = File(...)):
    img = imageio.imread(await image.read())
    return RecognizePassportResult(
        first_name=RecognizePassportField(
            text='qwe2',
            confidence=service.recognize_passport.rpc_call(img)
        ),
        second_name=RecognizePassportField(
            text='qwe2',
            confidence=service.recognize_passport.rpc_call(img)
        ),
        sex=RecognizePassportField(
            text='qwe2',
            confidence=service.recognize_passport.rpc_call(img)
        ),
    )
