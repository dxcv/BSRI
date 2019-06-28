from BSRI import getdata
import os
import pandas as pd
import talib as tl
import numpy as np
import MyBackTest
import matplotlib.pyplot as plt
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.sans-serif'] = ['SimHei']

## 获取数据
gdt = getdata.GetDataTushare(token = '82d980384ae4f29eef88403c0c6e26d3e808b5c91e2ff3d22bbfa783',
                             datapath = os.getcwd() + '/data')
gdt.updateAllData()


## 无空仓大小盘轮动策略
def strategy1(data, date, Bname, Sname, MAlen = 15):
    dataB = data[Bname]
    dataS = data[Sname]

    dataB = dataB[dataB.index <= date]['close']
    dataS = dataS[dataS.index <= date]['close']
    n = min(len(dataB), len(dataS))

    dataB = dataB[-n:]
    dataS = dataS[-n:]
    B_S = np.log(dataB) - np.log(dataS)

    BS_EMA = tl.EMA(B_S.values, MAlen)
    if BS_EMA[-1] < B_S.values[-1]:
        return({Bname: 1, Sname:0, 'cash': 0})
    else:
        return ({Bname: 0, Sname: 1, 'cash': 0})

## 有空仓大小盘轮动策略
def strategy2(data, date, Bname, Sname, MAlen = 15):
    dataB = data[Bname]
    dataS = data[Sname]

    dataB = dataB[dataB.index <= date]['close']
    dataS = dataS[dataS.index <= date]['close']
    n = min(len(dataB), len(dataS))

    dataB = dataB[-n:]
    dataS = dataS[-n:]

    B_S = np.log(dataB) - np.log(dataS)
    BS_EMA = tl.EMA(B_S.values, MAlen)
    B_EMA = tl.EMA(dataB.values, MAlen)
    S_EMA = tl.EMA(dataS.values, MAlen)

    if (dataB.values[-1]<B_EMA[-1]) and (dataS.values[-1]<S_EMA[-1]):
        return ({Bname: 0, Sname: 0, 'cash': 1})
    else:
        if BS_EMA[-1] < B_S.values[-1]:
            return ({Bname: 1, Sname: 0, 'cash': 0})
        else:
            return ({Bname: 0, Sname: 1, 'cash': 0})


## 无空仓大小盘轮动策略
def strategy3(data, date, Bname, Sname, MAlen = 15):
    dataB = data[Bname]
    dataS = data[Sname]

    dataB = dataB[dataB.index <= date]['close']
    dataS = dataS[dataS.index <= date]['close']
    n = min(len(dataB), len(dataS))

    dataB = dataB[-n:]
    dataS = dataS[-n:]
    B_S = np.log(dataB) - np.log(dataS)

    BS_EMA = tl.EMA(B_S.values, MAlen)
    if BS_EMA[-1] < B_S.values[-1]:
        return({Bname: 1, Sname:-1, 'cash': 1})
    else:
        return ({Bname: -1, Sname: 1, 'cash': 1})



##
Bname = "上证50"
Sname = "创业板指"
for Bname in ["上证50", "沪深300"]:
    for Sname in ["创业板指", "中证500", "中证1000"]:
        dataB = pd.read_csv(open('./data/'+Bname+'.csv'), index_col=1, parse_dates=True)
        dataS = pd.read_csv(open('./data/' + Sname + '.csv'), index_col=1, parse_dates=True)

        ## 用于回测的数据、日期和策略
        data = {Bname: dataB, Sname:dataS}
        backtest_dates = data[Bname].index

        for sty in ["无空仓大小盘轮动", "有空仓大小盘轮动", "多空轮动"]:
            ## 设置回测策略
            if sty == "无空仓大小盘轮动":
                def strategy(data, date):
                    return(strategy1(data, date, Bname, Sname))
            elif sty == "有空仓大小盘轮动":
                def strategy(data, date):
                    return(strategy2(data, date, Bname, Sname))
            else:
                def strategy(data, date):
                    return(strategy3(data, date, Bname, Sname))

            ## 创建保存结果的目录
            if not os.path.exists('backtest_results'):
                os.mkdir('backtest_results')
            if not os.path.exists('backtest_results/'+sty):
                os.mkdir('backtest_results/'+sty)

            print("====================================================")
            print(Bname+"-"+Sname+","+sty+"")

            ## 进行回测
            bt = MyBackTest.backtest.BackTest(data, backtest_dates, strategy,
                                              buy_commission = 2.5e-4, sell_commission = 2.5e-4 + 1e-3)
            bt.runBackTest()

            ## 计算基准指数
            bmB = dataB.loc[bt.netval.index]['close']
            bmS = dataS.loc[bt.netval.index]['close']
            benchmark = bmB / bmB[0] * 0.5 + bmS / bmS[0] * 0.5

            ## 计算策略净值评价指标
            perf = MyBackTest.evaluation.eval(bt.netval, benchmark)
            perf.runEval()

            ## 保存结果，画图
            perf.summary.to_csv('backtest_results/'+sty+"/"+Bname+"-"+Sname+"-回测评价指标.csv")
            # np.mean(bt.turnover.values)
            excess = pd.DataFrame(bt.netval.values.T[0] / benchmark.values, index = bt.netval.index)

            plt.figure(figsize=(20, 10))
            plt.plot(np.log(bt.netval), linewidth=1.5)
            plt.plot(np.log(benchmark), linewidth=1.5)
            plt.plot(np.log(excess), linewidth=1.5)
            plt.legend(['Strategy', 'Benchmark', 'Excess'], fontsize=16)
            plt.title('The Log Netvalue of Strategy and Benchmark (' + Bname + ' and ' + Sname + ')',fontsize=22)
            plt.ylabel('Log Netvalue', fontsize=14)
            plt.tight_layout()
            plt.savefig('backtest_results/'+sty+"/"+Bname+"-"+Sname+"-净值曲线.jpeg")