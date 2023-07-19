from setuptools import setup, find_packages

description = open("README.rst").read()

setup(
    name="python-simva-can",
    url="https://github.com/minhyuk/simva-can.git",
    version=0.1,
    packages=find_packages(),
    author="Minhyuk Kwon",
    author_email="minhyuk@suresofttech.com",
    description="Python-CAN Interface for SimVA",
    keywords="CAN UDP simva remote",
    long_description=description,
    license="MIT",
    platforms=["any"],
    package_data={
        "can_remote": ["web/index.html", "web/assets/*"]
    },
    entry_points={
        "can.interface": [
            "simva=simva_can.simvabus:SimVABus",
        ]
    },
    install_requires=["python-can>=3.0.0"]
)
