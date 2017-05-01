# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='StudDP',
    version='1.1.94',
    author='Sebastian Höffner',
    author_email='shoeffner@uos.de',
    maintainer='Maxim Schuwalow',
    maintainer_email='mschuwalow@uos.de',
    packages=['studdp'],
    install_requires=[
        "cffi >= 1.9.1",
        "cryptography >= 1.6",
        "idna >= 2.1",
        "keyring >= 10.1",
        "pyasn1 >= 0.1.9",
        "pycparser >= 2.17",
        "requests >= 2.12.3",
        "SecretStorage >= 2.3.1",
        "six >= 1.10.0",
        "python-daemon",
        "pidfile",
        "pyyaml"
    ],
    url='https://github.com/shoeffner/StudDP.git',
    license='MIT',
    description='StudIP file downloader in python',
    long_description=open('README.rst').read(),
    keywords="StudIP Downloader Osnabrueck UOS utility",
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "studdp = studdp.StudDP:main",
            "stopdp = studdp.stopDP:stop",
        ],
    },
)
