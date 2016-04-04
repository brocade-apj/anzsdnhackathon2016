from setuptools import setup


setup(
    zip_safe=True,
    name='sroof',
    version='1.0',
    author='craig',
    author_email='craig@brocade.com',
    packages=[
        'srmanager',
    ],
    description='Segment Routing over OpenFlow',
    license='LICENSE',
    install_requires=[
        'networkx>=1.11',
        'xmltodict>=0.10.1',
        'websocket',
        'websocket-client',
    ]
)

