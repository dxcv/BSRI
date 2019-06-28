import pandas as pd
import numpy as np


class DrawBack:
    '''
    计算回撤情况的类
    '''
    def __init__(self, netval):
        '''
        初始化
        :param netval: 净值，Series，index为日期
        '''
        self.netval = netval
        self.calDrawDown()
        self.netval = None

    def calDrawDown(self):
        '''
        计算回撤、最大回撤和最大回撤起止时间
        '''
        n = len(self.netval)
        ## 两个起止时间的收益率，行为开始时间，列为结束时间
        retij = np.dot(1 / self.netval.values.reshape((n, 1)), self.netval.values.reshape((1, n))) - 1

        ## 初始化
        drawback = np.zeros(n)       # 每天的回撤
        max_drawback = 0             # 最大回撤
        max_drawback_start = np.nan  # 最大回撤起始点
        max_drawback_end = np.nan    # 最大回撤结束点

        ## 计算最大回撤
        for j in range(1, n):
            drawback[j] = min(retij[:(j + 1), j])  # 到j时间点时的回撤
            if drawback[j] < max_drawback:
                max_drawback = drawback[j]
                max_drawback_start = np.argmin(retij[:(j + 1), j])
                max_drawback_end = j

        ## 保存结果
        self.drawback = pd.DataFrame(drawback, index = self.netval.index, columns = ["drawback"])
        self.max_drawback = max_drawback
        self.max_drawback_period = [self.netval.index[max_drawback_start], self.netval.index[max_drawback_end]]



class eval:
    '''
    计算策略的评价指标
    '''
    def __init__(self, netval, benchmark, rfree = 0.03):
        '''
        初始化
        :param netval: 净值，Dataframe，index为日期
        :param benchmark: 基准净值，Dataframe，index为日期
        :param rfree: 年化无风险利率
        '''
        ## 检查netval和benchmark的index是否匹配
        assert all(netval.index == benchmark.index), "Error Indexes of netval and benchmark do not match."

        self.rfree = rfree     # 年化无风险利率
        self.n = len(netval)   # 策略执行的期数
        self.netval = self.__adjustDataFormat(netval)           # 调整数据格式
        self.benchmark = self.__adjustDataFormat(benchmark)     # 调整数据格式

        ## 计算策略执行的时间（年为单位）
        seconds = (self.netval.index[-1] - self.netval.index[0]).total_seconds()  # 策略执行的总时间（秒为单位）
        year_seconds = (pd.to_datetime('2019-01-01 00:00:00') - pd.to_datetime('2018-01-01 00:00:00')).total_seconds()
        self.year = seconds / year_seconds


    def __adjustDataFormat(self, netval):
        '''
        调整数据格式，将Dataframe转为Series
        '''
        if len(netval.shape) > 1:
            return(pd.Series(netval.values.T[0], index=netval.index))
        else:
            return(pd.Series(netval.values, index=netval.index))

    @staticmethod
    def calRiskReturn(netval, n, year, rfree):
        ## 总收益率
        total_ret = netval.values[-1] / netval.values[0] - 1
        ## 年化收益率
        anual_ret = np.power(1 + total_ret, 1.0 / year) - 1
        ## 每一期收益率
        freq_ret = netval.values[1:] / netval.values[:-1] - 1
        ## 平均收益率
        freq_mean = np.mean(freq_ret)
        ## 波动率
        freq_std = np.std(freq_ret)
        ## 年化波动率
        anual_std = np.sqrt(n / year) * freq_std
        ## sharpe ratio
        sharpe = (anual_ret - rfree) / anual_std

        res = pd.DataFrame([total_ret, anual_ret, anual_std, sharpe, freq_mean, freq_std],
                           index=['Total Return', 'Annualized Return', 'Annualized Volatility',
                                  'sharpe', 'Average Return', 'Volatility'])
        return (res)


    def __CAPM(self):
        '''
        计算alpha, beta, information ratio和active risk
        '''
        freq_ret = self.netval.values[1:] / self.netval.values[:-1] - 1              # 策略每期收益率
        bm_freq_ret = self.benchmark.values[1:] / self.benchmark.values[:-1] - 1     # 基准每期收益率
        beta = np.cov(freq_ret, bm_freq_ret)[0, 1] / np.var(bm_freq_ret)             # beta
        alpha = (self.netval_riskreturn.loc['Annualized Return'][0] - self.rfree) - \
                beta * (self.benchmark_riskreturn.loc['Annualized Return'][0] - self.rfree) # alpha
        active_risk = np.std(bm_freq_ret - freq_ret)                                 # active risk/tracking error
        anual_active_risk = np.sqrt(self.n / self.year) * active_risk                # 年化active risk
        info_ratio = (self.netval_riskreturn.loc['Annualized Return'][0] - self.benchmark_riskreturn.loc['Annualized Return'][0]) / \
                     anual_active_risk                                               # information ratio

        self.netval_capm = pd.DataFrame([info_ratio, alpha, beta, active_risk, anual_active_risk],columns = ['strategy'],
                                        index = [ 'Information Ratio', 'alpha', 'beta', 'Active Risk', 'Annualized Active Risk'])


    def __summary(self):
        '''
        汇总结果
        '''
        ## 风险收益指标
        res = pd.concat([self.netval_riskreturn, self.benchmark_riskreturn], axis = 1)
        res.columns = ['Strategy', 'Benchmark']

        ## 最大回撤
        tmp = pd.DataFrame([[self.netval_drawback.max_drawback, self.benchmark_drawback.max_drawback]],
                           columns=['Strategy', 'Benchmark'], index=['Max Drawback'])
        res = pd.concat([res, tmp])

        ## alpha, beta, IR
        tmp = pd.DataFrame([np.nan] * self.netval_capm.shape[0], index = self.netval_capm.index)
        tmp = pd.concat([self.netval_capm, tmp], axis = 1)
        tmp.columns = ['Strategy', 'Benchmark']

        self.summary = pd.concat([res, tmp])


    def runEval(self):
        ## 计算策略的回撤情况和风险收益指标
        self.netval_drawback = DrawBack(self.netval)
        self.netval_riskreturn = eval.calRiskReturn(self.netval, self.n, self.year, self.rfree)

        ## 计算基准的回撤情况和风险收益指标
        self.benchmark_drawback = DrawBack(self.benchmark)
        self.benchmark_riskreturn = eval.calRiskReturn(self.benchmark, self.n, self.year, self.rfree)

        ## 计算alpha, beta, information ratio和active risk
        self.__CAPM()

        ## 汇总结果
        self.__summary()





## test class
# dataB = pd.read_csv(open('.\data\上证50.csv'), index_col=1, parse_dates=True)
# dataS = pd.read_csv(open('.\data\创业板指.csv'), index_col=1, parse_dates=True)
# data = {'上证50': dataB, '创业板指':dataS}
#
#
# from backtest import BackTest
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
#
# perf = eval(bt.netval,benchmark)
# perf.runEval()
# perf.summary











