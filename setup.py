import setuptools

with open('requirements.txt', 'r') as f:
    install_requires = f.read().splitlines()

setuptools.setup(name='extractDataModel',
                 packages=['ALICEO2includeFile.py', 'extractDataModel'],
                 install_requires=install_requires)
