import logging
import pickle
import sys
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from typing import Any, List, NoReturn, Callable

import pika
from retry import retry

Message = Any
RPCHandler = Callable[[List[Message]], Any]


class RPCError(Exception):
    def __init__(self):
        ei = sys.exc_info()
        self._type = ei[0]
        self._tb = '<pre>\n' + traceback.format_exc() + '\n</pre>'

    def reraise(self):
        raise self._type(self._tb)


class BaseRPC(ABC):
    @abstractmethod
    def consume(self, batch_size: int = 1) -> NoReturn:
        pass

    @abstractmethod
    def process_batch(self, msgs: List[Message]) -> Any:
        pass

    @abstractmethod
    def __call__(self, msg: Message) -> Any:
        pass


class RabbitRPC(BaseRPC):
    def __init__(self, url: str, name: str, delay: float = 0.1):
        self._url: str = url
        self._name = name
        self._delay = delay

    @retry(pika.exceptions.AMQPConnectionError, delay=5, jitter=(1, 3))
    def consume(self, batch_size: int = 1) -> NoReturn:
        connection = pika.BlockingConnection(pika.URLParameters(self._url))
        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        channel.queue_declare(self._name, durable=True)
        try:
            while True:
                raw_msgs = []
                msgs = []
                for i in range(batch_size):
                    method, header, body = channel.basic_get(self._name)
                    if method is None:
                        break
                    logging.info([method, header, body])
                    try:
                        msg = pickle.loads(body)
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        logging.exception(e)
                        channel.basic_reject(method.delivery_tag)
                    msgs.append(msg)
                    raw_msgs.append((method, header, body))
                if not msgs:
                    time.sleep(self._delay)
                    continue
                try:
                    try:
                        responses = self.process_batch(msgs)
                    except KeyboardInterrupt:
                        raise
                    except:
                        responses = []
                        for msg in msgs:
                            try:
                                response = self.process_batch([msg])
                            except KeyboardInterrupt:
                                raise
                            except:
                                response = RPCError()
                            responses.append(response)
                    for response, (method, header, body) in zip(responses,
                                                                raw_msgs):
                        channel.basic_publish(
                            exchange='',
                            routing_key=header.reply_to,
                            properties=pika.BasicProperties(
                                correlation_id=header.correlation_id,
                            ),
                            body=pickle.dumps(response)
                        )
                        channel.basic_ack(method.delivery_tag)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logging.exception(e)
                    for method, header, body in raw_msgs:
                        channel.basic_reject(method.delivery_tag)

        except KeyboardInterrupt:
            connection.close()

    def __call__(self, msg: Message) -> Any:
        connection = pika.BlockingConnection(pika.URLParameters(self._url))
        try:
            channel = connection.channel()
            result = channel.queue_declare('', exclusive=True)
            result_queue = result.method.queue
            correlation_id = str(uuid.uuid4())

            channel.basic_publish(
                exchange='',
                routing_key=self._name,
                properties=pika.BasicProperties(
                    reply_to=result_queue,
                    correlation_id=correlation_id
                ),
                body=pickle.dumps(msg)
            )

            while True:
                method, header, body = channel.basic_get(result_queue)
                if method is None:
                    time.sleep(self._delay)
                    continue
                logging.info([method, header, body])
                channel.basic_ack(method.delivery_tag)
                if correlation_id == header.correlation_id:
                    response = pickle.loads(body)
                    if isinstance(response, RPCError):
                        response.reraise()
                    return response
        finally:
            connection.close()


class RPCWrapper:
    def __init__(
            self,
            url: str,
            delay: float = 0.1,
            rpc_class: BaseRPC = RabbitRPC
    ):
        self._url = url
        self._delay = delay
        self._rpc_class = rpc_class

    def __call__(self, name: str = None):
        def wrapper(func: RPCHandler):
            class _RPC(self._rpc_class):
                def process_batch(self, msgs: List[Message]) -> Any:
                    return func(msgs)

            rpc = _RPC(self._url, name or func.__name__, delay=self._delay)
            func.rpc_consume = rpc.consume
            func.rpc_call = rpc.__call__
            return func

        return wrapper


DefaultRPC = RPC = RabbitRPC
