from DrissionPage import SessionPage,ChromiumOptions,ChromiumPage
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import threading
import time
import pandas as pd


class WebContentScraper(object):

    def __init__(self,keyword:str,location:str,resultNeed:int,savefilePath:str):
        self.threads = []
        self.threadsData = {}

        self.keyword = keyword
        self.location = location
        self.resultNeed = resultNeed

        self.saveFilePath = savefilePath
        self.c = canvas.Canvas(self.saveFilePath +"/" +self.keyword + ".pdf", pagesize=letter)


    def startSearch(self,format:str):
        """

        :param format: ".csv" , ".pdf"
        :return:
        """
        searchList = self.__getSearchResult(self.keyword,self.location,self.resultNeed)
        if searchList == "error":
            return "error"
        for i in range(len(searchList)):
            threads = threading.Thread(target=self.__getMainContent,args=(i,searchList[i],self.threadsData))
            self.threads.append(threads)
            threads.start()

        for i in range(len(self.threads)):
            self.threads[i].join()

        sorted_data = dict(sorted(self.threadsData.items(), key=lambda item: int(item[0])))
        print(sorted_data)
        if format == ".pdf":
            for i in range(len(sorted_data)):
                self.__writePageContentToPdf(sorted_data[str(i)])
            self.c.save()

        if format == ".csv":
            self.__writePageContentToCSV(sorted_data)


    def __getSearchResult(self,keyword: str, location: str, resultNum: int):
        """

        :param keyword: searching keyword
        :param location: HK / TW
        :param resultNum: return how many num of result
        :return: a length=resultNum list with the url
        """
        page = SessionPage()

        prefix = "https://www.google.com/search?as_q="
        keyWord = keyword
        suffix = "&as_epq=&as_oq=&as_eq=&as_nlo=&as_nhi=&lr=&cr=country" + location + "&as_qdr=all&as_sitesearch=&as_occt=any&as_filetype=&tbs=&start="
        startPoint = 0
        currentResultNum = 0
        result = []
        while True:
            if not page.get(prefix + keyWord + suffix + str(startPoint)):
                return "error"
            searchResult = page.eles("t:h3")
            for i in searchResult:
                if currentResultNum >= resultNum:
                    return result
                try:
                    print("org:", i.parent("t:a@@href:https://"))
                    url = i.parent("t:a@@href:https://").link.replace("https://www.google.com/url?esrc=s&q=&rct=j&sa=U&url=","").split("&ved")[0]
                    print("url",url)
                except Exception as e:
                    continue
                result.append(url)
                currentResultNum += 1
                startPoint += 1

    def __getMainContent(self,order:int,pageUrl: str,outputData:dict):
        page = SessionPage()

        content = {
            "title": "[內容無關聯或無法訪問的頁面]",
            "url": pageUrl,
            "description": "無",
            "introText": "無",
            "outLine": []
        }
        try:
            # 获取网页内容
            url = pageUrl
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # 方法1：获取<meta>标签中的description
            metaDescription = soup.find('meta', attrs={'name': 'description'})
            if metaDescription:
                description = metaDescription.get('content')
                content["description"] = description

            # 方法2：获取特定<div>或<p>标签中的内容
            # 需要根据实际网页结构调整选择器
            introParagraph = soup.find('p', class_='intro')
            if introParagraph:
                introText = introParagraph.get_text()
                content["introText"] = introText

            # get outline
            page.get(pageUrl)
            pageHtml = page.eles("@!id=1234")
            content["outLine"].append("│=========================")
            t = "   "
            for html in pageHtml:
                if not html.text or html.text == "" or html.text == " ":
                    continue
                if len(html.text) > 75:
                    continue
                if "h1" in str(html):
                    content["title"] = html.text
                    content["outLine"].append("│ [h1] " + html.text)
                    continue
                if "h2" in str(html):
                    # content["outLine"].append("│\t\t\t[h2] " + html.text)
                    content["outLine"].append("│" + t + t + t + "[h2] " + html.text)
                    continue
                if "h3" in str(html):
                    # content["outLine"].append("│\t\t\t\t\t[h3] " + html.text)
                    content["outLine"].append("│" + t + t + t + t + t +"[h3] " + html.text)
                    continue

                if "h4" in str(html):
                    # content["outLine"].append("│\t\t\t\t\t\t\t[h4] " + html.text)
                    content["outLine"].append("│" + t + t + t + t + t + t + t + "[h4] " + html.text)
                    continue

                if "h5" in str(html):
                    # content["outLine"].append("│\t\t\t\t\t\t\t\t[h5] " + html.text)
                    content["outLine"].append("│" + t + t + t + t + t + t + t + t + t + "[h5] " + html.text)
                    continue

                if "h6" in str(html):
                    # content["outLine"].append("│\t\t\t\t\t\t\t\t\t[h6] " + html.text)
                    content["outLine"].append("│" + t + t + t + t + t + t + t + t + t + t + t + "[h6] " + html.text)
                    continue
            content["outLine"].append("│=========================")

            if len(content["outLine"]) == 0:
                content["outLine"] = "無"
            outputData[str(order)] = content
        except Exception as e:
            content["outLine"] = "無"
            outputData[str(order)] = content

    def __writePageContentToPdf(self, content: dict):

        # 设置字体和大小
        pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
        self.c.setFont('SimSun', 12)

        # 在PDF上写入文本
        title = "標題: " + content["title"]
        self.c.drawString(25, 750, title)
        url = "URL: " + content["url"]
        self.c.drawString(25, 735, url)

        posY = 700
        self.c.drawString(25, posY, "內容大綱: ")
        for string in content["outLine"]:
            posY -= 15
            if posY < 100:
                # 开启新页面
                self.c.showPage()
                self.c.setFont('SimSun', 12)
                posY = 700
            self.c.drawString(25, posY, string)

        posY -= 50
        self.c.drawString(25, posY, "內容簡介一: ")
        lengthOfCharInLine = 45
        numOfLine = int(len(content["description"]) / lengthOfCharInLine)
        for i in range(0, numOfLine + 1):
            posY -= 15
            if posY < 100:
                # 开启新页面
                self.c.showPage()
                self.c.setFont('SimSun', 12)
                posY = 700
            self.c.drawString(25, posY, content["description"][i * lengthOfCharInLine:(i + 1) * lengthOfCharInLine])

        posY -= 50
        self.c.drawString(25, posY, "內容簡介二: ")
        lengthOfCharInLine = 45
        numOfLine = int(len(content["introText"]) / lengthOfCharInLine)
        for i in range(0, numOfLine + 1):
            posY -= 15
            if posY < 100:
                # 开启新页面
                self.c.showPage()
                self.c.setFont('SimSun', 12)
                posY = 700
            self.c.drawString(25, posY, content["introText"][i * lengthOfCharInLine:(i + 1) * lengthOfCharInLine])

        #开启新页面
        self.c.showPage()

    def __writePageContentToCSV(self,threadsData:dict):
        """

        :param threadsData: { "1":{"title": "","url":"",...} , "2":{"title": "","url":"",...}, ... }
        :return:
        """
        data = {
            "RANKING":[],
            "標題":[],
            "URL":[],
            "內容大綱":[],
            "內容簡介一":[],
            "內容簡介二":[]
        }

        for i in range(len(threadsData)):
            data["RANKING"].append(str(i+1))
            data["標題"].append(threadsData[str(i)]["title"])
            data["URL"].append(threadsData[str(i)]["url"])

            outline = ""
            for j in range(len(threadsData[str(i)]["outLine"])):
                outline += threadsData[str(i)]["outLine"][j] + '\n'

            data["內容大綱"].append(outline)
            data["內容簡介一"].append(threadsData[str(i)]["description"])
            data["內容簡介二"].append(threadsData[str(i)]["introText"])

        df = pd.DataFrame(data)

        # 转置 DataFrame
        df_transposed = df.T

        df_transposed.to_csv(self.saveFilePath+"/" + self.keyword + ".csv",header=False, encoding='utf-8-sig')





if __name__ == "__main__":
    start_time = time.time()
    a = WebContentScraper("大阪景點","TW",20,"D:/PyCharm Community Edition 2023.3.2/PROJECT FILE/outline/output")
    a.startSearch(".pdf")
    end_time = time.time()
    print("Total time:", end_time - start_time, "seconds")



