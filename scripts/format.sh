#!/bin/bash

cd $(dirname $0)

black --preview ../*.py
black --preview ../tests/*.py
black --preview ../app/*.py
