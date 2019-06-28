# BSRI
big/small rotation index 


This repository provides two python packages for big/small rotation strategy.
1) MyBackTest
This package provides a framwork to conduct backtest in BackTest Class and an eval Class to evaluate the performance of strategy with several commonly used measurements.

To install this package, 

cd \BSRI\module_make_MyBackTest\dist\MyBackTest-1.0

python setup.py install


2) BSRI
This package provides a GetDataTushare Class to get history transaction data from tushare, and a getRealData Class to get real-time transaction data from sina, as well as a rundaily Class to generate trading signals in real time and send signals with email.

To install this package, 

cd \BSRI\module_make_BSRI\dist\BSRI-1.0

python setup.py install

The python file conductbacktest is an example of conducting backtest with MyBackTest package.
The python file testsendemail is an example of sending real-time signals with BSRI package.
