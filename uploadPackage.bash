#!/usr/bin/env bash
# need to run this with python 2.7
python setup.py sdist
python setup.py bdist_wheel --universal
twine upload dist/*