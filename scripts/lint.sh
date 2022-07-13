#!/bin/bash

cd $(dirname $0)

flake8 ../ --max-line-length=88 --extend-ignore=E203
