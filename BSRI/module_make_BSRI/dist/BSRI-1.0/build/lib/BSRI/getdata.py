import tushare as ts
import os
import easyquotation


class GetDataTushare:
    '''
    从tushare获取指数数据
    token: tushare的token
    datapath: 数据保存路径
    '''
    def __init__(self,token, datapath = None):
        self.token = token
        ts.set_token(self.token)           # 设置token
        self.pro_api = ts.pro_api()        # 初始化数据接口
        print("Connect to Tushare successfully.")

        if datapath == None:               # 设置保存数据的路径
            self.datapath = os.getcwd()
        else:
            self.datapath = datapath
            if not os.path.exists(self.datapath):  #如果没有创建目录，则创建数据目录
                os.mkdir(self.datapath)

        self.IndexName2TushareCode = {     # Tushare指数代码
            '上证50': '000016.SH',
            '沪深300': '000300.SH',
            '中证500': '000905.SH',
            '中证1000': '000852.SH',
            '创业板指': '399006.SZ'
        }


    def updateAllData(self):
        '''
        更新/获取数据
        :return:
        '''
        for indexname in self.IndexName2TushareCode.keys():
            self.getIndexData(indexname)
        print('All data is updated.')
        print('Datapath: ' + self.datapath)


    def getIndexData(self, indexname):
        '''
        从Tushare获取指数数据
        indexname: 指数名称
        tushare_api: Tushare API
        :return:
        '''
        try:
            code = self.IndexName2TushareCode[indexname]
        except KeyError as e:
            print('Index Name Error!')

        data = self.pro_api.index_daily(ts_code = code)
        data = data.sort_values(by = 'trade_date')
        data.to_csv(self.datapath + '/' + indexname + '.csv', index = False)

        print('Get data for ' + indexname + ', Done.')
        return(data)





# ##test class
# gdt = GetDataTushare('82d980384ae4f29eef88403c0c6e26d3e808b5c91e2ff3d22bbfa783', 'C:\\Users\\asus\\Desktop\\BSRI\\data')
# gdt.updateAllData()



class getRealData:
    '''
    获取实时交易数据
    '''
    def __init__(self, name1, name2):
        self.IndexName2Code = {  # 指数代码
            '上证50': 'sh000016',
            '沪深300': 'sh000300',
            '中证500': 'sh000905',
            '中证1000': 'sh000852',
            '创业板指': 'sh399006'
        }
        self.name1 = name1
        self.name2 = name2
        self.code1 = self.IndexName2Code[self.name1]
        self.code2 = self.IndexName2Code[self.name2]

    def getData(self):
        '''
        使用easyquotation从新浪/腾讯/qq获取实时数据
        '''
        res = None
        for server in ['sina', 'tencent', 'qq']:
            quotation = easyquotation.use(server)
            realdata = quotation.real([self.code1, self.code2], prefix=True)

            try:
                res = {self.name1: realdata[self.code1]['now'],
                       self.name2: realdata[self.code2]['now'],
                       'date': realdata[self.code1]['date'],
                       'time': realdata[self.code1]['time']}
                break
            except:
                pass

        assert not res == None, "Network Error."
        return(res)