import BSRI
sig = BSRI.rundaily.rundaily(Bname='上证50', Sname='中证500',
                             sender = 'xxx@163.com',  # your 163 email to send email
                             senderpw = "password",   # password of your 163 email
                             receiver = "yyy@qq.com", # your email to receive email
                             gap = 2, nemail = 3)
sig.sendMsg()