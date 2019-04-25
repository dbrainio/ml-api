import collections
import io
import json
import re
import traceback
from base64 import b64encode, b64decode

import imageio
import numpy
import yaml
from aiohttp import web

__all__ = ['routes', 'run']

routes = web.RouteTableDef()


def data_base64_hook(obj):
    if isinstance(obj, str):
        try:
            if re.match('^data:image/(png|jpeg);base64,', obj):
                s = obj.strip().split(',', 1)[1].encode()
                data = b64decode(s)
                return imageio.imread(data)
            elif obj.startswith('data:application/octet-stream;base64,'):
                s = obj.strip().split(',', 1)[1].encode()
                data = b64decode(s)
                return io.BytesIO(data)
        except:
            pass  # it' okay here
    elif isinstance(obj, list):
        for i, el in enumerate(obj):
            if isinstance(el, str):
                obj[i] = data_base64_hook(el)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, str):
                obj[key] = data_base64_hook(val)
    return obj


def req_cast_from_str(s):
    try:
        obj = json.loads(s)
        return data_base64_hook(obj)
    except:
        pass  # yes, it's really okay ^_^

    try:
        ss = io.StringIO(s)
        obj = yaml.safe_load(ss)
        return data_base64_hook(obj)
    except:
        pass  # ok here

    return data_base64_hook(s)


def get_ext(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[-1]
    return None


def req_cast_from_filefield(f):
    if f.content_type.startswith('image/'):
        return imageio.imread(f.file)
    if get_ext(f.filename) in {'jpg', 'jpeg', 'png'}:
        return imageio.imread(f.file)

    if f.content_type == 'application/json':
        obj = json.load(f.file)
        return data_base64_hook(obj)
    if get_ext(f.filename) in {'json', 'js'}:
        obj = json.load(f.file)
        return data_base64_hook(obj)

    if 'yaml' in f.content_type:
        obj = yaml.safe_load(f.file)
        return data_base64_hook(obj)
    if get_ext(f.filename) in {'yaml', 'yml'}:
        obj = yaml.safe_load(f.file)
        return data_base64_hook(obj)

    return f.file.read()


async def post_to_kwargs(request):
    if request.content_type == 'application/json':
        obj = await request.json()
        return data_base64_hook(obj)
    # try:
    #     data = await request.text()
    #     _data = req_cast_from_str(data)
    #     if data != _data:
    #         return _data
    # except:
    #     pass  # it's okay here

    data = await request.post()
    results = dict()
    counts = collections.Counter()
    for key, val in data.items():
        if isinstance(val, str):
            val = req_cast_from_str(val)
        if isinstance(val, web.FileField):
            val = req_cast_from_filefield(val)
        counts[key] += 1
        count = counts[key]
        if count == 1:
            results[key] = val
        elif count == 2:
            results[key] = [results[key], val]
        else:
            results[key].append(val)
    return results


def resp_cast_from_numpy_array(a, base64=False):
    bs = io.BytesIO()
    imageio.imwrite(bs, a, 'PNG')
    img = bs.getvalue()
    if base64:
        return 'data:image/png;base64,' + b64encode(img).decode()
    return img


def resp_cast_from_file(f):
    try:
        data = f.read()
    finally:
        f.close()
    if isinstance(data, bytes):
        return 'data:application/octet-stream;base64,' + b64encode(
            data).decode()
    return data


def json_encoder_hooks(obj):
    if isinstance(obj, numpy.ndarray):
        return resp_cast_from_numpy_array(obj, base64=True)
    if hasattr(obj, 'read') and hasattr(obj, 'close'):
        return resp_cast_from_file(obj)

    raise TypeError


def result_to_response(result):
    if isinstance(result, numpy.ndarray):
        img = resp_cast_from_numpy_array(result)
        return web.Response(body=img, content_type='image/png')
    if hasattr(result, 'read') and hasattr(result, 'close'):
        try:
            data = result.read()
        finally:
            result.close()
        if isinstance(data, bytes):
            return web.Response(
                body=data, content_type='application/octet-stream')
        return web.Response(body=data.encode(), content_type='text/plain')
    dumps = json.JSONEncoder(default=json_encoder_hooks, indent=4).encode
    return web.json_response(result, dumps=dumps)


def cast_middleware(model):
    @web.middleware
    async def _cast_middleware(request, handler):
        try:
            if request.method != 'POST':
                return await handler(model)
            kwargs = await post_to_kwargs(request) or dict()
            result = await handler(model, request, **kwargs)
            return result_to_response(result)
        except web.HTTPException:
            raise
        except:
            error = traceback.format_exc()
            return web.json_response({'error': error}, status=500)

    return _cast_middleware


def healthcheck(request):
    return web.Response(status=204)


def run(model_factory, config=None, **kw):
    if config:
        with open(config) as f:
            config = yaml.load(f)
    else:
        config = {}
    config.update(kw)
    model = model_factory(**config)
    app = web.Application(
        middlewares=[
            cast_middleware(model),
        ]
    )
    app.add_routes(routes)
    app.add_routes([
        web.get('/healthcheck', healthcheck)
    ])
    web.run_app(app)
