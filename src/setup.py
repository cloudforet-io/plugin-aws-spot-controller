from setuptools import setup, find_packages
 
with open('VERSION', 'r') as f:
    VERSION = f.read().strip()
    f.close()
 
setup(
    name='plugin-aws-spot-scheduler-controller',
    version=VERSION,
    description='AWS plugin for spot automation',
    long_description='',
    author='Jin',
    author_email='sj0307.lee@samsung.com',
    packages=find_packages(),
    install_requires=[
        'spaceone-core',
        'spaceone-api',
        'spaceone-tester',
        'boto3',
        'schematics'
    ],
    zip_safe=False,
)
