import requests
from bs4 import BeautifulSoup

from concurrent.futures import ThreadPoolExecutor

import random, copy, re, json
from time import sleep, time


# 資料準備
class Prepare:
    def __init__(self, imdbUrl="", season="", episode=""):
        self.imdbUrl = imdbUrl
        self.season = season
        self.episode = episode

    def menu(self):
        print("")
        print("******** MIDb Crawler System ********")
        print("1. Start to Scrapy")
        print("0 & else. Exit")
        print("***********************************")

    def setting(self):
        self.user_Agent = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:65.0) Gecko/20100101 Firefox/65.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"]
        self.headers = {
            "User-Agent": random.choice(self.user_Agent),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Cookie": "lc-main=en_US"}



# 各種檢查
class Checking(Prepare):
    def urlChecking(self):
        self.pattern = r"https:\/\/www.imdb.com\/title\/tt\d+\/"
        self.match = re.findall(self.pattern, self.imdbUrl)
        if self.match:
            return True
        else:
            return False     
    
    def userChecking(self):
        # if self.urlChecking == True:
        super().setting()
        self.imdbUrl = self.match[0]
        res = requests.get(self.imdbUrl, headers=self.headers)
        print(f"Video check:{res.status_code}")

        self.video_check = ""
        print("User checking...")
        # 0確認連線
        if res.status_code == 404:
            print("Please check your internet or URL and try again.")
            return False
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # 電影與影集區分環節
        try:
            stupid_check = soup.select_one('.sc-219085a0-1')
            if stupid_check == None:
                self.video_check = "movie"
                self.season_list = ["movie"]
            else:
                self.video_check = "series"

                # 1確認 season 是否是集 or 年
                if len(self.season) == 4:
                    self.imdbUrl_season = self.imdbUrl + f"episodes?year={self.season}"
                elif self.season.lower() == "all":
                    self.imdbUrl_season = self.imdbUrl + f"episodes?season=1"
                elif self.season.lower().strip() == "":
                    print("This URL is for series, so season is required, if you want to scrapy all season, please try again and enter \"all\".")
                    return False
                else:
                    self.imdbUrl_season = self.imdbUrl + f"episodes?season={self.season}"

                # 防呆檢查環節
                sleep(random.randint(3, 6))
                res =  requests.get(self.imdbUrl_season, headers=self.headers)
                print(f"Season & episode check:{res.status_code}")
                soup = BeautifulSoup(res.text, 'html.parser')

                # 2所有季數或年份儲存 
                if "season" in self.imdbUrl_season:
                    all_season = soup.select_one("select[id='bySeason']").select('option')
                    self.season_list = [season.text.strip() for season in all_season]
        
                if "year" in self.imdbUrl_season:
                    all_year = soup.select_one("select[id='byYear']").select('option')
                    self.season_list = [year.text.strip() for year in all_year]

                # 3檢查 season 是否存在
                if self.season.lower() != "all" and self.video_check == 'series':
                    try:
                        season_check = soup.select_one("#episode_top").text
                        if self.season != (season_check.replace("Season", "").lower().strip() or season_check):
                            print(f"Season(year) {self.season} does not exist.")
                            return False
                    except:
                        print(f"Season(year) {self.season} does not exist, maybe season's format is wrong or this URL is for the movie, please try again.")
                        return False

                # 4檢查 episode 是否存在
                try:
                    if self.season.lower() != "all" and self.video_check == 'series':
                        self.eplist = soup.select_one(".list.detail.eplist")
                        self.eps = self.eplist.select(".image")
                        self.start_ep = self.eps[0].select_one(".hover-over-image").text.split(',')[-1].replace('Ep','').strip()
                        self.end_ep = int(self.start_ep) + len(self.eps) - 1
                        if self.episode.lower() != "all":
                            try:
                                if (int(self.episode) - int(self.start_ep) + 1) > len(self.eps) or int(self.episode) < int(self.start_ep) or int(self.episode) > self.end_ep:
                                    print(f"Episode {self.episode} does not exist.")
                                    return False
                            except:
                                print(f"Episode's format may wrong, please try again.")
                                return False
                except:
                    print(f"Episode may not exist, please try again.")
                    return False
                print(f"Season & episode check ok.")
                
                # 5檢視最後要的 season
                if self.season.lower() != "all":
                    self.season_list = [self.season]
                print(f"Season: {(', ').join(self.season_list)}")

        except:
            print("Season may be wrong, please check again.")
            return False
        print(f"User ok...Type: {self.video_check}.")
        return True



# 開爬環節
class Scrapy(Checking):
    def daScarpy(self):
        # 抓取 Director&Actor Name、More 資料後暫存於 da_list 中
        self.da_list = []
        try:
            da_checks = self.soup.select_one(".sc-52d569c6-3")
            da_check = da_checks.select(".ipc-metadata-list__item") # 如果沒有任何 Directors、Writers、Stars 的話，這邊會 error > except
            for check in da_check:
                try:
                    # 抓取 Director Name、More 資料
                    if check.select_one(".ipc-metadata-list-item__label").text == "Director" or check.select_one(".ipc-metadata-list-item__label").text == "Directors":
                        director_name = check.select_one(".ipc-metadata-list-item__list-content-item").text
                        director_more = "https://www.imdb.com/" + check.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                        self.da_list.append({"data": {"Name": director_name,
                                                    "More": director_more}})
                    # 抓取 Actors Name、More 資料
                    elif check.select_one(".ipc-metadata-list-item__label").text == "Stars" or check.select_one(".ipc-metadata-list-item__label").text == "Star":
                        actors = check.select(".ipc-inline-list__item")
                        for actor in actors:
                            actor_name = actor.select_one(".ipc-metadata-list-item__list-content-item").text
                            actor_more = "https://www.imdb.com/" + actor.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                            if len(self.da_list) == 0:
                                self.da_list.append({"data": {"Name": "",
                                                            "More": ""}})
                                self.da_list.append({"data": {"Name": actor_name,
                                                            "More": actor_more}})
                            else:
                                self.da_list.append({"data": {"Name": actor_name,
                                                        "More": actor_more}})
                    else:
                        self.da_list.append({"data": {"Name": "",
                                                    "More": ""}})
                except:
                    pass

            # 如果 Director、Actor 的資料不齊全或是格式不對的話修正
            while True:
                if self.da_list[1]["data"]["Name"] == "":
                    self.da_list.pop(1)

                if len(self.da_list) < 4:
                    self.da_list.append({"data": {"Name": "",
                                                "More": ""}})
                else:
                    break
            
            # 抓取 Director&Actors AllRole、Bio、Born、img 資料
            for i in range(len(self.da_list)):
                if self.da_list[i]["data"]["More"] != "":
                    sleep(random.randint(3, 6))
                    res = requests.get(self.da_list[i]["data"]["More"], headers=self.headers)          
                    self.soup = BeautifulSoup(res.text, 'html.parser')
                    
                    # AllRole、Bio、Born 環節
                    try:
                        bio = self.soup.select_one(".sc-c1781ec7-1 .ipc-html-content-inner-div").text.replace("\n"," ")
                        if len(bio) >= 500:
                            bio = bio[:500] + "..."
                    except:
                        bio = ""
                    
                    try:
                        born = self.soup.select(".sc-dec7a8b-2")[1].text
                    except:
                        born = ""
                    
                    allRole_list = []
                    allRoles = self.soup.select(".sc-afe43def-4 li")
                    for allRole in allRoles:
                        allRole_list.append(allRole.text)

                    # 圖片url中有格式參數，直接進行調整
                    try:
                        img1 = self.soup.select_one(".sc-385ac629-7")
                        da400x532 = img1.select_one("img[class='ipc-image']")['src']
                        if da400x532[-18:-16] == "CR":
                            pickUY = round(int(da400x532[-22:-19]) * (400 / int(da400x532[-12:-9])))
                            pickCR = round(int(da400x532[-16:-15]) * (400 / int(da400x532[-12:-9])))
                            da400x532 = da400x532[:-22] + str(pickUY) + da400x532[-19:-16] + str(pickCR) + da400x532[-15:-12] + "400,532" + da400x532[-5:]
                        elif da400x532[-19:-17] == "CR":
                            pickUY = round(int(da400x532[-23:-20]) * (400 / int(da400x532[-12:-9])))
                            pickCR = round(int(da400x532[-17:-15]) * (400 / int(da400x532[-12:-9])))
                            da400x532 = da400x532[:-23] + str(pickUY) + da400x532[-20:-17] + str(pickCR) + da400x532[-15:-12] + "400,532" + da400x532[-5:]
                        else:
                            pickUY = round(int(da400x532[-24:-21]) * (400 / int(da400x532[-12:-9])))
                            pickCR = round(int(da400x532[-18:-15]) * (400 / int(da400x532[-12:-9])))
                            da400x532 = da400x532[:-24] + str(pickUY) + da400x532[-21:-18] + str(pickCR) + da400x532[-15:-12] + "400,532" + da400x532[-5:]
                    except:
                        da400x532 = ""

                    try:
                        img2 = self.soup.select_one(".sc-385ac629-8")
                        da600x600 = img2.select_one("img[class='ipc-image']")['src']
                        if da600x600[-18:-16] == "CR":
                            pick = round(int(da600x600[-22:-19]) * (600 / int(da600x600[-8:-5])))
                            da600x600 = da600x600[:-22] + str(pick) + da600x600[-19:-12] + "600,600" + da600x600[-5:]
                        else:
                            pick = round(int(da600x600[-23:-20]) * (600 / int(da600x600[-8:-5])))
                            da600x600 = da600x600[:-23] + str(pick) + da600x600[-20:-12] + "600,600" + da600x600[-5:]
                    except:
                        da600x600 = ""
                else:
                    allRole_list, bio, born, da400x532, da600x600 = "", "", "", "", ""
                
                self.da_list[i]["data"]["AllRole"] = allRole_list
                self.da_list[i]["data"]["Bio"] = bio
                self.da_list[i]["data"]["Born"] = born
                self.da_list[i]["data"]["400x532"] = da400x532
                self.da_list[i]["data"]["600x600"] = da600x600
        except:
            for _ in range(4 - len(self.da_list)):
                self.da_list.append({"data": {"AllRole": "",
                                        "Bio": "",
                                        "Born": "",
                                        "Name": "",
                                        "More": "",
                                        "400x532": "",
                                        "600x600": ""}})

    def videoScrapy(self):
        super().setting()
        super().userChecking()
        sleep(random.randint(3, 6))
        res = requests.get(self.imdbUrl, headers=self.headers)
        print(f"Video check:{res.status_code}")
        self.soup = BeautifulSoup(res.text, 'html.parser')

        self.datas = [
                    {
                        "Video":{
                            "Sources": []
                        },
                        "Series": {
                            "Sources": []
                        }
                    }
                ]
        # title、Excerpt、IMDB 環節(for series)
        if self.video_check == "series":
            try:
                self.title = self.soup.select_one(".sc-afe43def-3").text.replace('Original title:', '').strip()
            except:
                self.title = self.soup.select_one(".sc-afe43def-1").text

            try:
                excerpt = self.soup.select_one(".sc-cd57914c-2").text
            except:
                excerpt = ""
            
            try:
                iMDB = float(self.soup.select_one(".sc-bde20123-1 ").text)
            except:
                iMDB = ""

            # Year、Age、Length 環節
            yal = self.soup.select_one(".sc-afe43def-4").contents
            if len(yal[1].text.replace("–","")) == 8:
                year = int(yal[1].text[-4:])
            else:
                year = int(yal[1].text[:4])
            
            try: # 可以再想一下比較不會那麼死
                age = yal[2].text
            except:
                age = ""
            
            if (len(yal[-1].text) > 3) and ("m" in yal[-1].text[-1]): # case: 1h23m
                length_hours = yal[-1].text.split(' ')[0].replace('h','')
                length_mins = yal[-1].text.split(' ')[1].replace('m','')
                length = int(length_hours) * 60 + int(length_mins)
            elif (len(yal[-1].text) <= 3) and ("m" in yal[-1].text[-1]): # case: 46m
                length = int(yal[-1].text.replace('m',''))
            elif (len(yal[-1].text) <= 3) and ("h" in yal[-1].text[-1]): # case: 1h
                length = int(yal[-1].text.replace('h','')) * 60
            else:
                length = ""

        # title、Excerpt、IMDB 資料(for movie)
        else:
            try:
                self.title = self.soup.select_one(".sc-afe43def-3").text.replace('Original title:', '').strip()
            except:
                self.title = self.soup.select_one(".sc-afe43def-1").text

            try:
                excerpt = self.soup.select_one(".sc-cd57914c-2").text
            except:
                excerpt = ""

            try:
                iMDB = float(self.soup.select_one(".sc-bde20123-1").text)
            except:
                iMDB = ""

            # 抓取 Year、Age 、Length 資料 (避免資料有誤，故都用try)
            yal = self.soup.select_one(".sc-afe43def-4").contents
            try:
                year = int(yal[0].text)
            except:
                year = ""
            
            try: 
                if yal[-1].text != yal[1].text:
                    age = yal[1].text
                else:
                    age = ""
            except:
                age = ""
            
            # Length 資料分析環節
            if (len(yal[-1].text) > 3) and ("m" in yal[-1].text[-1]): # case: 1h23m
                length_hours = yal[-1].text.split(' ')[0].replace('h','')
                length_mins = yal[-1].text.split(' ')[1].replace('m','')
                length = int(length_hours) * 60 + int(length_mins)
            elif (len(yal[-1].text) <= 3) and ("m" in yal[-1].text[-1]): # case: 46m
                length = int(yal[-1].text.replace('m',''))
            elif (len(yal[-1].text) <= 3) and ("h" in yal[-1].text[-1]): # case: 1h
                length = int(yal[-1].text.replace('h','')) * 60
            else:
                length = ""

        # 抓取 Thumbnail 資料(圖片url中有藏圖片格式參數，直接進行調整)
        thumbnail = {}
        try:
            img1 = self.soup.select_one(".sc-385ac629-7")
            thumbnail600x400 = img1.select_one("img.ipc-image")['src']
            if thumbnail600x400[-18:-16] == "CR": 
                pick = round(int(thumbnail600x400[-22:-19]) * (600 / int(thumbnail600x400[-8:-5])))
                thumbnail600x400 = thumbnail600x400[:-22] + str(pick) + thumbnail600x400[-19:-12] + "400,600" + thumbnail600x400[-5:]
            elif thumbnail600x400[-19:-17] == "CR":
                pick = round(int(thumbnail600x400[-23:-20]) * (600 / int(thumbnail600x400[-8:-5])))
                thumbnail600x400 = thumbnail600x400[:-23] + str(pick) + thumbnail600x400[-20:-12] + "400,600" + thumbnail600x400[-5:]
            else:
                pick = round(int(thumbnail600x400[-24:-21]) * (600 / int(thumbnail600x400[-8:-5])))
                thumbnail600x400 = thumbnail600x400[:-24] + str(pick) + thumbnail600x400[-21:-12] + "400,600" + thumbnail600x400[-5:]
        except:
            thumbnail600x400 = ""

        try:
            img2 = self.soup.select_one(".sc-385ac629-8")    
            thumbnail600x600 = img2.select_one("img.ipc-image")['src']
            if thumbnail600x600[-18:-16] == "CR": 
                pick = round(int(thumbnail600x600[-22:-19]) * (600 / int(thumbnail600x600[-8:-5])))
                thumbnail600x600 = thumbnail600x600[:-22] + str(pick) + thumbnail600x600[-19:-12] + "600,600" + thumbnail600x600[-5:]
            else:
                pick = round(int(thumbnail600x600[-23:-20]) * (600 / int(thumbnail600x600[-8:-5])))
                thumbnail600x600 = thumbnail600x600[:-23] + str(pick) + thumbnail600x600[-20:-12] + "600,600" + thumbnail600x600[-5:]
        except:
            thumbnail600x600 = ""
        thumbnail["600x400"] = thumbnail600x400
        thumbnail["600x600"] = thumbnail600x600
        
        # 使用者輸入的網址資料先存於 datas 中
        self.datas[0]["Video"]["Excerpt"] = excerpt
        self.datas[0]["Video"]["Year"] = year
        self.datas[0]["Video"]["Thumbnail"] = thumbnail
        self.datas[0]["Video"]["Age"] = age
        self.datas[0]["Video"]["IMDB"] = iMDB
        self.datas[0]["Video"]["Length"] = length


        # 抓取 Director&Actor 環節
        self.daScarpy()

        # 將 Video 剩餘資料存入 datas 中
        self.datas[0]["Video"]["Director"] = self.da_list[0]["data"]
        self.datas[0]["Video"]["Actors"] = [self.da_list[1]["data"], self.da_list[2]["data"], self.da_list[3]["data"]]
        if self.video_check == "series": 
            self.datas[0]["Video"]["Season"] = True
        else:
            self.datas[0]["Video"]["Season"] = False
            self.datas[0]["Series"] = False
            # 存入 Json 檔中
            with open(f'imdb_{self.title.replace(" ","_").replace(",","_").replace(":","_")}.json', 'w', encoding='utf-8') as file:
                json.dump(self.datas, file, indent=4, ensure_ascii=False)
                print(f"{self.title}: done!")
                return True

    def seriesScrapy(self):
        for season in self.season_list:
            super().setting()
            sleep(random.randint(3, 6))
            res = requests.get(self.imdbUrl_season, headers=self.headers)
            print("=" * 20)
            print(f"Season {season} check:{res.status_code}")
            print("=" * 20)
            self.soup = BeautifulSoup(res.text, 'html.parser')

            # 檢查使用者輸入，如果是要整季(年)，把篇數紀錄下來
            if self.episode.lower() == "all" and season in self.season_list:
                total_episodes = len(self.eps)
                low = 1
                high = total_episodes + 1
            else:
                total_episodes = 1
                try:
                    low = int(self.episode) - int(self.start_ep) + 1
                except:
                    pass
                high = low + 1
            
            # 有幾個 episode 就要有幾組資料
            self.new_datas = []
            for _ in range(total_episodes):
                self.new_datas += copy.deepcopy(self.datas) 


            for ep in range(low, high):
                img_ep = self.eps[ep - 1].select_one(".hover-over-image").text.split(',')[-1].replace('Ep','').strip()
                subtitle = self.eps[ep - 1].select_one('a').get('title')
                print(f"Episode {img_ep} is exist: {subtitle}")
                imdbUrl_ep = "https://www.imdb.com" + self.eps[ep - 1].select_one('a').get('href')
                thumbnail_series = {}
                try:
                    thumbnail224x126 = self.eps[ep - 1].select_one("img.zero-z-index").get('src')
                    thumbnail600x600 = thumbnail224x126
                    if thumbnail600x600 == None:
                        thumbnail600x600 = thumbnail224x126
                    elif thumbnail600x600[-21:-19] == "CR":
                        thumbnail600x600 = thumbnail600x600[:-25] + "1067" + thumbnail600x600[-22:-15] + "600,600" + thumbnail600x600[-8:]
                    elif thumbnail600x600[-22:-20] == "CR":
                        thumbnail600x600 = thumbnail600x600[:-26] + "600" + thumbnail600x600[-23:-15] + "600,600" + thumbnail600x600[-8:]
                    else:
                        thumbnail600x600 = thumbnail600x600[:-17] + "600_CR0,0,600,600_AL_.jpg"
                    thumbnail_series["224x126"] = thumbnail224x126
                    thumbnail_series["600x600"] = thumbnail600x600
                except:
                    thumbnail_series["224x126"] = ""
                    thumbnail_series["600x600"] = ""

                # 進入 episode 頁面 
                sleep(random.randint(3, 6))
                res = requests.get(imdbUrl_ep, headers=self.headers)
                print(f"Episode {img_ep} check:{res.status_code}")
                self.soup = BeautifulSoup(res.text, 'html.parser')

                # Excerpt、IMDB 環節
                # title_check = soup.select_one(".sc-afe43def-1").text
                try:
                    excerpt = self.soup.select_one(".sc-cd57914c-2").text
                except:
                    excerpt = ""

                try:
                    iMDB = float(self.soup.select_one(".sc-bde20123-1").text)
                except:
                    iMDB = ""

                # 抓取 Year、Age 、Length 資料 (避免資料有誤，故都用try)
                yal = self.soup.select_one(".sc-afe43def-4").contents
                try:
                    year = int(yal[0].text[-4:])
                except:
                    year = ""
                
                try: 
                    if yal[-1].text != yal[1].text:
                        age = yal[1].text
                    else:
                        age = ""
                except:
                    age = ""
                
                # Length 資料分析環節
                if (len(yal[-1].text) > 3) and ("m" in yal[-1].text[-1]): # case: 1h23m
                    length_hours = yal[-1].text.split(' ')[0].replace('h','')
                    length_mins = yal[-1].text.split(' ')[1].replace('m','')
                    length = int(length_hours) * 60 + int(length_mins)
                elif (len(yal[-1].text) <= 3) and ("m" in yal[-1].text[-1]): # case: 46m
                    length = int(yal[-1].text.replace('m',''))
                elif (len(yal[-1].text) <= 3) and ("h" in yal[-1].text[-1]): # case: 1h
                    length = int(yal[-1].text.replace('h','')) * 60
                else:
                    length = ""


                # 抓取 Thumbnail 資料(圖片url中有藏圖片格式參數，直接進行調整)(出現新的格式，如果再有例外可能用 re 處理 比較不會出問題)
                thumbnail = {}
                try:
                    img1 = self.soup.select_one(".sc-385ac629-7")
                    thumbnail400x532 = img1.select_one("img.ipc-image")['src']
                    if thumbnail400x532[-18:-16] == "CR": 
                        pick = round(int(thumbnail400x532[-22:-19]) * (600 / int(thumbnail400x532[-8:-5])))
                        thumbnail400x532 = thumbnail400x532[:-22] + str(pick) + thumbnail400x532[-19:-12] + "400,600" + thumbnail400x532[-5:]
                    elif thumbnail400x532[-19:-17] == "CR":
                        pick = round(int(thumbnail400x532[-23:-20]) * (600 / int(thumbnail400x532[-8:-5])))
                        thumbnail400x532 = thumbnail400x532[:-23] + str(pick) + thumbnail400x532[-20:-12] + "400,600" + thumbnail400x532[-5:]
                    else:
                        pick = round(int(thumbnail400x532[-24:-21]) * (600 / int(thumbnail400x532[-8:-5])))
                        thumbnail400x532 = thumbnail400x532[:-24] + str(pick) + thumbnail400x532[-21:-12] + "400,600" + thumbnail400x532[-5:]
                except:
                    thumbnail400x532 = ""

                try:
                    img2 = self.soup.select_one(".sc-385ac629-8")    
                    thumbnail600x600 = img2.select_one("img.ipc-image")['src']
                    if thumbnail600x600[-18:-16] == "CR": 
                        pick = round(int(thumbnail600x600[-22:-19]) * (600 / int(thumbnail600x600[-8:-5])))
                        thumbnail600x600 = thumbnail600x600[:-22] + str(pick) + thumbnail600x600[-19:-12] + "600,600" + thumbnail600x600[-5:]
                    elif thumbnail600x600[-19:-17] == "CR":
                        pick = round(int(thumbnail600x600[-23:-20]) * (600 / int(thumbnail600x600[-8:-5])))
                        thumbnail600x600 = thumbnail600x600[:-23] + str(pick) + thumbnail600x600[-20:-12] + "600,600" + thumbnail600x600[-5:]
                    else:
                        pick = round(int(thumbnail600x600[-24:-21]) * (600 / int(thumbnail600x600[-8:-5])))
                        thumbnail600x600 = thumbnail600x600[:-24] + str(pick) + thumbnail600x600[-21:-12] + "600,600" + thumbnail600x600[-5:]      
                except:
                    thumbnail600x600 = ""
                thumbnail["600x400"] = thumbnail400x532
                thumbnail["600x600"] = thumbnail600x600


                # 抓取 Director&Actors Name、More 資料 
                self.daScarpy()

                # 將 Series 資料存入 datas 中
                self.new_datas[ep - low]["Series"]["Subtitle"] = subtitle
                self.new_datas[ep - low]["Series"]["Year"] = year
                self.new_datas[ep - low]["Series"]["Thumbnail"] = thumbnail_series
                self.new_datas[ep - low]["Series"]["Age"] = age
                self.new_datas[ep - low]["Series"]["IMDB"] = iMDB
                self.new_datas[ep - low]["Series"]["Length"] = length
                self.new_datas[ep - low]["Series"]["Director"] = self.da_list[0]["data"]
                self.new_datas[ep - low]["Series"]["Actors"] = [self.da_list[1]["data"], self.da_list[2]["data"], self.da_list[3]["data"]]
                self.new_datas[ep - low]["Series"]["Episode"] = img_ep
                print(f"Episode {img_ep} done.")
                print("=" * 20)

            
            # 存入 Json 檔中
            if total_episodes > 1:
                self.episode = "All"
            with open(f'imdb_{self.title.replace(": ","_").replace(", ","_").replace(" - ","_").replace(" ","_")}_Season{self.season}_Episode{self.episode}.json', 'w', encoding='utf-8') as file:
                json.dump(self.new_datas, file, indent=4, ensure_ascii=False)
                print(f"{self.title} : Season{season} Episode{self.episode} done!")
                print("=" * 20)






# 測試專區
'''
def get_url(imbdurl:str):
    user_Agent = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:65.0) Gecko/20100101 Firefox/65.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"]
    headers = {
        "User-Agent": random.choice(user_Agent),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache"
    }
    res = requests.get(imbdurl, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    url_list = []
    urls = soup.select('.lister-item-image a')
    for url in urls:
        ur = "https://www.imdb.com" + url.get('href')
        url_list.append(ur)
    
    # print(len(url_list))

    with open('url_list.txt', mode='w', encoding='utf-8') as f:
        for url in url_list:
            f.write(url + "\n")
        print('Done!')

def quick(url, season, episodes):
    test = Scrapy(url, season, episodes)
    result = test.urlChecking()
    if result == True:
        test.videoScrapy()
        if test.video_check == "series":
            test.seriesScrapy()


if  __name__ == "__main__":
    get_url("https://www.imdb.com/search/title/?title_type=tv_series,tv_miniseries&genres=adventure&start=351&explore=genres&ref_=adv_nxt")

    with open('url_list.txt', mode='r', encoding='utf-8') as f:
        urls = f.readlines()

    url_list= [url.strip() for url in urls]

    with ThreadPoolExecutor() as executor:
        for url in url_list:
            executor.submit(quick, url, "1", "3")

    print("done.....")
    
'''

