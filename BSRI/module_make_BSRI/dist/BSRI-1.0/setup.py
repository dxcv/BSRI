from setuptools import setup, find_packages

setup(
    name= 'BSRI',
    version= '1.0',
    description="Provide APIs to getdata and send trade signals for BSRI strategy",
    author='heshun',
    author_email='heshun@pku.edu.cn',
    packages=find_packages(),
    license='',
    url=''
)


# from distutils.core import setup
#
# setup(name="MyBackTest", version="1.0",
#       description="Conduct back test and evaluate performance",
#       author="heshun",
#       author_email="heshun@pku.edu.cn",
#       py_modules=['MyBackTest.backtest', 'MyBackTest.evaluation', 'MyBackTest.positions'])