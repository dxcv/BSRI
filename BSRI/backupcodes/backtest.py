import pandas as pd
import numpy as np
from .positions import Positions


class BackTest:
    def __init__(self, data, backtest_dates, strategy,
                 buy_commission = 2.5e-4, sell_commission = 2.5e-4 + 1e-3):
        '''
        :param data: 回测数据，dict，key为标的名，值为dataframe数据
        :param backtest_dates: 运行回测的日期
        :param strategy: 策略函数，输入为data和date，输出为各个标的目标权重的字典
        :param buy_commission: 买入手续费，默认万2.5佣金
        :param sell_commission: 卖出手续费，默认万2.5佣金+千1印花税
        '''
        self.data = data
        self.backtest_dates = pd.to_datetime(backtest_dates)
        self.strategy = strategy
        self.buy_commission = buy_commission
        self.sell_commission = sell_commission


    def checkWeights(self, weights):
        '''
        检查weights中是否包含na
        '''
        if weights == None:
            return True
        else:
            return any(np.isnan(np.array(list(weights.values()))))


    def getReturn(self, names, date, nextdate):
        '''
        计算两个日期间标的的收益率
        :param names: 标的名
        :param date:  回测时间点
        :param nextdate: 下一回测时间点
        :return: 各个标的收益率形成的字典
        '''
        ret = dict()
        for name in names:
            if name == 'cash':
                ret[name] = 0
            else:
                ret[name] = self.data[name]['close'][nextdate] / self.data[name]['close'][date] - 1
        return(ret)


    def getStartEndTime(self):
        '''
        根据数据的时间区间调整起止时间
        '''
        ## 找到能进行有效回测的数据的起点
        target_pos = None
        start_date = None
        for date in self.backtest_dates:
            try:
                target_pos = self.strategy(self.data, date)           # 测试数据能否根据策略计算出完整有效的目标权重
            except:
                pass

            if (not self.checkWeights(target_pos)) and (start_date == None):
                start_date = date         # 策略strategy第一次可以计算出完整有效的目标权重,作为开始日期
                break

        ## 找到能进行有效回测的数据的终点
        end_date = max(self.backtest_dates)
        for key in self.data.keys():           # 检查回测日期没有超过数据允许的日期
            data_end_date = max(self.data[key].index)
            if  end_date > data_end_date:
                end_date = data_end_date

        self.backtest_dates = self.backtest_dates[(self.backtest_dates >= start_date) & (self.backtest_dates <= end_date)]
        print("Time period for backtest is set as from " + str(start_date) + " to " + str(end_date))


    def runBackTest(self):
        self.getStartEndTime()       # 根据数据的时间区间调整起止时间

        ## 回测初始化
        pos = Positions(weights = {'cash':1.0}, netval = 1, buy_commission = 2.5e-4, sell_commission = 2.5e-4 + 1e-3)
        netval_ls = []         # 记录回测过程中净值
        positions_ls = []      # 记录回测过程中持仓情况
        turnover_ls = []       # 纪录回测过程中换手率
        # netval&weights -> trade -> netval&weights -> update -> netval&weights -> nextdate -> trade -> netval&weights
        for date, nextdate in zip(self.backtest_dates[:-1], self.backtest_dates[1:]):
            netval_ls.append([date, pos.netval])                            # 纪录交易前的净值

            target_pos = self.strategy(self.data, date)                     # 计算策略的目标权重
            turnover = pos.trade(target_pos)                                # 执行交易并计算换手率
            turnover_ls.append([date, turnover])                            # 纪录交易的换手率
            positions_ls.append([date, pos.weights.copy()])                 # 纪录交易后的持仓权重

            ret = self.getReturn(list(pos.weights.keys()), date, nextdate)  # 获取持仓标的的收益率
            pos.update(ret)                                                 # 更新下一回测时间点交易前的权重和净值


        # 纪录回测最后一天的净值，换手率和权重
        netval_ls.append([nextdate, pos.netval])
        target_pos = self.strategy(self.data, nextdate)
        turnover = pos.trade(target_pos)
        turnover_ls.append([nextdate, turnover])
        positions_ls.append([nextdate, pos.weights.copy()])
        print("Backtest done.")

        self.netval = pd.DataFrame(list(map(lambda x: x[1], netval_ls)), columns = ['netval'],
                                   index = pd.to_datetime(list(map(lambda x: x[0], netval_ls))))
        self.turnover = pd.DataFrame(list(map(lambda x: x[1], turnover_ls)), columns = ['turnover'],
                                   index = pd.to_datetime(list(map(lambda x: x[0], turnover_ls))))
        self.positions = positions_ls




# ## test class
# dataB = pd.read_csv(open('.\data\上证50.csv'), index_col=1, parse_dates=True)
# dataS = pd.read_csv(open('.\data\创业板指.csv'), index_col=1, parse_dates=True)
# data = {'上证50': dataB, '创业板指':dataS}
#
#
# import talib as tl
# def strategy(data, date):
#     dataB = data['上证50']
#     dataS = data['创业板指']
#
#     dataB = dataB[dataB.index <= date]['close']
#     dataS = dataS[dataS.index <= date]['close']
#     n = min(len(dataB), len(dataS))
#
#     dataB = dataB[-n:]
#     dataS = dataS[-n:]
#     B_S = np.log(dataB) - np.log(dataS)
#
#     BS_MA = tl.EMA(B_S.values, 15)
#     if BS_MA[-1] < B_S.values[-1]:
#         return({'上证50': 1, '创业板指':0, 'cash': 0})
#     else:
#         return ({'上证50': 0, '创业板指': 1, 'cash': 0})
#
#
# backtest_dates = data['上证50'].index
#
# bt = BackTest(data, backtest_dates, strategy, buy_commission = 2.5e-4, sell_commission = 2.5e-4 + 1e-3)
# bt.runBackTest()
#
# import matplotlib.pyplot as plt
# plt.plot(bt.netval)
# plt.show()
#
# plt.plot(bt.turnover)
# plt.show()
#
# benchmark = dataB.loc[bt.netval.index]['close'] * 0.5 + dataS.loc[bt.netval.index]['close'] * 0.5
# benchmark = benchmark / benchmark[0]