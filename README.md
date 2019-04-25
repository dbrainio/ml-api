## Basic usage (**example.py**):

```python
from ml2api import routes, run


class DSModel:
    @routes.post('/predict')
    async def predict(self, request, **kw):
        # some logic
        return result


if __name__ == '__main__':
    run(DSModel)
```

---

## Possible input data

Now let's consider possible values of inputs & outputs.

For simplicity of curl commands we need run this first:

```bash
$ alias xcurl="curl -i -w\\n -X POST http://127.0.0.1:8080/predict"
```

##### 1. The most simple case

```bash
$ xcurl -F foo=bar
```

In terms of **example.py** this will lead to kw = `{'foo': 'bar'}`

##### 2. Multiple values with similar name

* `$ xcurl -F foo=bar -F foo=123` => `{'foo': ['bar', 123]}`

##### 3. Automatic casts of POST params from json/yaml are allowed
 
* `$ xcurl -d foo=123` => `{'foo': 123}`
* `$ xcurl -d 'foo={"bar":[123,456]}'` => `{'foo': {'bar': [123, 456]}}`

##### 4. Also json/yaml file uploads are castable

* Suppose we have foo.json: 
```json
{"foo":["bar", 123]}
```
* ... and foo.yml:
```yamlex
foo:
  - bar
  - 123
```
* `$ xcurl -F x=@foo.json` => `{'x': {'foo': ['bar', 123]}}`
* `$ xcurl -F x=@foo.yml` => `{'x': {'foo': ['bar', 123]}}`

##### 5. Images(Content-Type: image/...) automatically casted to numpy.ndarray

```bash
$ xcurl -F x=@img.jpg
```
=>
```python
{'x': Array([[...]], dtype=uint8)}
```

##### 6. Cast application/octet-stream to binary file-like object

```bash
$ xcurl --data-urlencode x="data:application/octet-stream;base64,eyJmb28iOlsiYmFyIiwgMTIzXX0K"
```
=>
```python
{'x': <_io.BytesIO object at 0x7fb77b69f888>}
```

##### 7. Cast image/* to binary file-like object

```bash
$ xcurl --data-urlencode x="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAYAAACp8Z5+AAAARklEQVR42gXBQQ5AMBBA0a+mFk2wxtL9T1UiYTVIk1rMeK9RVT+2HYBpmQlmRlcqo0PAke86ecpNfiNrPyCWEipCtYDFlh/3VBqoiCSbdQAAAABJRU5ErkJggg=="
```
=>
```python
{'x': Array([[[241, 241, 241, 255],
        [216, 213, 214, 255],
        [216, 213, 214, 255],
        [241, 240, 240, 255]],

       [[239, 239, 239, 255],
        [222, 203, 207, 255],
        [231, 212, 214, 255],
        [243, 240, 239, 255]],

       [[233, 218, 217, 255],
        [209, 193, 193, 255],
        [193, 191, 198, 255],
        [228, 225, 228, 255]],

       [[231, 228, 227, 255],
        [194, 197, 197, 255],
        [186, 195, 200, 255],
        [226, 230, 231, 255]]], dtype=uint8)}
```

##### 8. Also all of these casts can be used together

```bash
$curl \
	-F x=@img.jpg \
	-F y=@reqs.json \
	-F z=@reqs.yml \
	-F a=123 \
	-F b=xyz \
	-F 'c={"foo":["bar",123]}'
```
=>
```python
{
	'x': Array([[...]], dtype=uint8),
	'y': {'foo': ['bar', 123]},
	'z': {'foo': ['bar', 123]},
	'a': 123,
	'b': 'xyz',
	'c': {'foo': ['bar', 123]}
}
```

---

## Possible output data

Now we will consider how output values are casted.

##### 1. Cast to json

* Return values are trying to be casted to json:
```python
return 123, 'foo', {'bar': 123}
```
=>
```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 54
Date: Tue, 23 Apr 2019 19:52:08 GMT
Server: Python/3.6 aiohttp/3.5.4

[
    123,
    "foo",
    {
        "bar": 123
    }
]
```

* numpy.ndarray objects casted data:image/png:
```python
return {'img': Array([[...]])}
```
=>
```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 657299
Date: Tue, 23 Apr 2019 20:02:14 GMT
Server: Python/3.6 aiohttp/3.5.4

{
    "img": "data:image/png;base64,iVBORw0KG...SUVORK5CYII="
}
```

* binary file-like objects casted data:application/octet-stream:
```python
return {'data': open('foo.json', 'rb')}
```
=>
```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 83
Date: Tue, 23 Apr 2019 20:13:09 GMT
Server: Python/3.6 aiohttp/3.5.4

{
    "data": "data:application/octet-stream;base64,eyJmb28iOlsiYmFyIiwgMTIzXX0K"
}
```

* text file-like objects casted to text:
```python
return {'data': open('foo.json', 'r')}
```
=>
```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 44
Date: Tue, 23 Apr 2019 20:16:06 GMT
Server: Python/3.6 aiohttp/3.5.4

{
    "data": "{\"foo\":[\"bar\", 123]}\n"
}
```

##### 2. Cast to image/png

If return single numpy.ndarray object, then it will be casted to image/png.

```python
return Array([[...]])
```
=>
```
HTTP/1.1 200 OK
Content-Type: image/png
Content-Length: 492944
Date: Tue, 23 Apr 2019 20:19:07 GMT
Server: Python/3.6 aiohttp/3.5.4

<binary data here>
```

##### 3. Cast to application/octet-stream

If return single binary file-like object, then it will be casted to
application/octet-stream.

```python
return open('foo.json', 'rb')
```
=>
```
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: 21
Date: Tue, 23 Apr 2019 20:25:43 GMT
Server: Python/3.6 aiohttp/3.5.4

{"foo":["bar", 123]}
```

##### 4. Cast to text/plain

If return single text file-like object, then it will be casted to text/plain.

```python
return open('foo.json', 'r')
```
=>
```
HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: 21
Date: Tue, 23 Apr 2019 20:28:53 GMT
Server: Python/3.6 aiohttp/3.5.4

{"foo":["bar", 123]}
```
