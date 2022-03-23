import io

from setuptools import find_packages, setup

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="LouisDeLaTech",
    version="1.0.0",
    url="https://github.com/lyon-esport/LouisDeLaTech",
    license="CeCILL v2.1",
    maintainer="Lyon e-Sport",
    maintainer_email="dev@lyon-esport.fr",
    description="LouisDeLaTech is a discord bot manager for Lyon e-Sport",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8,<3.10",
    install_requires=[
        "discord.py==1.7.3",
        "toml==0.10.2",
        "Jinja2==3.0.3",
        "discord.py==1.7.3",
        "google-api-python-client==2.42.0",
        "google-auth-httplib2==0.1.0",
        "pyotp==2.6.0",
        "tortoise-orm==0.18.1",
        "aiosqlite==0.16.1",
        "cryptography==36.0.2",
        "sentry-sdk==1.5.7",
    ],
    extras_require={
        "dev": ["pre-commit==2.17.0"],
    },
)
