#!/usr/bin/env python
#coding=utf-8
#@author: xiongyan

import wx
import wx.lib.filebrowsebutton as filebrowse
import threading
import os,random,time

cmdStr = "ping 127.0.0.1 -t"  #全局
curr_time = "0:0:0" #当前时间

def china_time():
    #switch_time_zone() #for unix
    int_time = time.gmtime(time.time() + 3600*8 )
    cn_time = time.strftime('%a, %d %b %Y %H:%M:%S +0800', int_time)
    return cn_time

class WorkerThread(threading.Thread):
    """
    This just simulates some long-running task that periodically sends
    a message to the GUI thread.
    """
    def __init__(self, threadNum, window):
        threading.Thread.__init__(self)
        self.threadNum = threadNum
        self.window = window
        self.timeToQuit = threading.Event()
        self.timeToQuit.clear()
        self.messageCount = random.randint(10,20)
        self.messageDelay = 0.1 + 2.0 * random.random()

    def stop(self):
        self.timeToQuit.set()

    def run(self):#运行一个线程
        #msg = "Thread %d iterating %d times with a delay of %1.4f " %(self.threadNum, self.messageCount, self.messageDelay)
        #wx.CallAfter(self.window.LogMessage, msg)
        global cmdStr
        print(cmdStr)
        for i in range(1, self.messageCount+1):
            self.timeToQuit.wait(self.messageDelay)
            if self.timeToQuit.isSet():
                break
            #msg = "Message %d from thread %d " % (i, self.threadNum)
            ### ---
            timeout = 3600 * 24
            import subprocess, datetime, time, signal
            start = datetime.datetime.now()
            process = subprocess.Popen(cmdStr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            
            while process.poll() is None:
                time.sleep(0.2)
                now = datetime.datetime.now()
            
                out_str = process.stdout.readline()
                wx.CallAfter(self.window.LogMessage, out_str) #输出
            
                if (now - start).seconds> timeout:
                    os.kill(process.pid, signal.SIGKILL)
                    os.waitpid(-1, os.WNOHANG)
                    
            wx.CallAfter(self.window.LogMessage, u"备份操作已成功完成,或被人为中止！") #完成
            self.stop() #中止当前线程
            ### ---
            #wx.CallAfter(self.window.LogMessage, msg)
        else:
            wx.CallAfter(self.window.ThreadFinished, self)


#----------------------------------------------------------------------
#主界面类
class BackupPanel(wx.Frame):
    back_dir = '' # backup dir
    def __init__(self):
        global curr_time
        wx.Frame.__init__(self, None, title= u"Tengfang Backup System: by xiongyan",
                            size=(640, 480) )
        self.threads = []
        self.count = 0
        
        panel = wx.Panel(self)
        path_title = wx.StaticText(panel, -1, 
                    u"请选择备份存放目录: [默认为备份在程序所在目录下,"
                    u"尽量选取非中文目录]" )

        self.startBtn = wx.Button(panel, -1, u" 开始备份 ")
        stopBtn  = wx.Button(panel, -1, u" 停止所有 threads")
        self.tc  = wx.StaticText(panel, -1, "Worker Threads: 00")
        self.log = wx.TextCtrl(panel, -1, u"备份准备中...\n\n"
                               u"若已选择好备份目录，请点击[开始备份]...\n",
                               style=wx.TE_RICH|wx.TE_MULTILINE)
        
        self.run_time = wx.StaticText(panel, -1, "%s | Time is running......" %curr_time )
        
        inner = wx.BoxSizer(wx.HORIZONTAL)
        inner.Add(self.startBtn, 0, wx.RIGHT, 15)
        inner.Add(stopBtn, 0, wx.RIGHT, 15)
        inner.Add(self.tc, 0, wx.ALIGN_CENTER_VERTICAL)
        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(path_title, 0, wx.ALL, 5)
        self.dbb = filebrowse.DirBrowseButton(
            panel, -1, size=(420, -1), changeCallback = self.dbbCallback ) #选择框
        main.Add(self.dbb, 0, wx.ALL, 5)
        
        box = wx.StaticBox(panel,-1,u"请选择要备份的项目: [因文件过多建议分开备份]\n" )
        boxSizer = wx.StaticBoxSizer(box,wx.VERTICAL)
        self.sortChoices = wx.CheckBox(panel,-1,u"数据库 mysql_backup")
        boxSizer.Add(self.sortChoices, 0,wx.ALL, 5)
        self.sortSelected = wx.CheckBox(panel,-1,u"网站程序及图片等 www_backup")
        boxSizer.Add(self.sortSelected, 0,wx.ALL, 5)
        main.Add(boxSizer,0,wx.ALL, 10)
        
        main.Add(inner, 0, wx.ALL, 5)
        main.Add(self.log, 1, wx.EXPAND|wx.ALL, 5)
        main.Add(self.run_time, 0, wx.ALL, 5)
        panel.SetSizer(main)

        self.Bind(wx.EVT_BUTTON, self.Go, self.startBtn)
        self.Bind(wx.EVT_BUTTON, self.OnStopButton, stopBtn)
        self.Bind(wx.EVT_CLOSE,  self.OnCloseWindow)

        self.UpdateCount()
        # 初始化一个wxTimer
        self.timer1 = wx.Timer(self) 
        self.Bind(wx.EVT_TIMER, self.OnTimer1Event, self.timer1) # 建立事件处理句柄
        self.timer1.Start( 1000 ) # 启动wxTimer,单位毫秒.
        #self.timer1.Stop() # 停止wxTimer
        #sb = self.CreateStatusBar(2) #创建状态栏
        #sb.SetStatusWidths([-1, 220])         
        

    def OnStartButton(self):
        self.startBtn.Disable() #禁止再点
        self.count += 1
        thread = WorkerThread(self.count, self)#创建一个线程
        self.threads.append(thread)
        self.UpdateCount()
        thread.start()#启动线程
    
    def OnStopButton(self, evt):
        self.StopThreads()
        self.UpdateCount()
        os.system('taskkill /F /IM lftp.exe')  #特别关掉
        self.startBtn.Enable() #禁止再点
        
    def OnCloseWindow(self, evt):
        self.StopThreads()
        self.Destroy()

    def StopThreads(self):#从池中删除线程
        while self.threads:
            thread = self.threads[0]
            thread.stop()
            self.threads.remove(thread)
            
    def UpdateCount(self):
        self.tc.SetLabel("Worker Threads: %d\n" % len(self.threads))
        
    def LogMessage(self, msg):#注册一个消息
        self.log.AppendText(msg)
        
    def ThreadFinished(self, thread):#删除线程
        self.threads.remove(thread)
        self.UpdateCount()
        
#---------------------------------------------------------------------
#选择框处理
    def dbbCallback(self, evt):
        self.back_dir = evt.GetString() #保存当前备份目录
        self.log.write('DirBrowseButton: %s\n' % evt.GetString())

#处理备份事件
    def Go(self, evt):
        global cmdStr
        # get current working directory
        if self.back_dir != '':
            back_dir = self.back_dir
        else:
            self.showTipPath() #提示路径
            back_dir = os.getcwd() + "/bak_dir"
            return
        back_dir = back_dir.replace('\\', '/')
        back_dir = back_dir.replace(':', '')
        print(back_dir)
        
        style = 0
        if self.sortChoices.GetValue():
            style |= 1 # "database"
        if self.sortSelected.GetValue():
            style |= 2 # "www"
        print(style)
        
        cfg = self.testConfig() #测试配置
        if cfg is None:
            self.showTip()
            return
        #print(cfg)
        
        cmdStr = "lftp\\lftp.exe -u '%s' %s -e \"mirror --verbose --ignore-time --delete-first --dereference " %(cfg[0] ,cfg[1])
        if style == 1:
            cmdStr = cmdStr + "mysql_backup/ /cygdrive/"+ back_dir + "/mysql_backup ; exit\" "
        elif style == 2:
            cmdStr = cmdStr + "www_backup/ /cygdrive/"+ back_dir + "/www_backup ; exit\" "
        elif style == 3:
            cmdStr = cmdStr + "/ /cygdrive/"+ back_dir + " ; exit\" "
        else:
            cmdStr = "" #置空以免出错
            self.showTipChs() #提示备份项
            return
            
        #print(cmdStr)
        #chg_bin_dir = "cd %s\\lftp\\" % os.getcwd()
        #chg_bin_dir = chg_bin_dir.replace('\\', '\\\\')
        #os.system(chg_bin_dir)
        #os.system(cmdStr)
        thestr = self.OnStartButton()
        if thestr == True :
            self.log.AppendText(u"备份操作成功完成！")
        #p = os.popen(cmdStr)  #replace os.system
        #thestr =  p.read()
        #self.out_log.AppendText(thestr)
        #p.close()

#----------------------------------------------------------------------
    # 需要处理事务的代码
    def OnTimer1Event(self, event): 
        curr_time = china_time() #当前时间
        self.run_time.SetLabel("%s | Time is running......" %curr_time )
        #self.SetStatusText(curr_time, 1)  #设置状态栏时间      
        pass
     
    # 提示函数1   
    def showTip(self):
        dlg = wx.MessageDialog(self, u"配置文件不存在，请检查程序目录下的config.txt文件!\n",
                            u"腾房网提醒您：",
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
        dlg.ShowModal()
        dlg.Destroy()
    
    #提示函数2    
    def showTipPath(self):
        dlg = wx.MessageDialog(self, u"请先选择备份存放目录!\n",
                            u"腾房网提醒您：",
                            wx.OK | wx.ICON_INFORMATION )
        dlg.ShowModal()
        dlg.Destroy()
         
    #提示函数3    
    def showTipChs(self):
        dlg = wx.MessageDialog(self, u"未选择想要备份的项目!\n",
                            u"腾房网提醒您：",
                            wx.OK | wx.ICON_INFORMATION )
        dlg.ShowModal()
        dlg.Destroy()
    
    # 测试配置文件
    def testConfig(self):
        config_f = "./config.txt" #配置文件
        cfg_arr  = list()
        try:
            cfg_hand = open(config_f,'r')
            list_str  = cfg_hand.readlines()
            for line in list_str:
                cfg_arr.append ( line.strip('\n') );
        except IOError:
            return None

        return cfg_arr
    
    #析构方法
    def __del__( self ):  
        os.system('taskkill /F /IM lftp.exe') 
        self.parent.Enable()
        self.Destroy()


if __name__ == '__main__':
    app = wx.App()
    frm = BackupPanel()
    frm.Show()
    app.MainLoop()