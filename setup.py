from setuptools import find_packages, setup

setup(
    name="procon-grassmaker",
    version="1.1.0",
    author="Masaki Kobayash",
    author_email="bayashi.cl@gmail.com",
    install_requires=[
        "requests",
        "bs4",
        "GitPython",
        "python-dateutil",
        "toml",
        "colorama",
        "colorlog",
        "dacite",
        "pandas",
        "dukpy",
    ],
    packages=find_packages(exclude=["tests*"]),
    entry_points={
        "console_scripts": ["procon-grassmaker = procon_grassmaker.main:main"]
    },
)
