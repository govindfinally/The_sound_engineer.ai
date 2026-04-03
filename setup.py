from setuptools import setup, find_packages
setup(
    name='the_sound_engineer.ai',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
        'numpy',
        'scipy',
        'pydantic'],
    description='A real-time audio analysis and recommendation system for live music performances.',    
    author='Govind Chandra Mohanty',
    author_email='govindmohanty4@gmail.com'
)   
