#!/usr/bin/env python
# coding=utf-8
#@author: xiongyan
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.Utils import formatdate
import os
import codecs  #解决读取中文配置的问题
import ConfigParser  #分析配置文件模块


"""EMAIL_HOST = "smtp.exmail.qq.com"
EMAIL_USER = "test@tengfang.net"
EMAIL_PWD  = "" """
#EMAIL_POSTFIX = "tengfang.net"
#全局配置-----start
config_file="config.ini"
config = ConfigParser.ConfigParser()
config.readfp(codecs.open(config_file, "r", "utf-8-sig"))
#config.readfp(open(config_file,'r','utf-8'))
#--发件配置
EMAIL_HOST = config.get("email", "EMAIL_HOST")
EMAIL_USER = config.get("email", "EMAIL_USER")
EMAIL_PWD  = config.get("email", "EMAIL_PWD")
#全局配置-----end
ME = "腾房网<editor@tengfang.net>"


class XMail:
    ACCESSORY_FULLPATH = "" #附件路径
    ACCESSORY_NAME = "" #附件名
    data={} #存发送内容等
    TO_EMAIL=()

    #初始化
    def __init__(self, host=EMAIL_HOST, user=EMAIL_USER, pwd=EMAIL_PWD):
        self.EMAIL_SUBJECT = "尊敬的用户,您在腾房网订阅的楼盘动态已经更新"
        pass

    def sendmail(self, message):
        try:
            smtp = smtplib.SMTP(EMAIL_HOST)
            smtp.login(EMAIL_USER, EMAIL_PWD)
            smtp.sendmail(EMAIL_USER, self.TO_EMAIL, message)
            smtp.quit()
            print('email send success.')
        except Exception ,e:
            print(e)
            print('email send failed.')

    #使用MIMEText生成，注意这里用到了utf-8，因为内容有可能是中文，所以要特别指定
    def sendwithoutattachment(self, data):
        self.data = data
        self.TO_EMAIL = (data["to_email"],)
        #self.TO_EMAIL = ("a@tengfang.net","37676777@qq.com","576637108@qq.com")
        if data["body"] == "":
            body = self.getcontent(file_name="./data/default_body.txt")
        else:
            body = data["body"]
        msg = MIMEText(body, 'html','utf-8') #default: plain/html  
        self.getheader(msg)
        self.sendmail(msg.as_string())

    #getheader函数是用来设置发送者，接受者，主题和发送时间
    def getheader(self, msg):
        msg['From'] = ME
        msg['To'] = ";".join(self.TO_EMAIL)
        msg['Subject'] = self.data["title"]
        msg['Date'] = formatdate(localtime=True)

    #邮件正文
    def getcontent(self, file_name):
        path = os.getcwd()
        file = os.path.join(path, file_name)
        content = open(file, 'rb')
        data = content.read()
        try:
            data = data.decode('gbk')
        except:
            data = data.decode('gbk', 'ignore')
        content.close()
        return data

    #加附件
    def getattachment(self, msg):
        ctype, encoding = mimetypes.guess_type(self.ACCESSORY_FULLPATH)
        if ctype is None or encoding is not None:  
            ctype = 'application/octet-stream'  
        maintype, subtype = ctype.split('/', 1)

        #Formating accessory data
        data = open(self.ACCESSORY_FULLPATH, 'rb')
        file_msg = MIMEBase(maintype, subtype)
        file_msg.set_payload(data.read())
        data.close()
        encode_base64(file_msg) 
        #file_msg["Content-Type"] = ctype # if add type then return error 10054
        file_msg.add_header('Content-Disposition', 'attachment', filename = self.ACCESSORY_NAME)
        msg.attach(file_msg)


if __name__ == "__main__":
    test["body"] = "" 
    test["title"]= u"尊敬的%s,您在腾房网订阅的%s楼盘动态已有更新" \
    %("银狐", "绿地新都会")
    test["to_email"] = "37676777@qq.com"
    test["uname"] = "xiongyan"
    #以上为测试数据
    fa = XMail()
    fa.sendwithoutattachment(test)