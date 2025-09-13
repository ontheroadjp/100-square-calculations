from setuptools import setup, find_packages

setup(
    name='100-square-calculations',
    version='0.1.0',
    packages=find_packages(),
    py_modules=['100masu'],  # Specify 100masu.py as a module
    install_requires=[
        'reportlab',
    ],
    entry_points={
        'console_scripts': [
            '100masu = 100masu:main',
        ],
    },
    author='ontheroadjp',
    description='A tool to generate 100-square calculation worksheets in PDF format.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ontheroadjp/100-square-calculations',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
