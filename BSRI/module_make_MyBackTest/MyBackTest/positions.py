class Positions:
    '''
    记录标的的权重和净值
    '''
    def __init__(self, weights = {'cash':1.0}, netval = 1, buy_commission = 2.5e-4, sell_commission = 2.5e-4 + 1e-3):
        '''
        初始化
        :param weights: 各个标的的持仓权重，字典，key为标的名，value为权重
        :param netval: 净值
        :param buy_commission: 买入手续费，默认万2.5佣金
        :param sell_commission: 卖出手续费，默认万2.5佣金+千1印花税
        '''
        self.weights = weights
        self.netval = netval
        self.buy_commission = buy_commission
        self.sell_commission = sell_commission
        self.calCashWeight()


    def calCashWeight(self):
        '''
        将未使用的权重置为现金
        '''
        non_cash_weight = 0.0
        for key in self.weights.keys():
            if not key == 'cash':
                non_cash_weight += self.weights[key]
        self.weights['cash'] = 1 - non_cash_weight


    def positionsNorm(self):
        '''
        将权重标准化到和为1，并更新净值
        '''
        s = sum(self.weights.values())
        for key in self.weights.keys():
            self.weights[key] = self.weights[key] / s
        self.netval *= s


    def delZeroWeights(self):
        '''
        删除0权重的标的
        '''
        keys = self.weights.keys()
        for key in list(keys):
            if self.weights[key] == 0:
                del self.weights[key]


    def trade(self, target_positions):
        '''
        执行交易，将权重调整至目标权重
        :param target_positions: 各个标的的目标权重，字典，key为标的名，value为权重
        '''
        ## 检查target_positions权重和为1
        target_positions = target_positions.copy()
        assert abs(sum(target_positions.values()) - 1) < 1e-8, "sum of weights should be 1."

        ## 将持仓头寸和目标头寸的标的名统一起来
        pos_keys = set(self.weights.keys())
        target_pos_keys = set(target_positions.keys())
        for key in pos_keys.difference(target_pos_keys):
            target_positions[key] = 0.0
        for key in target_pos_keys.difference(pos_keys):
            self.weights[key] = 0.0

        ## 逐个标的进行交易
        sale_weight = 0          # 总卖出额
        buy_weight = 0           # 总买入额
        for key in self.weights.keys():
            if key == 'cash':
                pass
            else:
                diff_weight = target_positions[key] - self.weights[key]
                if diff_weight > 0:        # 需要买进, 用现金买入，花费手续费
                    buy_weight += diff_weight
                    self.weights['cash'] -= diff_weight * (1 + self.buy_commission)
                    self.weights[key] = target_positions[key]
                else:                      # 需要卖出，卖出获得现金，花费手续费
                    sale_weight += abs(diff_weight)
                    self.weights['cash'] += abs(diff_weight) * (1 - self.sell_commission)
                    self.weights[key] = target_positions[key]

        ## 标准化，检查权重和为1
        self.positionsNorm()
        self.delZeroWeights()
        assert abs(sum(self.weights.values()) - 1) < 1e-8, "sum of weights should be 1."
        turnover = buy_weight + sale_weight    # 换手率
        return turnover

    def update(self, ret):
        '''
        根据标的收益率更新持仓标的的权重和净值
        :param ret: 标的收益率，字典，key为标的名，value收益率
        '''
        ret['cash'] = 0                       # 现金收益率设置为0
        for key in self.weights.keys():       # 根据收益率更新
            self.weights[key] *= (1 + ret[key])

        ## 标准化，检查权重和为1
        self.positionsNorm()
        self.delZeroWeights()
        assert abs(sum(self.weights.values()) - 1)  < 1e-8, "sum of weights should be 1."


# ##test class
# pos = Positions(weights = {'stock1':0.3, 'stock2':0.4}, netval = 1)
# pos.weights
# pos.netval
#
# target_pos = {'stock1':0.5, 'stock3':0.4, 'cash':0.1}
# pos.trade(target_pos)
# pos.weights
# pos.netval
# pos.update({'stock1':0.2, 'stock3':0.1})
# pos.weights
# pos.netval