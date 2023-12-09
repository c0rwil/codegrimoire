from setuptools import setup, find_packages

setup(
    name='code-grimoire',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'fastapi',
        'uvicorn',
        'PyGithub'  # Add all your dependencies here
    ],
    entry_points={
        'console_scripts': [
            'code-grimoire = src.api:run',  # Adjust with your module and function
        ],
    },
)
