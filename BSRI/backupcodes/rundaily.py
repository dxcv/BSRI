import getdata
import pandas as pd
import os
import numpy as np
import talib as tl
import datetime
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import matplotlib.pyplot as plt
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.sans-serif'] = ['SimHei']
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


class rundaily:
    '''
    根据实时指数数据计算交易信号并发送邮件
    '''
    def __init__(self, Bname, Sname, MAlen = 15,
                 update = True,
                 datapath = os.path.join(os.getcwd(),'data'),
                 token = '82d980384ae4f29eef88403c0c6e26d3e808b5c91e2ff3d22bbfa783',
                 pct = 0.04, nticks = 100,
                 sender = 'hesh22@163.com',
                 senderpw = "",
                 receiver = "1649006808@qq.com",
                 gap = 180, nemail = 3):
        '''
        初始化
        :param Bname: 大盘指数名称
        :param Sname: 小盘指数名称
        :param MAlen: 计算均线用的期数
        :param update: 是否更新数据库
        :param datapath: 数据保存路径
        :param token: tushare获取数据用的token
        :param pct: 展示决策区域的边界时坐标轴上下限百分比
        :param nticks: 展示决策区域的边界时tick的个数
        :param sender: 发送邮件使用的邮箱(163邮箱)
        :param senderpw: 发送邮件使用的邮箱的密码
        :param receiver: 接受邮件使用的邮箱
        :param gap: 发送邮件的时间间隔
        :param nemail: 发送邮件的次数
        '''
        self.Bname = Bname
        self.Sname = Sname
        self.MAlen = MAlen
        self.update = update
        self.datapath = datapath
        self.token = token
        self.pct = pct
        self.nticks = nticks
        self.sender = sender
        self.senderpw = senderpw
        self.receiver = receiver
        self.gap = gap
        self.nemail = nemail

        ## 使用tushare更新数据
        if self.update:
            try:
                gdt = getdata.GetDataTushare(token=self.token, datapath=self.datapath)
                gdt.updateAllData()
            except:
                print("Update data from Tushare failed. The previous data is used.")
        else:
            print("The previous data is used.")

        ## 导入大小盘指数数据
        self.importData()

        ## 连接邮箱服务器
        self.connectEmailServer()


    def importData(self):
        '''
        导入大小盘指数数据
        '''
        try:
            dataB = pd.read_csv(open(os.path.join(self.datapath, self.Bname + '.csv')), index_col=1, parse_dates=True)
            dataS = pd.read_csv(open(os.path.join(self.datapath, self.Sname + '.csv')), index_col=1, parse_dates=True)

            dataB = dataB['close']
            dataS = dataS['close']
            n = min(len(dataB), len(dataS))
            self.dataB = dataB[-n:]
            self.dataS = dataS[-n:]
            print("Import index data successfully.")

            ## 如果realdata和已有数据重复（当收盘后就会出现这种情况），则去掉最后一天的数据
            realdata = getdata.getRealData(self.Bname, self.Sname).getData()
            if (abs(realdata[self.Bname] - self.dataB.values[-1]) < 1e-3) and \
                    (abs(realdata[self.Sname] - self.dataS.values[-1]) < 1e-3):
                self.dataB = self.dataB[:-1]
                self.dataS = self.dataS[:-1]
                print("Remove the index data of the last data.")

            ## 增加一行index
            self.index_extend = list(self.dataB.index)
            self.index_extend.append(self.dataB.index[-1] + datetime.timedelta(days=1))
        except:
            print("Import index data failed.")
            raise IOError


    def connectEmailServer(self):
        '''
        连接邮箱服务器
        :return:
        '''
        try:
            self.email_server = smtplib.SMTP("smtp.163.com", port=25)  # 邮件服务器及端口号
            self.email_server.login(self.sender, self.senderpw)
            print("Connect to 163 email server successfully.")
        except:
            print("Connect to 163 email server failed.")


    def getSignalMsg(self, realB, realS, now):
        '''
        根据过去的数据和当日实时数据计算实时的信号
        :param realB: 大盘指数实时数据
        :param realS: 小盘指数实时数据
        :param now, 当前时间，datetime.datetime格式
        :return: (信号: 0:空仓，1:大盘，-1:小盘，文字信息）
        '''
        ## 加入实时数据
        dataB_ls = list(self.dataB.values)
        dataB_ls.append(realB)
        dataB = np.array(dataB_ls)
        dataS_ls = list(self.dataS.values)
        dataS_ls.append(realS)
        dataS = np.array(dataS_ls)

        ## 计算均线
        BS = np.log(dataB) - np.log(dataS)
        BS_EMA = tl.EMA(BS, self.MAlen)
        B_EMA = tl.EMA(dataB, self.MAlen)
        S_EMA = tl.EMA(dataS, self.MAlen)

        ## 画出均线运行情况
        now = now.strftime('%Y-%m-%d %H:%M:%S')
        plotdata = pd.DataFrame([dataB, B_EMA, dataS, S_EMA, BS, BS_EMA]).T   #创建画图数据
        plotdata.index = self.index_extend
        plotdata.columns = ['B','B_MA','S','S_MA','BS','BS_MA']

        fig = plt.figure(figsize = (6.4,9))
        ax1 = plt.subplot(311)
        ax2 = plt.subplot(312)
        ax3 = plt.subplot(313)
        ax1.plot(plotdata['B'][-120:])
        ax1.plot(plotdata['B_MA'][-120:])
        ax1.legend([self.Bname, '均线'])
        ax1.set_title(self.Bname + " (" + now  + ")")

        ax2.plot(plotdata['S'][-120:])
        ax2.plot(plotdata['S_MA'][-120:])
        ax2.legend([self.Sname, '均线'])
        ax2.set_title(self.Sname + " (" + now  + ")")

        ax3.plot(plotdata['BS'][-120:])
        ax3.plot(plotdata['BS_MA'][-120:])
        ax3.legend(['指数对数差', '均线'])
        ax3.set_title(self.Bname + "-" + self.Sname + " (" + now  + ")")
        fig.tight_layout()
        figpath = os.path.join(self.datapath, "MAs.png")
        plt.savefig(figpath)
        plt.close()

        ## 计算信号
        B_over_MA = dataB[-1] > B_EMA[-1]
        S_over_MA = dataS[-1] > S_EMA[-1]
        BS_over_MA = BS[-1] > BS_EMA[-1]

        ## 计算信号与文字信息
        realB = " (" + str(round(dataB[-1], 2)) + ") "
        realS = " (" + str(round(dataS[-1], 2))+ ") "
        realBS = " (" + str(round(BS[-1], 3)) + ") "
        B_EMA = " (" + str(round(B_EMA[-1], 2)) + ") "
        S_EMA = " (" + str(round(S_EMA[-1], 2)) + ") "
        BS_EMA = " (" + str(round(BS_EMA[-1], 3)) + ") "

        msg1 = '时间:' + now
        msg2 = self.Bname + realB  + '在均线' + B_EMA + (': 上方' if B_over_MA else ': 下方')
        msg3 = self.Sname + realS + '在均线' + S_EMA + (': 上方' if S_over_MA else ': 下方')
        msg4 = self.Bname + '-' + self.Sname + realBS + '对数差在均线' + BS_EMA + (': 上方' if BS_over_MA else ': 下方')

        if (not B_over_MA) and (not S_over_MA):  # 都在均线下方
            signal = 0
            msg5 = self.Bname + ' 和 ' + self.Sname + ' 都在均线下方'
            msg6 = '********空仓********'
        else:                                    # 未都在均线下方
            if BS_over_MA:    # 大盘强势
                signal = 1
                msg5 = self.Bname + ' 或 ' + self.Sname + ' 在均线上方，大盘强势'
                msg6 = '********买' + self.Bname + '********'
            else:             # 小盘强势
                signal = -1
                msg5 = self.Bname + ' 或 ' + self.Sname + ' 在均线上方，小盘强势'
                msg6 = '********买' + self.Sname + '********'

        return ((signal, [msg1,msg2,msg3,msg4,msg5,msg6], figpath))


    def __calLastEMA(self):
        '''
        计算过去的数据的均线
        :return:
        '''
        self.BlastEMA = tl.EMA(self.dataB.values, self.MAlen)[-1]   # 大盘指数上一期的EMA
        self.SlastEMA = tl.EMA(self.dataS.values, self.MAlen)[-1]   # 小盘指数上一期的EMA
        BS = np.log(self.dataB.values) - np.log(self.dataS.values)  #大小盘指数对数差上一期的EMA
        self.BSlastEMA = tl.EMA(BS, self.MAlen)[-1]


    def __getBoundaries(self):
        '''
        获取不同持仓信号对应的区域
        (1-alpha)*BlastEMA + alpha*realB = realB   <=>  BlastEMA = realB
        (1-alpha)*SlastEMA + alpha*realS = realS   <=>  SlastEMA = realS
        (1-alpha)*BSlastEMA + alpha*realBS = realBS   <=>  BSlastEMA = realBS = log(realB/realS) <=> realB = realS*exp(BSlastEMA)
        :param pct: 区域上限
        :param nticks: tick的个数
        '''
        ## 计算过去数据的均线
        self.__calLastEMA()

        ## xlim, ylim
        x_lower_lim = self.BlastEMA * (1 - self.pct)
        x_upper_lim = self.BlastEMA * (1 + self.pct)
        y_lower_lim = self.SlastEMA * (1 - self.pct)
        y_upper_lim = self.SlastEMA * (1 + self.pct)
        ## x ticks
        xticks = np.linspace(x_lower_lim, x_upper_lim, self.nticks)
        ## fill the area
        fig, ax = plt.subplots(1, 1)
        ax.fill_between(xticks, np.exp(-self.BSlastEMA) * xticks, y_upper_lim, color='blue', alpha=0.25)
        ax.fill_between(xticks, y_lower_lim, np.exp(-self.BSlastEMA) * xticks, color='red', alpha=0.25)
        ax.fill_between(xticks[xticks < self.BlastEMA], y_lower_lim, self.SlastEMA, color='white', alpha=1)
        ax.set_xlabel(self.Bname)
        ax.set_ylabel(self.Sname)
        return ((fig, ax))

    def __sendEmail(self, subject, msg, imgpath1, imgpath2, count = 1):
        '''
        发送电子邮件
        :param subject: 邮件主题
        :param msg: 邮件正文
        :param imgpath1: 决策边界图像路径
        :param imgpath2: 均线运行图像路径
        '''
        msg_email = MIMEMultipart('related')
        msg_email['Subject'] = subject   # 邮件主题
        msg_email['From'] = self.sender  # 发送方邮箱
        msg_email['To'] = self.receiver  # 收件人邮箱

        ## 添加邮件正文
        # 以html格式构建邮件内容
        send_str = '<html><body>'
        for x in msg:
            send_str += '<p>' + x + '</p>'
        send_str += '<center>决策边界如下图</center>'
        # html中以<img>标签添加图片，align和width可以调整对齐方式及图片的宽度
        send_str += '<img src="cid:image1" alt="image1" align="center" width=100% >'
        send_str += '<center>均线运行情况如下图</center>'
        send_str += '<img src="cid:image2" alt="image2" align="center" width=100% >'
        send_str += '</body></html>'
        content = MIMEText(send_str, 'html', 'utf-8')
        msg_email.attach(content)

        ## 添加第一张图像
        file1 = open(imgpath1, "rb")
        img_data1 = file1.read()
        file1.close()

        img1 = MIMEImage(img_data1)
        img1.add_header('Content-ID', 'image1')
        msg_email.attach(img1)

        ## 添加第二张图像
        file2 = open(imgpath2, "rb")
        img_data2 = file2.read()
        file2.close()

        img2 = MIMEImage(img_data2)
        img2.add_header('Content-ID', 'image2')
        msg_email.attach(img2)

        try:
            self.email_server.sendmail(self.sender, self.receiver, msg_email.as_string())
            print("Successfully send email " + str(count))
        except:
            print("Send email failed.")

    def sendMsg(self):
        fig, ax = self.__getBoundaries()          ## 获取决策边界的图像

        realB_ls = []
        realS_ls = []
        for i in range(self.nemail):
            ## 获取实时数据
            realdata = getdata.getRealData(self.Bname, self.Sname).getData()
            now = datetime.datetime.now()                # 获取时间
            realB = realdata[self.Bname]
            realS = realdata[self.Sname]
            realB_ls.append(realB)
            realS_ls.append(realS)

            ## 生成邮件内容
            signal, msg, figpath = self.getSignalMsg(realB, realS, now)  # 获取交易信号和文字信息
            subject = "空仓" if signal == 0 else (self.Bname if signal == 1 else self.Sname) # 邮件主题
            imgpath = os.path.join(self.datapath, "boundaries.png")                          # 图像保存路径

            ax.set_title(now.strftime('%Y-%m-%d %H:%M:%S'))
            ax.plot(realB_ls, realS_ls, 'ro-')
            plt.savefig(imgpath)
            #fig.show()
            self.__sendEmail(subject, msg, imgpath1 = imgpath, imgpath2 = figpath, count = i+1)
            time.sleep(self.gap)
        self.email_server.quit()
        print("Disconnect to 163 email server.")