import os
from setuptools import setup

__version__ = ()
exec(open("veritas/version.py").read())

with open("requirements.txt") as f:
    install_requires = f.readlines()

tests_require = ["nose", "responses"]

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

readme_path = os.path.join(os.path.dirname(__file__), "README.md")

# Get the long description from README.md
with open(readme_path) as readme:
    setup(
        name="Veritas",
        version=".".join([str(_) for _ in __version__]),
        packages=["veritas"],
        include_package_data=True,
        license="GPLv3",
        description="UKTI integration with Microsoft Azure AD",
        long_description=readme.read(),
        url="https://github.com/UKTradeInvestment/crm-veritas",
        download_url="https://github.com/UKTradeInvestment/crm-veritas",
        install_requires=install_requires,
        tests_require=tests_require,
        test_suite="nose.collector",
        classifiers=[
            "Operating System :: POSIX",
            "Operating System :: Unix",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Topic :: Internet :: WWW/HTTP",
        ],
    )
