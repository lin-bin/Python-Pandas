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

        title = ["省", "市", "县", "乡", "村", "户编号", "人口编号",
                 "姓名", "性别", "出生日期", "证件类型", "证件号码",
                 "民族", "户联系电话", "成员联系电话", "年度",
                 "与户主关系", "文化程度", "在校生状况", "劳动技能", "务工时间（月）",
                 "健康状况", "政治面貌", "务工企业名称", "是否享受低保", "是否参加城镇职工基本养老保险",
                 "是否参加大病保险", "是否参加新型农村合作医疗（城乡居民基本医疗保险）", "是否参加城乡居民基本养老保险",
                 "失学或辍学原因", "是否会讲普通话", "是否参加商业补充医疗保险", "是否国外务工", "产业分类",
                 "是否接受大病医疗救助", "是否接受其他健康扶贫", "公益性岗位类型", "公益性岗位(月数)", "就业渠道",
                 "残疾类别", "务工所在地", "户主姓名", "户主证件号码", "是否参加城镇职工基本医疗保险",
                 "是否特困供养人员", "残疾证办证年度", "识别标准"]
        title = sorted(title, key=lambda i: len(i))  # 将表头按字符串长度进行排序
        # title = []  # 表头
        # for i in range(90):
        #     tou = f'A{i}'  # A0 - A171
        #     title.append(tou)
        self.tableTitle = title  # 表头
        # 键是错误类型也是产生的 excel 表名，值是 sql 语句

        self.sqlDictionary = {

            '01-身份证号码疑似有误的': """
            select * from tables WHERE (substr("证件号码",7,4) + 0) < 1900 or (substr("证件号码",7,4) + 0) >2021 or
            (substr("证件号码",11,2) + 0) > 12 or
            (

                (substr("证件号码",1,1)+0)*7+

                (substr("证件号码",2,1)+0)*9+

                (substr("证件号码",3,1)+0)*10+

                (substr("证件号码",4,1)+0)*5+

                (substr("证件号码",5,1)+0)*8+

                (substr("证件号码",6,1)+0)*4+

                (substr("证件号码",7,1)+0)*2+

                (substr("证件号码",8,1)+0)*1+

                (substr("证件号码",9,1)+0)*6+

                (substr("证件号码",10,1)+0)*3+

                (substr("证件号码",11,1)+0)*7+

                (substr("证件号码",12,1)+0)*9+

                (substr("证件号码",13,1)+0)*10+

                (substr("证件号码",14,1)+0)*5+

                (substr("证件号码",15,1)+0)*8+

                (substr("证件号码",16,1)+0)*4+

                (substr("证件号码",17,1)+0)*2

            ) % 11

            <>
            			(

            case

                when substr("证件号码",18,1)='1' then 0

                when substr("证件号码",18,1)='0' then 1

                when substr("证件号码",18,1) in ('X','x') then 2

                when substr("证件号码",18,1)='9' then 3

                when substr("证件号码",18,1)='8' then 4

                when substr("证件号码",18,1)='7' then 5

                when substr("证件号码",18,1)='6' then 6

                when substr("证件号码",18,1)='5' then 7

                when substr("证件号码",18,1)='4' then 8

                when substr("证件号码",18,1)='3' then 9

                when substr("证件号码",18,1)='2' then 10

            end

            );
            """,
            '02-身份证号码有重复的': 'select * from tables where SUBSTR("证件号码",1,18) in (SELECT SUBSTR("证件号码",1,18) FROM tables group by SUBSTR("证件号码",1,18) having count("证件号码") > 1)',
            '03-与户主关系有误的': 'select * from tables where "与户主关系" not in ("户主","配偶","之子","之女","之儿媳","之女婿","之孙子","之孙女","之外孙子","之外孙女","之父","之母","之岳父","之岳母","之公公","之婆婆","之祖父","之祖母","之外祖父","之外祖母","之兄弟姐妹","之曾孙子","之曾孙女","之侄儿","之侄女","之兄弟媳妇","之叔伯","其他")',
            '04-文化程度和在校生状况同时填写或都未填写的': 'select * from tables where (length("文化程度") <> 0 and length("在校生状况") <> 0) or (length("文化程度") = 0 and length("在校生状况") = 0);',
            '05-同一户编号下有多个户主的': 'select a.* from tables as a left join (select 户编号 from tables where "与户主关系"="户主" group by 户编号 having count(*) > 1) as b on a.户编号 = b.户编号 where a.户编号 = b.户编号 order by a.户编号',
            '06-同一户编号下有多个配偶的': 'select a.* from tables as a left join (select 户编号 from tables where "与户主关系"="配偶" group by 户编号 having count(*) > 1) as b on a.户编号 = b.户编号 where a.户编号 = b.户编号 order by 户编号',
            '07-同一户编号下没有户主的': 'select a.* from tables as a left join (select distinct "户编号" from tables where "与户主关系"="户主") as b on a."户编号" = b."户编号" where b."户编号" is null and a."户编号" <>"" order by a."户编号";',
            '08-政治面貌疑似有误的': 'select * from tables where "政治面貌" not in ("中共党员","中共预备党员","共青团员","群众");',
            '09-文化程度填写有误的': 'select * from tables where "文化程度" not in ("文盲或半文盲","小学","初中","高中","大专","本科及以上","")',
            '10-在校生状况填写有误的': 'select * from tables where "在校生状况" not in ("学龄前儿童","学前教育","小学","七年级","八年级","九年级","普通高中一年级","普通高中二年级","普通高中三年级","中职一年级","中职二年级","中职三年级","高职高专一年级","高职高专二年级","高职高专三年级","技师学院一年级","技师学院二年级","技师学院三年级","技师学院四年级","本科一年级","本科二年级","本科三年级","本科四年级","本科五年级","硕士研究生及以上","");',
            '11-健康状况为空的': 'select * from tables where length("健康状况") = 0;',
            '12-劳动技能填写有误的': 'select * from tables where "劳动技能" not in ("普通劳动力","技能劳动力","弱劳动力或半劳动力","丧失劳动力","无劳动力");',
            '13-有务工所在地没务工时间或有务工时间没务工所在地的': 'select * from tables where (length("务工所在地") > 0 and "务工时间（月）"+0 <= 0) or (length("务工所在地") = 0 and "务工时间（月）"+0 > 0);',
            '14-脱贫户有未参加大病保险的': 'select * from tables where "是否参加大病保险" <> "是";',
            '15-户联系电话有误或为空': 'select * from tables where length("户联系电话") <> 11;',
            '16-是否参加城乡居民基本养老保险为空': 'select * from tables where length("是否参加城乡居民基本养老保险") = 0;',
            '17-参加新型农村合作医疗（城乡居民基本医疗保险）与城镇职工基本医疗保险都同时填写为是或都同时填写为否': 'select * from tables where ("是否参加新型农村合作医疗（城乡居民基本医疗保险）" = "是" and "是否参加城镇职工基本医疗保险" = "是") or ("是否参加新型农村合作医疗（城乡居民基本医疗保险）" = "否" and "是否参加城镇职工基本医疗保险" = "否");',
            '18-是否参加新型农村合作医疗（城乡居民基本医疗保险）为空': 'select * from tables where length("是否参加新型农村合作医疗（城乡居民基本医疗保险）") = 0;',
            '19-是否参加城镇职工基本医疗保险为空': 'select * from tables where length("是否参加城镇职工基本医疗保险") = 0;',
            '20-是否会讲普通话为空': 'select * from tables where length("是否会讲普通话") = 0;',
            '21-是否享受低保为空': 'select * from tables where length("是否享受低保") = 0;',
            '22-是否参加大病保险为空': 'select * from tables where length("是否参加大病保险") = 0;',
            '23-是否参加商业补充医疗保险为空': 'select * from tables where length("是否参加商业补充医疗保险") = 0;',
            '24-是否国外务工为空': 'select * from tables where length("是否国外务工") = 0;',
            '25-是否接受大病医疗救助为空': 'select * from tables where length("是否接受大病医疗救助") = 0;',
            '26-是否接受其他健康扶贫为空': 'select * from tables where length("是否接受其他健康扶贫") = 0',
            '27-是否特困供养人员为空': 'select * from tables where length("是否特困供养人员") = 0',
            '28-身份证校验出同一户编号下户主与配偶性别相同的': """
            select * from tables where "与户主关系" = "配偶" and 
            (substr("证件号码",17,1) + 0 in (1,3,5,7,9) and substr("户主证件号码",17,1) + 0 in (1,3,5,7,9) or 
            substr("证件号码",17,1) + 0 in (0,2,4,6,8) and substr("户主证件号码",17,1) + 0 in (0,2,4,6,8)
            )
            """
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
            try:
                ex = pd.read_csv(self.excelPath, encoding='ANSI', keep_default_na=False, low_memory=False, sep=',')
                print('读取的csv')
            # labels = list(ex.columns.values)
            # print('表头',labels)
            except BaseException as e:
                e = str(e)
                so.msg.emit(f'错误,读取 csv 出现问题：{e}')
                self.toin = 1  # 让导入计时停止
                self.ui.pushButton_3.setEnabled(True)
                return

        else:
            ex = pd.read_excel(self.excelPath, keep_default_na=False)
            print('读取的excel')

        # 将 excel 读成表格形式, excel 就是要操作的数据表
        excel = pd.DataFrame(ex)

        # print('excel',excel[[0]])

        a = list(excel.keys())

        a = sorted(a, key=lambda i: len(i))  # 将表头按字符串长度进行排序
        print("导入的表头", a)
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
        print("arr", len(arr), arr[1])
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
