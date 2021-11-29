import pandas as pd
from pandasql import sqldf  # 用 SQL 语句操作 panda 模块
import os  # 处理文件模块
import shutil  # 删除非空文件夹模块
import time
from PySide2.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QIcon
from threading import Thread, Lock
from PySide2.QtCore import Signal, QObject


# 多线程处理

# 信号库
class SignalStore(QObject):
    # 定义一种信号
    progress_update = Signal(int)
    # 还可以定义其他作用的信号
    abnormal = Signal(str)  # 异常型号
    # 导入计时信号
    useTime = Signal(int)
    # 子线程让主线程弹窗
    msg = Signal(str)
    # 导入显示框添加内容信号
    show2 = Signal(int, list)


# 实例花
so = SignalStore()


# 数据处理
class DataHandle:
    def __init__(self):
        self.ui = QUiLoader().load('static/web.ui')
        # 连接信号到处理的 slot 函数
        so.progress_update.connect(self.setProgress)
        so.abnormal.connect(self.setAbnormal)
        so.useTime.connect(self.showTime)
        so.msg.connect(self.son_msg)
        so.show2.connect(self.showInfo)
        self.obj = {}  # 统计表字典
        self.importSj = 0
        self.i = 0
        self.bankLock = Lock()
        self.excelPath = ''  # 导入表的路径
        self.excel = ''  # 读取导入的表数据
        self.toin = 0  # 判断是否导入数据，0 未导入， 1 已导入
        self.ui.pushButton.clicked.connect(self.changeFileExcel)  # 选择文件事件
        self.ui.pushButton_3.clicked.connect(self.beg_in)  # 开始导入事件
        self.ui.pushButton_2.clicked.connect(self.beg_start)  # 开始校验事件
        self.start_time = ''  # 校验用时
        self.end_time = ''  # 校验用时
        self.errorNum = 0  # 校验出来有多少种错误
        self.dataQuery_son = ''
        self.errExeceltitle = 1  # 0 代表错误 1代表正确

        title = ["省", "市", "县", "乡", "村",
                 "户编号", "户主编号", "户主姓名", "户主证件号码", "家庭人口数",
                 "是否危房户", "人均纯收入", "年收入", "是否解决安全饮用水", "年度",
                 "村办公电话", "开户银行名称", "银行卡号", "识别标准", "主要致贫原因",
                 "次要致贫原因", "工资性收入", "生产经营性收入", "财产性收入", "转移性收入",
                 "计划生育金", "低保金", "五保金", "养老保险金", "生态补偿金", "其他转移性收入",
                 "生产经营性支出", "纯收入", "资产收益扶贫分红收入", "其他财产性收入",
                 "耕地面积（亩）", "水面面积", "是否加入农民专业合作组织", "退耕还林面积（亩）",
                 "林果面积（亩）", "牧草地面积", "林地面积（亩）", "是否通生产用电",
                 "是否通生活用电", "是否通广播电视", "与村主干路距离", "入户路类型", "住房面积",
                 "是否有卫生厕所", "主要燃料类型", "危房级别", "是否有龙头企业带动", "是否有创业致富带头人带动"]
        title = sorted(title, key=lambda i: len(i))  # 将表头按字符串长度进行排序
        # title = []  # 表头
        # for i in range(90):
        #     tou = f'A{i}'  # A0 - A171
        #     title.append(tou)
        self.tableTitle = title  # 表头
        # 键是错误类型也是产生的 excel 表名，值是 sql 语句

        self.sqlDictionary = {
            '01-是否加入农民专业合作组织为空的': 'select * from tables where length("是否加入农民专业合作组织") = 0;',
            '02-是否通生产用电为空的': 'select * from tables where length("是否通生产用电") = 0',
            '03-是否通生活用电为空的': 'select * from tables where length("是否通生活用电") = 0',
            '04-是否通广播电视为空的': 'select * from tables where length("是否通广播电视") = 0',
            '05-脱贫户住危房的': 'select * from tables where "是否危房户" <> "否";',
            '06-是否有卫生厕所为空的': 'select * from tables where length("是否有卫生厕所") = 0;',
            '07-脱贫户未解决安全饮用水': 'select * from tables where "是否解决安全饮用水" <> "是";',
            '08-是否有龙头企业带动': 'select * from tables where length("是否有龙头企业带动") = 0;',
            '09-是否有创业致富带头人带动': 'select * from tables where length("是否有创业致富带头人带动") = 0;',
            '10-耕地面积、林地面积、退耕还林（草）面积、林果面积、牧草地面积、水面面积有其中一项为空': """
            select * from tables where length("水面面积") = 0 or
            length("耕地面积（亩）") = 0 or
            length("牧草地面积") = 0 or
            length("林地面积（亩）") = 0 or
            length("退耕还林面积（亩）") = 0 or
            length("林果面积（亩）") = 0;       
            """,
            # '11-耕地面积小于0或大于100亩':'select * from tables where "耕地面积（亩）" + 0 > 100 or "耕地面积（亩）" + 0 < 0;',
            # '12-林地面积为空小于0或大于200亩':'select * from tables where "林地面积（亩）" + 0 > 200 or "林地面积（亩）" + 0 < 0;',
            # '13-退耕还林（草）面积小于0或大于200亩':'select * from tables where "退耕还林面积（亩）" + 0 > 200 or "退耕还林面积（亩）" + 0 < 0;',
            # '14-林果面积小于0或大于200亩':'select * from tables where "林果面积（亩）" + 0 > 200 or "林果面积（亩）" + 0 < 0;',
            # '15-牧草地面积小于0或大于100亩':'select * from tables where "牧草地面积" + 0 > 100 or "牧草地面积" + 0 < 0;',
            # '16-水面面积小于0或大于100亩':'select * from tables where "水面面积" + 0 > 100 or "水面面积" + 0 < 0;',
            '17-与村主干路距离为空或超过5公里': 'select * from tables where "与村主干路距离" + 0 > 5 or length("与村主干路距离") = 0;',
            '18-脱贫户和监测对象户人均纯收入低于4000元或为空（户年度基础信息家庭收入情况）': 'select * from tables where "人均纯收入" + 0 < 4000;',
            '19-脱贫户和监测对象工资性收入小300元或大于300000元': 'select * from tables where ("工资性收入" + 0 > 0 and "工资性收入" + 0 < 300) or "工资性收入" + 0 > 300000;',
            '20-脱贫户退耕还林（草）面积大于林地面积与牧草地面积之和': 'select * from tables where ("退耕还林面积（亩）" + 0) > (("牧草地面积" + 0 ) +("林地面积（亩）" + 0))',
            '21-主要燃料类型为空': 'select * from tables where length("主要燃料类型") = 0;',
            '22-脱贫户和监测对象有生产经营性收入但无生产经营性支出': 'select * from tables where "生产经营性收入" + 0 > 0 and "生产经营性支出" + 0 <= 0;',
            '23-脱贫户和监测对象有生态补偿金但无退耕还林面积': 'select * from tables where "生态补偿金" + 0 > 0 and "退耕还林面积（亩）" <= 0;',
            '24-脱贫户和监测对象低保金低于200元': 'select * from tables where "低保金" + 0 > 0 and "低保金" + 0 < 200;',
            '25-脱贫户和监测对象计划生育金低于100元': 'select * from tables where "计划生育金" + 0 > 0 and "计划生育金" + 0 < 100;',
            '26-脱贫户和监测对象养老保险金低于88元': 'select * from tables where "养老保险金" + 0 > 0 and "养老保险金" + 0 < 88;',
            '27-脱贫户和监测对象特困供养金(五保金)低于200元': 'select * from tables where "五保金" + 0 > 0 and "五保金" + 0 < 200;',
        }

        self.ui.progressBar_2.setRange(0, len(self.sqlDictionary))

    # 处理进度条的 slot 函数
    def setProgress(self, value):
        self.ui.progressBar_2.setValue(value)

        if value == len(self.sqlDictionary):
            self.end_time = time.time()
            QMessageBox.information(
                self.ui,
                '成功',
                f'校验数据成功,用时：{round(self.end_time - self.start_time, 0)}秒\n'
                f'共校验规则 {len(self.sqlDictionary)} 种\n'
                f'存在 {self.errorNum} 种规则错误')

    # 处理 sql 语句异常 的函数
    def setAbnormal(self, value):
        print('信号异常处理', value)
        QMessageBox.information(
            self.ui,
            '异常',
            value
        )

    # 开始校验事件
    def beg_start(self):

        if self.excelPath == '':
            self.msg('错误', '请先选择需要校验的数据表')
            return
        if self.toin != 1 or self.errExeceltitle == 0:
            self.msg('错误', '请先导入需要校验的数据表')
            return

        try:
            ml = os.getcwd() + '\\疑点数据'  # 获取当前目录
            judge = os.path.exists(ml)  # 判断疑点数据文件夹是否存在，存在就删除重新创建
            if judge:
                shutil.rmtree(ml)
            os.mkdir(os.getcwd() + '\\疑点数据')  # 创建疑点数据文件夹
            self.i = 0
        except PermissionError as e:
            e = str(e)
            self.msg('错误', e)
            return
        self.obj = {}
        self.ui.pushButton_2.setEnabled(False)
        self.errorNum = 0
        self.ui.progressBar_2.setValue(0)
        # 开始校验时间
        self.start_time = time.time()

        self.ui.textBrowser_3.setText('')
        self.ui.textBrowser_3.setText(f'开始校验数据{getTime()}')
        for key, value in self.sqlDictionary.items():  # 创建多线程执行 sql 语句

            self.ui.textBrowser_3.append(f'开始校验规则"{key}"')
            dataQuery_son = Thread(target=self.dataQuery, args=(key, value))
            dataQuery_son.setDaemon(True)  # 设置成守护线程，主程序退出，线程也结束
            dataQuery_son.start()

    # 开始导入事件，导入事件写为子线程
    def beg_in(self):
        self.toin = 0
        self.importSj = 0
        begt = Thread(target=self.importTime)
        begt.setDaemon(True)
        begt.start()
        self.ui.textBrowser_2.setText('')

        if self.excelPath == '':
            self.msg('错误', '请先选择需要校验的数据表')
            self.toin = 1
            return

        self.ui.progressBar.setRange(0, 2)
        self.ui.progressBar.setValue(0)

        beg = Thread(target=self.beg)
        beg.setDaemon(True)
        beg.start()
        self.ui.pushButton_3.setEnabled(False)
        self.ui.textBrowser_2.append(f'正在导入数据，请稍等')

    # 开始导入子线程
    def beg(self):
        # 导入开始时间
        begin = time.time()

        print('文件路径', self.excelPath)
        tableArr = self.excelPath.split(".")
        print("文件类型", tableArr[-1])
        if tableArr[-1] == "csv":
            ex = pd.read_csv(self.excelPath, encoding='gbk', keep_default_na=False, low_memory=False, sep=',')
            print('读取的csv')
            # labels = list(ex.columns.values)
            # print('表头',labels)

        else:
            ex = pd.read_excel(self.excelPath, keep_default_na=False)
            print('读取的excel')

        # 将 excel 读成表格形式, excel 就是要操作的数据表
        excel = pd.DataFrame(ex)
        a = list(excel.keys())

        a = sorted(a, key=lambda i: len(i))  # 将表头按字符串长度进行排序
        print("导入的表头", a)
        print("规定的表头", self.tableTitle)
        lackOf = [x for x in a if x not in self.tableTitle]  # 如果有，代表导入表头有多的字段
        muchMore = [y for y in self.tableTitle if y not in a]  # 如果有，代表导入表头有缺少的字段

        if lackOf != []:  # 存在多出的表头
            self.toin = 1  # 让导入计时停止
            self.ui.pushButton_3.setEnabled(True)
            print('toin', self.toin)
            # self.msg('错误', '表头有误')
            lackOf = " ".join(lackOf)
            so.msg.emit(f'错误,多出规定表头字段：{lackOf}')
            self.errExeceltitle = 0  # 让其表示导入未成功
            return
        if muchMore != []:  # 存在缺少的表头
            self.toin = 1  # 让导入计时停止
            self.ui.pushButton_3.setEnabled(True)
            print('toin', self.toin)
            # self.msg('错误', '表头有误')
            muchMore = " ".join(muchMore)
            so.msg.emit(f'错误,缺少规定表头字段：{muchMore}')
            self.errExeceltitle = 0  # 让其表示导入未成功
            return
        global tables
        tables = excel
        self.ui.progressBar.setValue(2)
        self.errExeceltitle = 1
        so.show2.emit(1, [self.importSj, excel.shape[0]])  # 发出导入成功信号，执行showinfo函数
        self.ui.pushButton_3.setEnabled(True)
        self.toin = 1

    # 子线程让主线程弹窗,表头有误
    def son_msg(self, str):
        arr = str.split(',')
        print(arr)
        QMessageBox.critical(
            self.ui,
            arr[0],
            arr[1]
        )

    # 弹框
    def msg(self, info, text):

        QMessageBox.critical(
            self.ui,
            info,
            text
        )

    # 选择文件点击事件,创建疑点数据文件夹
    def changeFileExcel(self):

        filePath = QFileDialog.getOpenFileName(
            self.ui,  # 父窗口对象
            "选择需要导入的 excel",  # 标题
            "",  # 起始目录
            "文件类型 (*.xlsx *.xls *.csv)"  # 选择类型过滤项，过滤内容在括号中
        )
        self.excelPath = filePath[0]  # excel 表路径
        self.ui.textBrowser.setText(self.excelPath)

    # 导入进度事件显示
    def showTime(self, time):
        self.ui.textBrowser_2.setText(f'正在导入数据，导入用时：{self.importSj}秒')

    # 导入进度显示
    def importTime(self):
        while self.toin == 0:
            self.importSj += 1
            print(f'导入用时：{self.importSj}')
            so.useTime.emit(self.importSj)
            time.sleep(1)

    # 对数据表 self.excel 进行查询处理
    def dataQuery(self, excelName, q):
        self.bankLock.acquire()
        try:

            self.i = self.i + 1
            print(f'开始查询规则：{excelName}')
            pysqldf = lambda sql: sqldf(sql, globals())  # 为了避免每次都要传入dataframes，可以定义一个lambda

            sql = q
            # try:
            df = pysqldf(sql)  # 执行 sql
            # except:
            #     print('表头有误')
            #     return '表头有误'

            print(f'表名{excelName}\n'
                  f'列数：{df.shape[1]}\n'
                  f'行数：{df.shape[0]}')

            # 如果查出来没有数据，则代表没有该项错误，不需要生成 excel 表
            if df.shape[0] > 0:
                self.errorNum += 1  # 增加一种错误类型计数
                thePath = os.getcwd() + '\\疑点数据'  # 获取存取路径
                # writer = pd.ExcelWriter(thePath + f'\\{excelName}.csv')  # 创建错误数据 excel
                writer = thePath + f'\\{excelName}.csv'  # 创建错误数据 excel
                # 将容易变成科学计数法的列保存为字符串
                for item in self.tableTitle:
                    df[item] = '="' + df[item].apply(str) + '"'

                df.to_csv(writer, float_format='{:f}'.format, columns=self.tableTitle, index=False, sep=',',
                          encoding='utf_8_sig')
                # writer.save()

            print(f'查询完成规则：{excelName}')
            # print(self.i)
            so.show2.emit(2, [excelName, df.shape[0]])  # 查询完成，发出信号

            so.progress_update.emit(self.i)

            self.obj[excelName] = df.shape[0]
            if self.i == len(self.sqlDictionary):
                print('统计表', self.obj)
                print('校验完了')
                obj = pd.DataFrame(list(self.obj.items()), columns=['错误类型', '错误条数'])
                print('obj', obj)
                obj.to_excel('疑点数据统计表.xlsx', float_format='{:f}'.format, index=False,
                             encoding='utf_8_sig')
                self.ui.textBrowser_3.append(
                    f'校验完成，共校验<span style="color:red;font-weight:bold;">{len(self.sqlDictionary)}</span>条规则')
                # self.ui.textBrowser_3.ensureCursorVisible()
                self.ui.textBrowser_3.moveCursor(self.ui.textBrowser_3.textCursor().End)
                self.ui.pushButton_2.setEnabled(True)
        except BaseException as e:
            print('错误', e)
            e = '存在异常：' + str(e)
            self.ui.pushButton_2.setEnabled(True)
            so.abnormal.emit(e)
            print("存在异常", e)  # 打印所有异常

            self.bankLock.release()
            return
        self.bankLock.release()

    # 处理导入进度显示框内容
    def showInfo(self, num, obj):
        print('执行了吗')
        if num == 1:
            self.ui.textBrowser_2.append(f'导入成功,用时 {obj[0]} 秒\n'
                                         f'共导入数据 {obj[1]} 条')
        elif num == 2:
            self.ui.textBrowser_3.append(
                f'查询完成规则：{obj[0]},存在错误数据 <span style="color:red;font-weight:bold;">{obj[1]}</span> 条')
            self.ui.textBrowser_3.moveCursor(self.ui.textBrowser_3.textCursor().End)


def getTime():
    a = time.strftime('%H:%M:%S', time.localtime(time.time()))
    # return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    return a


if __name__ == '__main__':
    # thread = Thread(target=DataHandle)
    # thread.start()

    app = QApplication([])
    # 加载 icon
    app.setWindowIcon(QIcon("static/logo.ico"))
    handle = DataHandle()
    handle.ui.show()

    app.exec_()
