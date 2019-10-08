from setuptools import find_packages, setup

setup(
    name="py-scrapers",
    version="0.1.0",
    description="Small polite scrapers: book prices, a weather table and RSS/Atom feeds",
    author="Avery Lane",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.6",
    install_requires=["requests>=2.21.0", "beautifulsoup4>=4.7.1"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
