import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='ipmi',
      version='0.1.0',
      description='IPMI energy measuments tool',
      url='https://github.com/VitorRamos/cpufreq',
      author='Vitor Ramos, Alex Furtunato',
      author_email='ramos.vitor89@gmail.com, alex.furtunato@academico.ifrn.edu.br',
      license='MIT',
      packages=['ipmi'],
      install_requires=[
          'requests'
      ],
      long_description=read('README.rst'),
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Topic :: Software Development :: Build Tools",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Scientific/Engineering",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 3",
      ],
      entry_points={
          'console_scripts': [
              'ipmiread = ipmi.run:main',
          ],
      },
      keywords='ipmi energy sensor tool',
      zip_safe=False)