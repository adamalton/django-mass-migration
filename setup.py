from setuptools import setup, find_packages
import os

NAME = "massmigration"
PACKAGES = find_packages()
DESCRIPTION = "Django app for long-running data migrations"
LONG_DESCRIPTION = open(os.path.join(os.path.dirname(__file__), "README.md")).read()
URL = "https://github.com/adamalton/django-mass-migration"
AUTHOR = "Adam Alton"

# TODO: possibly make the dependency on djangae optional
EXTRAS = {}


setup(
    name=NAME,
    version="{{VERSION_PLACEHOLDER}}",
    packages=PACKAGES,
    author=AUTHOR,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords=["django", "djangae", "django-gcloud-connectors", "Google App Engine"],
    url=URL,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    include_package_data=True,
    install_requires=[
        "django>=3.2,<5.0",
        "djangae>=1.1.0",
        "django-gcloud-connectors>=0.3.7",
    ],
    extras_require=EXTRAS,
    # tests_require=EXTRAS["test"],
)
