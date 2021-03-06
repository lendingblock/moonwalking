import os
from setuptools import setup, find_packages

import moonwalking

NAME = 'moonwalking'


def read(name):
    filename = os.path.join(os.path.dirname(__file__), name)
    with open(filename) as fp:
        return fp.read()


def requirements(name):
    install_requires = []
    dependency_links = []

    for line in read(name).split('\n'):
        if line.startswith('-e '):
            link = line[3:].strip()
            if link == '.':
                continue
            dependency_links.append(link)
            line = link.split('=')[1]
        line = line.strip()
        if line:
            install_requires.append(line)

    return install_requires, dependency_links


meta = dict(
    version=moonwalking.__version__,
    description=moonwalking.__doc__,
    name=NAME,
    long_description=read("readme.md"),
    long_description_content_type='text/markdown',
    license="BSD",
    maintainer_email='admin@lendingblock.com',
    url='https://github.com/lendingblock/moonwalking',
    python_requires='>=3.6.0',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=requirements('dev/requirements.txt')[0],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities'
    ]
)


if __name__ == '__main__':
    setup(**meta)
