from setuptools import setup, find_packages
import webservices


setup(
    author="Jonas Obrist",
    name='webservices',
    version=webservices.__version__,
    license='BSD License',
    platforms=['OS Independent'],
    install_requires=[
        'itsdangerous',
    ],
    extras_require={
        'django':  ["django", "requests"],
        'flask': ["flask", "requests"],
        'twisted': ["twisted"],
        'consumer': ["requests"],
    },
    tests_require=[
        'twisted',
        'requests',
        'django',
        'flask',
    ],
    packages=find_packages(),
    include_package_data=False,
    zip_safe=False,
    test_suite='webservices.tests',
)
