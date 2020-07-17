from setuptools import setup, find_packages

setup(
    name='docker-plugin',
    packages=find_packages(),
    version='1.0.0',
    author='',
    author_email='@codilime.com',
    description='Manage Docker nodes/containers by Cloudify.',
    license='LICENSE',
    zip_safe=False,
    install_requires=['docker==2.4.2'],
)
