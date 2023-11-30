#!/bin/sh

# A shell script to be used as the ENTRYPOINT for the Docker container for running tests so that
# the passed arguments (i.e. test name(s)) can be passed through to Django.

django-admin test massmigration $@
