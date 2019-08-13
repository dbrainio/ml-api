import logging

from fastapi import FastAPI

from ml2api.rpc import RPCWrapper

logging.basicConfig(level=logging.INFO)

rpc = RPCWrapper('amqp://admin:j8XfG9ZDT5ZZrWTzw62q@queue')
app = FastAPI(debug=True, title='Docr-v3 api', version='1.0.0')
