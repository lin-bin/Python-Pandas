# -*- coding: utf-8 -*-
from selenium import webdriver
import time
import os


class TheTest:
    def __init__(self):
        self.bankArr = []  # 题库
        # na = input('请输入您的姓名：')
        # un = input('请输入您的单位名称：')
        # sfz = input('请输入您的身份证：')
        # num = self.getUnit()  # 返回选择地址的序号
        num = 2
        # 打开谷歌浏览器，填写谷歌浏览器驱动的位置，python里 \ 代表转移，r 代表不转义，原始字符串
        # WebDriver 实例对象，指明使用  chrome 浏览器驱动
        self.web = webdriver.Chrome(r'd:\chromedriver.exe')
        # 滑块验证码
        self.web.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator,'webdriver',{
                get:() => undefined
            })
            """
        })
        self.web.implicitly_wait(20)

        # 打开网站，输入网址
        self.web.get('https://ks.wjx.top/vj/hdJsJMD.aspx')

        name = self.web.find_element_by_css_selector('#q1')  # 姓名
        unit = self.web.find_element_by_css_selector('#q2')  # 单位名称
        idCard = self.web.find_element_by_css_selector('#q3')  # 身份证号
        p = f'//*[@id="divquestion4"]/ul/li[{num}]/label'  # 选择地址

        name.send_keys('买买提')
        unit.send_keys('喀什市')
        idCard.send_keys('510322200103156253')
        clickUnit = self.web.find_element_by_xpath(p).click()
        self.getT()

    # 获取所有单位
    def getUnit(self):
        arr = ['1.喀什地区纪委监委（含地委巡察办）', '2.驻地委办公室纪检监察组', '3.驻地委组织部纪检监察组', '4.驻地委宣传部纪检监察组', '5.驻地委政法委纪检监察组',
               '6.驻地区人大工委机关纪检监察组', '7.驻地区行署办公室纪检监察组', '8.驻地区政协工委机关纪检监察组', '9.驻地区发改委纪检监察组', '10.驻地区财政局纪检监察组',
               '11.驻地区市场监督管理局纪检监察组', '12.驻地委教育工委纪检监察组', '13.驻地区生态环境局纪检监察组', '14.驻地区农业农村局纪检监察组', '15.驻地区卫健委纪检监察组',
               '16.经济开发区纪工委', '17.地委直属机关纪检监察工委', '18.喀什市', '19.疏勒县', '20.疏附县', '21.英吉沙县', '22.伽师县', '23.岳普湖县',
               '24.麦盖提县', '25.莎车县', '26.泽普县', '27.叶城县', '28.巴楚县', '29.塔什库尔干县']

        title = ''
        n = 0
        i = 0
        for item in arr:
            i += 1
            if i % 4 == 0:
                str = ", ".join(arr[n:i])

                print(str)
                n = i

        unitNum = input("请选择地址：")

        # print(f'{num}. {value}')
        print(title)
        return unitNum

    # 答题
    def getT(self):
        # 判断是否有题库文件
        if os.path.exists('题库.txt') == False:
            open('题库.txt', 'w')
        with open('题库.txt', 'r', encoding='utf-8') as f:
            self.bankArr = f.readlines()
            # print(self.bankArr)

        # 将题库和答案对应分成两个数组
        TMArr = []  # 题库
        TheAnswer = []  # 答案
        for item in self.bankArr:
            arr = item.split('|')
            TMArr.append(arr[0])  # 题目数组
            TheAnswer.append(arr[1])  # 答案数组
        self.web.implicitly_wait(0)
        # 单选题
        for item in range(5, 25):
            reg = f'//*[@id="divTitle{item}"]'
            tm = self.web.find_element_by_xpath(reg)

            try:
                index = TMArr.index(tm.text)  # 题目在题库数组中的索引
                if index >= 0:
                    # print(TheAnswer[index])
                    # print('题目', tm.text)
                    for i in range(1, 5):  # 循环4个选项，判断正确的进行选择
                        tegT = f'//*[@id="divquestion{item}"]/ul/li[{i}]/label'
                        tegTM = self.web.find_element_by_xpath(tegT)
                        str = TheAnswer[index].split(".")[-1].replace("\n", '')  # 题库答案
                        strW = tegTM.text.split(".")[-1]  # 网页答案
                        # print("题库答案",str)
                        # print('网页答案',strW)
                        if str == strW:
                            tegTM.click()
                            print("选择了", tegTM.text)


            except:
                print('单选题：此题不在题库里', tm.text)
                tegT = f'//*[@id="divquestion{item}"]/ul/li/label'
                tegTM = self.web.find_elements_by_xpath(tegT)
                tegTM[-1].click()
                # tegT = f'//*[@id="divquestion{item}"]/ul/li[4]/label'  # 该题不在题库里，默认选 A
                # tegTM = self.web.find_element_by_xpath(tegT).click()

        # 多选题
        for i in range(85, 95):
            reg = f'//*[@id="divTitle{i}"]'  # 获取网页多选题题目

            tm = self.web.find_element_by_xpath(reg)
            # tm.text = tm.text.replace(' 【多选题】','')
            webTM = tm.text
            webTM = webTM.replace(' 【多选题】', '')
            # print("题目",webTM)
            try:
                index = TMArr.index(webTM)  # 题目在题库数组中的索引
                print("题目在题库里", webTM)
                if index >= 0:
                    print("题库答案：", TheAnswer[index])
                    TheAnswer[index] = TheAnswer[index].replace("\n", "")
                    D_tegT = f'//*[@id="divquestion{i}"]/ul/li/label'
                    D_tegTM = self.web.find_elements_by_xpath(D_tegT)  # 多选题所有选项
                    ans = TheAnswer[index].split("┋")  # 将多选题题库答案进行分割
                    arr = []  # 处理好的题库答案，没有ABC，只有中文答案
                    for a in ans:
                        a = a.split(".")[-1]
                        arr.append(a)
                    print('题库答案', arr)
                    for d in D_tegTM:
                        dt = d.text.split(".")[-1]
                        if dt in arr:
                            d.click()



            except:
                print('多选题：此题不再题库里', webTM)
                D_tegT = f'//*[@id="divquestion{i}"]/ul/li/label'
                D_tegTM = self.web.find_elements_by_xpath(D_tegT)  # 多选题所有选项
                for it in D_tegTM:
                    # tegT = f'//*[@id="divquestion{i}"]/ul/li[{it}]/label'  # 该题不在题库里，默认选 ABCD
                    tegTM = it.click()

        # 判断题
        for i in range(120, 140):
            reg = f'//*[@id="divTitle{i}"]'  # 获取网页判断题题目
            tm = self.web.find_element_by_xpath(reg)

            try:
                index = TMArr.index(tm.text)  # 题目在题库数组中的索引
                if index >= 0:
                    TheAnswer[index] = TheAnswer[index].replace("\n", "")
                    print('题目', tm.text)
                    print("题库答案：", TheAnswer[index])
                    if TheAnswer[index] == "对":
                        re = f'//*[@id="divquestion{i}"]/ul/li[1]/label'
                        t = self.web.find_element_by_xpath(re)
                        t.click()
                    else:
                        re = f'//*[@id="divquestion{i}"]/ul/li[2]/label'
                        t = self.web.find_element_by_xpath(re)
                        t.click()




            except:
                print('判断题：此题不再题库里', tm.text)
                re = f'//*[@id="divquestion{i}"]/ul/li[2]/label'  # 默认选中错
                t = self.web.find_element_by_xpath(re)
                t.click()

        btn = self.web.find_element_by_css_selector('#submit_button')
        btn.click()
        try:
            self.web.execute_script('closeAlert()')
        except:
            pass
        time.sleep(1)
        btnyz = self.web.find_element_by_css_selector('#rectMask')
        btnyz.click()

        time.sleep(10)
        self.getTK()

    # 判断某个元素是否存在
    def exists(self, div, element):
        try:
            element = div.find_element_by_css_selector(element)
        except:
            return False
        else:
            return True

    # 获取题库
    def getTK(self):
        score = self.web.find_element_by_css_selector('.score-font-style')  # 获取考试的分数
        print("分数", score.text)
        if int(score.text) < 100:  # 分数小于98，就继续获取题库
            div = self.web.find_elements_by_css_selector('.data__items')
            # print('div', div)
            for i, item in enumerate(div):

                if i < 4:
                    continue
                isN = self.exists(item, '.answer-ansys')
                print(isN)
                if isN:
                    num = item.find_element_by_css_selector('.data__tit_cjd label').text  # 题目序号
                    spans = item.find_element_by_css_selector('.data__tit_cjd').text  # 题目 包含序号
                    spans = spans.replace(num, '')  # 将序号去除掉
                    spans = spans.replace("  分值2分", "")  # 将分值去掉
                    spans = spans.lstrip()  # 去除首空格
                    answer = item.find_element_by_css_selector('.answer-ansys div').text  # 答案
                    print(f'{spans}|{answer}')
                    topic = f'{spans}|{answer}\n'
                    with open('题库.txt', 'a', encoding='utf-8') as f:
                        f.write(topic)

            self.web.quit()
            THE = TheTest()
        else:
            print(f'题库获取完成，最后一次分数为{score.text}')
            # 对题库进行去重
            with open('题库.txt', 'r', encoding="utf-8") as f:
                arr = f.readlines()
            bank = []
            for item in arr:
                if item not in bank:
                    bank.append(item)

            for i in bank:
                with open('最终题库.txt', 'a', encoding='utf-8') as f:
                    f.write(i)


if __name__ == '__main__':
    TheTest = TheTest()
