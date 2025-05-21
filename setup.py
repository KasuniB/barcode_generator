# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    install_requires = f.read().strip().split('\n')

setup(
    name='barcode_generator',
    version='0.0.1',
    description='Individual Item Barcode Generator',
    author='KasuniB',
    author_email='kasunimoses@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
