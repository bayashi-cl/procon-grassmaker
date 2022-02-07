from setuptools import setup, find_packages

setup(
    name="procon-grassmaker",
    version="0.0.2",
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
    ],
    packages=find_packages("procon_grassmaker"),
    entry_points={
        "console_scripts": ["procon-grassmaker = procon_grassmaker.main:main"]
    },
)
