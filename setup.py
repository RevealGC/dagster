from setuptools import find_packages, setup

setup(
    name="geo_coding_pipeline",
    packages=find_packages(exclude=["geo_coding_pipeline_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
