from setuptools import setup, find_packages

setup(
    name="maxlib",
    version="0.2b0",
    packages=find_packages(),
    description="MaxLib is a reverse-library for web.max.ru",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Sudo",
    author_email="sudo@onlysq.ru",
    url="https://github.com/imsudoer/WebMaxLib",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "websockets",
        "requests",
    ],
)