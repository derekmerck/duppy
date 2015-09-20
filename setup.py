"""
Derek's Utility Package for Python
Merck, Summer 2015

[Derek Merck](derek_merck@brown.edu)

<https://github.com/derekmerck/duppy>

Dependencies: Numpy, matplotlib

See README.md for usage, notes, and license info.


## Distribution to a pypi server:

```
$ pandoc --from=markdown --to=rst --output=README.rst README.md
$ python setup.py sdist
$ python setup.py register [-r https://testpypi.python.org/pypi]
$ python setup.py sdist upload  [-r https://testpypi.python.org/pypi]
```
"""

import os

from setuptools import setup

__package__ = "duppy"
__description__ = "Derek's Utility Package for Python"
__url__ = "https://github.com/derekmerck/duppy"
__author__ = 'Derek Merck'
__email__ = "derek_merck@brown.edu"
__license__ = "MIT"
__version_info__ = ('0', '0', '1')
__version__ = '.'.join(__version_info__)

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

# # README.md is preferred
# long_desc = read('README.md')
# # pypi requires a README.rst, so we create one with pandoc and include it in the source distribution
# if os.path.exists('README.rst'):
#     long_desc = read('README.rst')

setup(
    name=__package__,
    description=__description__,
    author=__author__,
    author_email=__email__,
    version=__version__,
    # long_description=long_desc,
    url=__url__,
    license=__license__,
    py_modules=["PyroNode", "SatisfiableSet", "SMSMessenger"],
    include_package_data=True,
    zip_safe=True,
    install_requires=['Pyro4', 'PyYAML', 'Numpy'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: Medical Science Apps.'
    ]
)