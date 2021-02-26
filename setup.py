from setuptools import setup

setup(
    name='ml2api',
    version='0.1.0',
    description='ml -> api',
    url='',
    packages=['ml2api'],
    install_requires=[
        'aiohttp==3.7.4',
        'imageio==2.5.0',
        'numpy==1.16.3',
        'PyYAML==5.1',
    ]
)
