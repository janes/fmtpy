from setuptools import setup

setup(
   name='fmtpy',
   version='1.0',
   description='Realiza análises financeiras',
   author='Fábio Teixeira',
   author_email='fabiomt92@hotmail.com',
   packages=['fmtpy', 'cvmpy'],  #same as name
   install_requires=['selenium', 'bs4'], #external packages as dependencies
)



