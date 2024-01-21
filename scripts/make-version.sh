#! /bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

GIT_TAG=$(git describe --tags --exact-match 2>/dev/null)
GIT_BRANCH=$(git symbolic-ref -q --short HEAD)
GIT_SHA=$(git rev-parse --short HEAD)


echo "GIT_TAG=\"$GIT_TAG\"">> $SCRIPTPATH/../beavertails/_version.py
echo "GIT_BRANCH=\"$GIT_BRANCH\"">> $SCRIPTPATH/../beavertails/_version.py
echo "GIT_SHA=\"$GIT_SHA\"">> $SCRIPTPATH/../beavertails/_version.py