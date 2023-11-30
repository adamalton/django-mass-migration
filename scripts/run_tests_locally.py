#!/usr/bin/env python3

""" Builds a Docker image locally to run the tests (if it's not already built), then uses it to run
    the massmigration tests.
"""

import os
import subprocess
import sys


IMAGE_NAME = "django-mass-migrations-test"


def abort(msg):
    print(f"🚨 {msg}")
    sys.exit(1)


def check_have_docker():
    try:
        subprocess.check_call(["which", "docker"])
    except subprocess.CalledProcessError:
        abort(
            "It looks like you don't have the 'docker' command installed. "
            "This utility script uses Docker to run the tests."
        )


def project_folder():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(scripts_dir)


def dockerfile_path():
    return os.path.join(project_folder(), "testing", "Dockerfile")


def image_exists():
    output = subprocess.check_output(["docker", "images", "-q", IMAGE_NAME])
    return bool(output.strip())


def build_image():
    subprocess.check_call([
        "docker",
        "build",
        "-t",
        IMAGE_NAME,
        "--file",
        dockerfile_path(),
        project_folder(),
    ])


def run_tests():
    subprocess.check_call(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{project_folder()}/massmigration:/code/massmigration",
            IMAGE_NAME,
            *sys.argv[1:],
        ],
        cwd=project_folder(),
    )


def main():
    check_have_docker()
    if not image_exists():
        build_image()
    run_tests()


if __name__ == '__main__':
    main()
