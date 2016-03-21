from setuptools import setup


setup(
    name='gun',
    version='0.0.1',
    py_modules=['gun'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        gun=gun:cli
    ''',
)
