import requests
from bs4 import BeautifulSoup

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import random, copy, re, json
from time import sleep


# 選單
def menu():
    print("")
    print("******** MIDb Crawler System ********")
    print("1. Movie")
    print("2. TV Series or TV Show")
    print("0 & else. Quit")
    print("***********************************")


# 電影環節
def imdb_movie_scrapy(imdbUrl:str):
    # 基本設定
    user_Agent = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:65.0) Gecko/20100101 Firefox/65.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; M351 Build/KTU84P) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30"]
    headers = {
        "User-Agent": random.choice(user_Agent),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache"
    }
    
    # 檢查網址格式是否有誤
    pattern = r"https:\/\/www.imdb.com\/title\/tt\d+\/"
    match = re.findall(pattern, imdbUrl)
    if match:
        print("URL is correct.")
        res = requests.get(imdbUrl, headers=headers)
        print(f"Video check:{res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        # 防呆提示，若這是影集則回傳 False
        try:
            stupid_check = soup.select_one('.sc-219085a0-1')
            if stupid_check != None:
                print("This URL may be a TV show or TV seriese, please try again.")
                return False
        except:
            pass
            
        datas = [
                {
                    "Video":{
                        "Sources": []
                    },
                    "Serise": False
                }
            ]
        
        # 抓取 title、Excerpt、IMDB 資料 (避免資料有誤，故都用try)
        try:
            title = soup.select_one(".sc-afe43def-3").text.replace('Original title:', '').strip()
        except:
            title = soup.select_one(".sc-afe43def-1").text

        try:
            excerpt = soup.select_one(".sc-cd57914c-2").text
        except:
            excerpt = ""

        try:
            iMDB = float(soup.select_one(".sc-bde20123-1").text)
        except:
            iMDB = ""

        # 抓取 Year、Age 、Length 資料 (避免資料有誤，故都用try)
        yal = soup.select_one(".sc-afe43def-4").contents
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

        # 抓取 Thumbnail 資料(圖片url中圖片格式參數，直接進行調整)
        thumbnail = {}
        try:
            img1 = soup.select_one(".sc-385ac629-7")
            thumbnail600x400 = img1.select_one("img[class='ipc-image']")['src']
            if thumbnail600x400[-18:-16] == "CR": 
                pick = round(int(thumbnail600x400[-22:-19]) * (600 / int(thumbnail600x400[-8:-5])))
                thumbnail600x400 = thumbnail600x400[:-22] + str(pick) + thumbnail600x400[-19:-12] + "400,600" + thumbnail600x400[-5:]
            else:
                pick = round(int(thumbnail600x400[-23:-20]) * (600 / int(thumbnail600x400[-8:-5])))
                thumbnail600x400 = thumbnail600x400[:-23] + str(pick) + thumbnail600x400[-20:-12] + "400,600" + thumbnail600x400[-5:]
        except:
            thumbnail600x400 = ""

        try:
            img2 = soup.select_one(".sc-385ac629-8")    
            thumbnail600x600 = img2.select_one("img[class='ipc-image']")['src']
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
        datas[0]["Video"]["Excerpt"] = excerpt
        datas[0]["Video"]["Year"] = year
        datas[0]["Video"]["Thumbnail"] = thumbnail
        datas[0]["Video"]["Age"] = age
        datas[0]["Video"]["IMDB"] = iMDB
        datas[0]["Video"]["Length"] = length


        # 抓取 Director&Actor Name、More 資料後暫存於 da_list 中
        da_list = []
        da_checks = soup.select_one(".sc-52d569c6-3")
        da_check = da_checks.select(".ipc-metadata-list__item")
        for check in da_check:
            try:
                # 抓取 Director Name、More 資料
                if check.select_one(".ipc-metadata-list-item__label").text == "Director" or check.select_one(".ipc-metadata-list-item__label").text == "Directors":
                    director_name = check.select_one(".ipc-metadata-list-item__list-content-item").text
                    director_more = "https://www.imdb.com/" + check.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                    da_list.append({"data": {"Name": director_name,
                                             "More": director_more}})
                # 抓取 Actors Name、More 資料
                elif check.select_one(".ipc-metadata-list-item__label").text == "Stars" or check.select_one(".ipc-metadata-list-item__label").text == "Star":
                    actors = check.select(".ipc-inline-list__item")
                    for actor in actors:
                        actor_name = actor.select_one(".ipc-metadata-list-item__list-content-item").text
                        actor_more = "https://www.imdb.com/" + actor.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                        da_list.append({"data": {"Name": actor_name,
                                                 "More": actor_more}})
                else:
                    da_list.append({"data": {"Name": "",
                                             "More": ""}})
            except:
                pass

        # 如果 Director、Actor 的資料不齊全的話，補足至 4 個
        while da_list:
            if da_list[1]["data"]["Name"] == "":
                da_list.pop(1)

            if len(da_list) < 4:
                da_list.append({"data": {"Name": "",
                                         "More": ""}})
            else:
                break

        # 抓取 Director&Actors AllRole、Bio、Born、img 資料
        for i in range(len(da_list)):
            if da_list[i]["data"]["More"] != "":
                sleep(random.randint(3, 6))
                res = requests.get(da_list[i]["data"]["More"], headers=headers)
                print(f"Profile \"{da_list[i]['data']['Name']}\" check:{res.status_code}")            
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # AllRole、Bio、Born 環節
                bio = soup.select_one(".ipc-html-content-inner-div").text
                try:
                    born = soup.select(".sc-dec7a8b-2")[1].text
                except:
                    born = ""
                
                allRole_list = []
                allRoles = soup.select_one(".sc-afe43def-4").contents
                for allRole in allRoles:
                    allRole_list.append(allRole.text)

                # 圖片url中有格式參數，直接進行調整
                try:
                    img1 = soup.select_one(".sc-385ac629-7")
                    da400x532 = img1.select_one("img[class='ipc-image']")['src']
                    if da400x532[-18:-16] == "CR":
                        pick = round(int(da400x532[-22:-19]) * (400 / int(da400x532[-12:-9])))
                        da400x532 = da400x532[:-22] + str(pick) + da400x532[-19:-12] + "400,532" + da400x532[-5:]
                    else:
                        pick = round(int(da400x532[-23:-20]) * (400 / int(da400x532[-12:-9])))
                        da400x532 = da400x532[:-23] + str(pick) + da400x532[-20:-12] + "400,532" + da400x532[-5:]
                except:
                    da400x532 = ""

                try:
                    img2 = soup.select_one(".sc-385ac629-8")
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
            
            da_list[i]["data"]["AllRole"] = allRole_list
            da_list[i]["data"]["Bio"] = bio
            da_list[i]["data"]["Born"] = born
            da_list[i]["data"]["400x532"] = da400x532
            da_list[i]["data"]["600x600"] = da600x600
            print(f"Data \"{da_list[i]['data']['Name']}\" is ok!")
        
        # 將剩餘資料存入 datas 中
        datas[0]["Video"]["Director"] = da_list[0]["data"]
        datas[0]["Video"]["Actors"] = [da_list[1]["data"], da_list[2]["data"], da_list[3]["data"]]
        datas[0]["Video"]["Season"] = True

        # 存入 Json 檔中
        with open(f'imdb_{title.replace(" ","_").replace(",","_").replace(":","_")}.json', 'w', encoding='utf-8') as file:
            json.dump(datas, file, indent=4, ensure_ascii=False)
            print("Done!")

    else:
        print("URL may be wrong, please check again.")



# 單集環節(已被合併)
'''            
def imdb_series_scrapy(imdbUrl:str, season:str, episode:str):
    # 基本設定
    user_Agent = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:65.0) Gecko/20100101 Firefox/65.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        # "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) CriOS/31.0.1650.18 Mobile/11B554a Safari/8536.25",
        # "Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4",
        # "Mozilla/5.0 (Linux; Android 4.2.1; M040 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; M351 Build/KTU84P) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30"]
    headers = {
        "User-Agent": random.choice(user_Agent),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache"
    }
    
    pattern = r"https:\/\/www.imdb.com\/title\/tt\d+\/"
    match = re.findall(pattern, imdbUrl)
    if match:
        print("URL is correct.")
        imdbUrl = match[0]
        res = requests.get(imdbUrl, headers=headers)
        print(res.status_code)
        soup = BeautifulSoup(res.text, 'html.parser')

        datas = [
                {
                    "Video":{
                        "Sources": []
                    },
                    "Series": {
                        "Sources": []
                    }
                }
            ]
        # 抓取 subtitle、Excerpt、Year、Length、IMDB 資料
        try:
            title = soup.select_one("div[class='sc-afe43def-3 EpHJp']").text.split(':')[1].strip()
        except:
            title = soup.select_one("span[class='sc-afe43def-1 fDTGTb']").text

        excerpt = soup.select_one("span[class='sc-2eb29e65-2 jBnwaA']").text
        iMDB = float(soup.select_one("span[class='sc-bde20123-1 iZlgcd']").text)

        yal = soup.select_one("ul[class='ipc-inline-list ipc-inline-list--show-dividers sc-afe43def-4 kdXikI baseAlt']").contents
        if len(yal[1].text.replace("–","")) == 8:
            year = int(yal[1].text[-4:])
        else:
            year = int(yal[1].text[:4])

        age = yal[2].text
        
        if len(yal[3].text) > 3:
            length_hours = yal[3].text.split(' ')[0].replace('h','')
            length_mins = yal[3].text.split(' ')[1].replace('m','')
            length = int(length_hours) * 60 + int(length_mins)
        else:
            length = int(yal[3].text.replace('m',''))


        # 抓取 Thumbnail 資料(圖片url中有藏圖片格式參數，直接進行調整)
        thumbnail = {}
        try:
            img1 = soup.select_one("div[class~='sc-385ac629-7']")
            thumbnail600x400 = img1.select_one("img[class='ipc-image']")['src']
            if thumbnail600x400[-18:-16] == "CR": 
                pick = round(int(thumbnail600x400[-22:-19]) * (600 / int(thumbnail600x400[-8:-5])))
                thumbnail600x400 = thumbnail600x400[:-22] + str(pick) + thumbnail600x400[-19:-12] + "400,600" + thumbnail600x400[-5:]
            else:
                pick = round(int(thumbnail600x400[-23:-20]) * (600 / int(thumbnail600x400[-8:-5])))
                thumbnail600x400 = thumbnail600x400[:-23] + str(pick) + thumbnail600x400[-20:-12] + "400,600" + thumbnail600x400[-5:]
        except:
            thumbnail600x400 = ""
            print("img1(600x400) does not exist.")

        try:
            img2 = soup.select_one("div[class~='sc-385ac629-8']")    
            thumbnail600x600 = img2.select_one("img[class='ipc-image']")['src']
            if thumbnail600x600[-18:-16] == "CR": 
                pick = round(int(thumbnail600x600[-22:-19]) * (600 / int(thumbnail600x600[-8:-5])))
                thumbnail600x600 = thumbnail600x600[:-22] + str(pick) + thumbnail600x600[-19:-12] + "600,600" + thumbnail600x600[-5:]
            else:
                pick = round(int(thumbnail600x600[-23:-20]) * (600 / int(thumbnail600x600[-8:-5])))
                thumbnail600x600 = thumbnail600x600[:-23] + str(pick) + thumbnail600x600[-20:-12] + "600,600" + thumbnail600x600[-5:]
        except:
            thumbnail600x600 = ""
            print("img2(600x600) does not exist.")
        thumbnail["600x400"] = thumbnail600x400
        thumbnail["600x600"] = thumbnail600x600
        
        # 使用者輸入的網址資料先存於 datas 中
        datas[0]["Video"]["Excerpt"] = excerpt
        datas[0]["Video"]["Year"] = year
        datas[0]["Video"]["Thumbnail"] = thumbnail
        datas[0]["Video"]["Age"] = age
        datas[0]["Video"]["IMDB"] = iMDB
        datas[0]["Video"]["Length"] = length


        # 獲取其他網頁的網址，並先暫存於其他 list 中
        da_list = []
        da_checks = soup.select_one("div[class='sc-52d569c6-3 jBXsRT']")
        da_check = da_checks.select("li[class='ipc-metadata-list__item ipc-metadata-list-item--link']")
        for check in da_check:
            # 抓取 Director Name、More 資料
            if check.select_one("a[class='ipc-metadata-list-item__label ipc-metadata-list-item__label--link']").text == "Director":
                director_name = check.select_one("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']").text
                director_more = "https://www.imdb.com/" + check.select_one("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']").get('href')
                da_list.append({"data": {"Name": director_name,
                                        "More": director_more}})
            else:
                da_list.append({"data": {"Name": "",
                                        "More": ""}})

            # 抓取 Actors Name、More 資料
            if check.select_one("a[class='ipc-metadata-list-item__label ipc-metadata-list-item__label--link']").text == "Stars":
                actors = check.select("li[class='ipc-inline-list__item']")
                for actor in actors:
                    actor_name = actor.select_one("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']").text
                    actor_more = "https://www.imdb.com/" + actor.select_one("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']").get('href')
                    da_list.append({"data": {"Name": actor_name,
                                            "More": actor_more}})
        
        # 如果 Director、Actor 的資料不齊全的話，補足至 4 個
        while da_list:
            if da_list[1]["data"]["Name"] == "":
                da_list.pop(1)

            if len(da_list) < 4:
                da_list.append({"data": {"Name": "",
                                        "More": ""}})
            else:
                break

        # 抓取 Director&Actors AllRole、Bio、Born、img 資料
        for i in range(len(da_list)):
            sleep(random.randint(5, 12))
            if da_list[i]["data"]["More"] != "":
                res = requests.get(da_list[i]["data"]["More"], headers=headers)
                print(res.status_code)            
                soup = BeautifulSoup(res.text, 'html.parser')
                allRole_list = []

                bio = soup.select_one("div[class='ipc-html-content-inner-div']").text
                try:
                    born = soup.select("span[class='sc-dec7a8b-2 haviXP']")[1].text
                except:
                    born = ""
                    print(f"Can't find born attr.({da_list[i]['data']['Name']})")
                        
                allRoles = soup.select_one("ul[class='ipc-inline-list ipc-inline-list--show-dividers sc-afe43def-4 kdXikI baseAlt']").contents
                for allRole in allRoles:
                    allRole_list.append(allRole.text)

                # 圖片url中有藏圖片格式參數，直接進行調整
                try:
                    img1 = soup.select_one("div[class~='sc-385ac629-7']")
                    da400x532 = img1.select_one("img[class='ipc-image']")['src']
                    if da400x532[-18:-16] == "CR":
                        pick = round(int(da400x532[-22:-19]) * (400 / int(da400x532[-12:-9])))
                        da400x532 = da400x532[:-22] + str(pick) + da400x532[-19:-12] + "400,532" + da400x532[-5:]
                    else:
                        pick = round(int(da400x532[-23:-20]) * (400 / int(da400x532[-12:-9])))
                        da400x532 = da400x532[:-23] + str(pick) + da400x532[-20:-12] + "400,532" + da400x532[-5:]
                except:
                    da400x532 = ""
                    print(f"{da_list[i]['data']['Name']}\'s img(400x532) does not exist.")

                try:
                    img2 = soup.select_one("div[class~='sc-385ac629-8']")
                    da600x600 = img2.select_one("img[class='ipc-image']")['src']
                    if da600x600[-18:-16] == "CR":
                        pick = round(int(da600x600[-22:-19]) * (600 / int(da600x600[-8:-5])))
                        da600x600 = da600x600[:-22] + str(pick) + da600x600[-19:-12] + "600,600" + da600x600[-5:]
                    else:
                        pick = round(int(da600x600[-23:-20]) * (600 / int(da600x600[-8:-5])))
                        da600x600 = da600x600[:-23] + str(pick) + da600x600[-20:-12] + "600,600" + da600x600[-5:]
                except:
                    da600x600 = ""
                    print(f"{da_list[i]['data']['Name']}\'s img(600x600) does not exist.")        
            else:
                allRole_list, bio, born, da400x532, da600x600 = "", "", "", "", ""

            da_list[i]["data"]["AllRole"] = allRole_list
            da_list[i]["data"]["Bio"] = bio
            da_list[i]["data"]["Born"] = born
            da_list[i]["data"]["400x532"] = da400x532
            da_list[i]["data"]["600x600"] = da600x600
            print(f"data \"{da_list[i]['data']['Name']}\" is ok!")

        # 將 Video 剩餘資料存入 datas 中
        datas[0]["Video"]["Director"] = da_list[0]["data"]
        datas[0]["Video"]["Actors"] = [da_list[1]["data"], da_list[2]["data"], da_list[3]["data"]]
        datas[0]["Video"]["Season"] = True


        ### 處理 season 和 episode 環節
        sleep(random.randint(5, 15))
        imdbUrl_season = imdbUrl + f"episodes?season={season}"
        res = requests.get(imdbUrl_season, headers=headers)
        print(res.status_code)
        soup = BeautifulSoup(res.text, 'html.parser')

        # season 列表中 Subtitle、Thumbnail、href 資料
        thumbnail = {}            
        eplist = soup.select_one('div[class="list detail eplist"]')
        eps = eplist.select("div[class='image']")    
        if int(episode) <= len(eps):
            print(f"Episode {episode} is exist.")
            subtitle = eps[int(episode) - 1].select_one('a').get('title')
            imdbUrl_ep = "https://www.imdb.com" + eps[int(episode) - 1].select_one('a').get('href')
            thumbnail224x126 = eps[int(episode) - 1].select_one("img[class~='zero-z-index']").get('src')

            thumbnail600x600 = thumbnail224x126
            if thumbnail600x600[-21:-19] == "CR" and thumbnail600x600 != None:
                thumbnail600x600 = thumbnail600x600[:-25] + "600" + thumbnail600x600[-22:-15] + "600,600" + thumbnail600x600[-8:]
            else:
                thumbnail600x600 = thumbnail600x600[:-17] + "600_CR1,0,600,600_AL_.jpg"
            thumbnail["224x126"] = thumbnail224x126
            thumbnail["600x600"] = thumbnail600x600


            # 進入 episode 頁面 
            sleep(random.randint(5, 12))
            res = requests.get(imdbUrl_ep, headers=headers)
            print(res.status_code)
            soup = BeautifulSoup(res.text, 'html.parser')

            # 抓取 Year、Age、IMDB、Length、Director、Actors 資料
            # title_check = soup.select_one("span[class='sc-afe43def-1 fDTGTb']").text
            excerpt = soup.select_one("span[class='sc-2eb29e65-2 jBnwaA']").text
            iMDB = float(soup.select_one("span[class='sc-bde20123-1 iZlgcd']").text)

            yal = soup.select_one("ul[class='ipc-inline-list ipc-inline-list--show-dividers sc-afe43def-4 kdXikI baseAlt']").contents
            year = int(yal[0].text[-4:])
            if len(yal) > 2:
                age = yal[1].text
            else:
                age = ""

            if len(yal[-1].text) > 3 and (("m" or "h") in yal[-1].text):
                length_hours = yal[2].text.split(' ')[0].replace('h','')
                length_mins = yal[2].text.split(' ')[1].replace('m','')
                length = int(length_hours) * 60 + int(length_mins)
            else:
                length = int(yal[2].text.replace('m','')) 


            # 抓取 Thumbnail 資料(圖片url中有藏圖片格式參數，直接進行調整)(出現新的格式，如果再有例外可能用 re 處理 比較不會出問題)
            thumbnail = {}
            try:
                img1 = soup.select_one("div[class~='sc-385ac629-7']")
                thumbnail400x532 = img1.select_one("img[class='ipc-image']")['src']
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
                print("img1(600x400) does not exist.")

            try:
                img2 = soup.select_one("div[class~='sc-385ac629-8']")    
                thumbnail600x600 = img2.select_one("img[class='ipc-image']")['src']
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
                print("img2(600x600) does not exist.")
            thumbnail["600x400"] = thumbnail400x532
            thumbnail["600x600"] = thumbnail600x600


            # 抓取 Director Name、More 資料
            da_list = []
            director_details = soup.select("ul[class='ipc-inline-list ipc-inline-list--show-dividers ipc-inline-list--inline ipc-metadata-list-item__list-content baseAlt']")[0]
            director_detail = director_details.select_one("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']")
            director_name = director_detail.text
            director_more = "https://www.imdb.com" + director_detail.get('href')
            da_list.append({"data": {"Name": director_name,
                                    "More": director_more}})

            # 抓取 Actors Name、More 資料
            actor_details = soup.select("ul[class='ipc-inline-list ipc-inline-list--show-dividers ipc-inline-list--inline ipc-metadata-list-item__list-content baseAlt']")[-1]       
            actor1_detail = actor_details.select("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']")[0]
            actor1_name = actor1_detail.text
            actor1_more = "https://www.imdb.com" + actor1_detail.get('href')
            da_list.append({"data": {"Name": actor1_name,
                                    "More": actor1_more}})
            
            try: # 若演員只有一個的話，避免跳error
                actor2_detail = actor_details.select("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']")[1]
                actor2_name = actor2_detail.text
                actor2_more = "https://www.imdb.com" + actor2_detail.get('href')
                da_list.append({"data": {"Name": actor2_name,
                                        "More": actor2_more}})
                actor3_detail =actor_details.select("a[class='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link']")[2]
                actor3_name = actor3_detail.text
                actor3_more = "https://www.imdb.com" + actor3_detail.get('href')
                da_list.append({"data": {"Name": actor3_name,
                                        "More": actor3_more}})
            except IndexError:
                da_list.append({"data": {"Name": "",
                                        "More": ""}})
                da_list.append({"data": {"Name": "",
                                        "More": ""}})
                print(f"Just have \"one\" actor.({subtitle})")

            # 抓取 Director&Actors AllRole、Bio、Born、img 資料
            for i in range(len(da_list)):
                sleep(random.randint(5, 12))
                if da_list[i]["data"]["More"] != "":
                    res = requests.get(da_list[i]["data"]["More"], headers=headers)
                    print(res.status_code)            
                    soup = BeautifulSoup(res.text, 'html.parser')
                    allRole_list = []

                    bio = soup.select_one("div[class='ipc-html-content-inner-div']").text
                    try:
                        born = soup.select("span[class='sc-dec7a8b-2 haviXP']")[1].text
                    except:
                        born = ""
                        print(f"Can't find born attr.({da_list[i]['data']['Name']})")
                            
                    allRoles = soup.select_one("ul[class='ipc-inline-list ipc-inline-list--show-dividers sc-afe43def-4 kdXikI baseAlt']").contents
                    for allRole in allRoles:
                        allRole_list.append(allRole.text)

                    # 圖片url中有藏圖片格式參數，直接進行調整
                    try:
                        img1 = soup.select_one("div[class~='sc-385ac629-7']")
                        da400x532 = img1.select_one("img[class='ipc-image']")['src']
                        if da400x532[-18:-16] == "CR":
                            pick = round(int(da400x532[-22:-19]) * (400 / int(da400x532[-12:-9])))
                            da400x532 = da400x532[:-22] + str(pick) + da400x532[-19:-12] + "400,532" + da400x532[-5:]
                        else:
                            pick = round(int(da400x532[-23:-20]) * (400 / int(da400x532[-12:-9])))
                            da400x532 = da400x532[:-23] + str(pick) + da400x532[-20:-12] + "400,532" + da400x532[-5:]
                    except:
                        da400x532 = ""
                        print(f"{da_list[i]['data']['Name']}\'s img(400x532) does not exist.")

                    try:
                        img2 = soup.select_one("div[class~='sc-385ac629-8']")
                        da600x600 = img2.select_one("img[class='ipc-image']")['src']
                        if da600x600[-18:-16] == "CR":
                            pick = round(int(da600x600[-22:-19]) * (600 / int(da600x600[-8:-5])))
                            da600x600 = da600x600[:-22] + str(pick) + da600x600[-19:-12] + "600,600" + da600x600[-5:]
                        else:
                            pick = round(int(da600x600[-23:-20]) * (600 / int(da600x600[-8:-5])))
                            da600x600 = da600x600[:-23] + str(pick) + da600x600[-20:-12] + "600,600" + da600x600[-5:]
                    except:
                        da600x600 = ""
                        print(f"{da_list[i]['data']['Name']}\'s img(600x600) does not exist.")
                    
                else:
                    allRole_list, bio, born, da400x532, da600x600  = "", "", "", "", ""

                da_list[i]["data"]["AllRole"] = allRole_list
                da_list[i]["data"]["Bio"] = bio
                da_list[i]["data"]["Born"] = born
                da_list[i]["data"]["400x532"] = da400x532
                da_list[i]["data"]["600x600"] = da600x600
                print(f"data \"{da_list[i]['data']['Name']}\" is ok!")

        else:
            subtitle, year, thumbnail, age, iMDB, length, episode = "", "", {}, "", "", "", ""
            da_list = [{"data": {}} * 4]
        
        # 將 Series 資料存入 datas 中
        datas[0]["Series"]["Subtitle"] = subtitle
        datas[0]["Series"]["Year"] = year
        datas[0]["Series"]["Thumbnail"] = thumbnail
        datas[0]["Series"]["Age"] = age
        datas[0]["Series"]["IMDB"] = iMDB
        datas[0]["Series"]["Length"] = length
        datas[0]["Series"]["Director"] = da_list[0]["data"]
        datas[0]["Series"]["Actors"] = [da_list[1]["data"], da_list[2]["data"], da_list[3]["data"]]
        datas[0]["Series"]["Episode"] = episode
        
        # 存入 Json 檔中
        with open(f'imdb_{title.replace(" ","_")}_season{season}ep{episode}.json', 'w', encoding='utf-8') as file:
            json.dump(datas, file, indent=4, ensure_ascii=False)
            print("Done!")

        # else:
        #         print(f"Season {season} is not exist.")

    else:
        print("URL may be wrong, please check again.")
'''






# 影集環節
def imdb_season_scrapy(imdbUrl:str, season:str, episode:str):
    # 基本設定
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

    # 檢查網址格式是否有誤
    pattern = r"https:\/\/www.imdb.com\/title\/tt\d+\/"
    match = re.findall(pattern, imdbUrl)
    if match:
        print("URL is correct.")
        imdbUrl = match[0]

        # 確認 season 是否是集 or 年
        if len(season) == 4:
            imdbUrl_season = imdbUrl + f"episodes?year={season}"
        elif season.lower() == "all":
            imdbUrl_season = imdbUrl + f"episodes?season=1"
        else:
            imdbUrl_season = imdbUrl + f"episodes?season={season}"

        # 防呆檢查環節
        res =  requests.get(imdbUrl_season, headers=headers)
        print(f"Season & episode check:{res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')

        # 所有季數或年份儲存 
        if "season" in imdbUrl_season:
            all_season = soup.select_one("select[id='bySeason']").select('option')
            season_list = [season.text.strip() for season in all_season]
   
        if "year" in imdbUrl_season:
            all_year = soup.select_one("select[id='byYear']").select('option')
            season_list = [year.text.strip() for year in all_year]
        
        # 檢查 season 是否存在
        if season.lower() != "all":
            try:
                season_check = soup.select_one("#episode_top").text
                if season != (season_check.replace("Season", "").strip() or season_check):
                    print(f"Season(year) {season} does not exist.")
                    return False
            except:
                print(f"Season(year) {season} does not exist, maybe season's format is wrong or this URL is for the movie, please try again.")
                return False
        
        # 檢查 episode 是否存在
        try:
            if season.lower() != "all":
                eplist = soup.select_one(".list.detail.eplist")
                eps = eplist.select(".image")
                start_ep = eps[0].select_one(".hover-over-image").text.split(',')[-1].replace('Ep','').strip()
                end_ep = int(start_ep) + len(eps) - 1
                if episode.lower() != "all":
                    try:
                        if (int(episode) - int(start_ep) + 1) > len(eps) or int(episode) < int(start_ep) or int(episode) > end_ep:
                            print(f"Episode {episode} does not exist.")
                            return False
                    except:
                        print(f"Episode's format may wrong, please try again.")
                        return False
        except:
            print(f"Episode may not exist, please try again.")
            return False
        print(f"Season & episode check ok.")

        # 檢視最後要的 season
        if season.lower() != "all":
            season_list = [season]
        print(f"Season: {(', ').join(season_list)}")

        for season in season_list:
            sleep(random.randint(3, 6))
            res = requests.get(imdbUrl, headers=headers)
            print(f"Video check:{res.status_code}")
            soup = BeautifulSoup(res.text, 'html.parser')

            datas = [
                    {
                        "Video":{
                            "Sources": []
                        },
                        "Series": {
                            "Sources": []
                        }
                    }
                ]
            # title、Excerpt、IMDB 環節
            try:
                title = soup.select_one(".sc-afe43def-3").text.replace('Original title:', '').strip()
            except:
                title = soup.select_one(".sc-afe43def-1").text

            try:
                excerpt = soup.select_one(".sc-cd57914c-2").text
            except:
                excerpt = ""
            
            try:
                iMDB = float(soup.select_one(".sc-bde20123-1 ").text)
            except:
                iMDB = ""

            # Year、Age、Length 環節
            yal = soup.select_one(".sc-afe43def-4").contents
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
        
            # 抓取 Thumbnail 資料(圖片url中有藏圖片格式參數，直接進行調整)
            thumbnail = {}
            try:
                img1 = soup.select_one(".sc-385ac629-7")
                thumbnail600x400 = img1.select_one("img.ipc-image")['src']
                if thumbnail600x400[-18:-16] == "CR": 
                    pick = round(int(thumbnail600x400[-22:-19]) * (600 / int(thumbnail600x400[-8:-5])))
                    thumbnail600x400 = thumbnail600x400[:-22] + str(pick) + thumbnail600x400[-19:-12] + "400,600" + thumbnail600x400[-5:]
                else:
                    pick = round(int(thumbnail600x400[-23:-20]) * (600 / int(thumbnail600x400[-8:-5])))
                    thumbnail600x400 = thumbnail600x400[:-23] + str(pick) + thumbnail600x400[-20:-12] + "400,600" + thumbnail600x400[-5:]
            except:
                thumbnail600x400 = ""

            try:
                img2 = soup.select_one(".sc-385ac629-8")    
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
            datas[0]["Video"]["Excerpt"] = excerpt
            datas[0]["Video"]["Year"] = year
            datas[0]["Video"]["Thumbnail"] = thumbnail
            datas[0]["Video"]["Age"] = age
            datas[0]["Video"]["IMDB"] = iMDB
            datas[0]["Video"]["Length"] = length


            # 抓取 Director&Actor Name、More 資料後暫存於 da_list 中
            da_list = [{"data": {"Name": "",
                                "More": ""}}]
            da_checks = soup.select_one(".sc-52d569c6-3")
            da_check = da_checks.select(".ipc-metadata-list__item")
            for check in da_check:
                try:
                    # 抓取 Director Name、More 資料
                    if check.select_one(".ipc-metadata-list-item__label").text == "Director" or check.select_one(".ipc-metadata-list-item__label").text == "Directors":
                        director_name = check.select_one(".ipc-metadata-list-item__list-content-item").text
                        director_more = "https://www.imdb.com/" + check.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                        da_list.append({"data": {"Name": director_name,
                                                "More": director_more}})
                    # 抓取 Actors Name、More 資料
                    elif check.select_one(".ipc-metadata-list-item__label").text == "Stars" or check.select_one(".ipc-metadata-list-item__label").text == "Star":
                        actors = check.select(".ipc-inline-list__item")
                        for actor in actors:
                            actor_name = actor.select_one(".ipc-metadata-list-item__list-content-item").text
                            actor_more = "https://www.imdb.com/" + actor.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                            da_list.append({"data": {"Name": actor_name,
                                                    "More": actor_more}})
                    else:
                        da_list.append({"data": {"Name": "",
                                                "More": ""}})
                except:
                    pass

            # 如果 Director、Actor 的資料不齊全或是格式不對的話修正
            while True:
                if da_list[1]["data"]["Name"] == "":
                    da_list.pop(1)

                if len(da_list) < 4:
                    da_list.append({"data": {"Name": "",
                                            "More": ""}})
                else:
                    break
            
            # 抓取 Director&Actors AllRole、Bio、Born、img 資料
            for i in range(len(da_list)):
                if da_list[i]["data"]["More"] != "":
                    sleep(random.randint(3, 6))
                    res = requests.get(da_list[i]["data"]["More"], headers=headers)
                    print(f"Profile \"{da_list[i]['data']['Name']}\" check:{res.status_code}")            
                    soup = BeautifulSoup(res.text, 'html.parser')
                    
                    # AllRole、Bio、Born 環節
                    bio = soup.select_one(".ipc-html-content-inner-div").text
                    try:
                        born = soup.select(".sc-dec7a8b-2")[1].text
                    except:
                        born = ""
                    
                    allRole_list = []
                    allRoles = soup.select_one(".sc-afe43def-4").contents
                    for allRole in allRoles:
                        allRole_list.append(allRole.text)

                    # 圖片url中有格式參數，直接進行調整
                    try:
                        img1 = soup.select_one(".sc-385ac629-7")
                        da400x532 = img1.select_one("img[class='ipc-image']")['src']
                        if da400x532[-18:-16] == "CR":
                            pick = round(int(da400x532[-22:-19]) * (400 / int(da400x532[-12:-9])))
                            da400x532 = da400x532[:-22] + str(pick) + da400x532[-19:-12] + "400,532" + da400x532[-5:]
                        else:
                            pick = round(int(da400x532[-23:-20]) * (400 / int(da400x532[-12:-9])))
                            da400x532 = da400x532[:-23] + str(pick) + da400x532[-20:-12] + "400,532" + da400x532[-5:]
                    except:
                        da400x532 = ""

                    try:
                        img2 = soup.select_one(".sc-385ac629-8")
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
                
                da_list[i]["data"]["AllRole"] = allRole_list
                da_list[i]["data"]["Bio"] = bio
                da_list[i]["data"]["Born"] = born
                da_list[i]["data"]["400x532"] = da400x532
                da_list[i]["data"]["600x600"] = da600x600
                print(f"Data \"{da_list[i]['data']['Name']}\" is ok!")

            # 將 Video 剩餘資料存入 datas 中
            datas[0]["Video"]["Director"] = da_list[0]["data"]
            datas[0]["Video"]["Actors"] = [da_list[1]["data"], da_list[2]["data"], da_list[3]["data"]]
            datas[0]["Video"]["Season"] = True


            ############################### 處理 season 和 episode 環節 ###############################
            sleep(random.randint(3, 6))
            res = requests.get(imdbUrl_season, headers=headers)
            print("=" * 20)
            print(f"Season {season} check:{res.status_code}")
            soup = BeautifulSoup(res.text, 'html.parser')

            # 檢查使用者輸入，如果是要整季(年)，把篇數紀錄下來
            eplist = soup.select_one(".list.detail.eplist")
            eps = eplist.select(".image")
            start_ep = eps[0].select_one(".hover-over-image").text.split(',')[-1].replace('Ep','').strip()
            end_ep = int(start_ep) + len(eps) - 1

            if episode.lower() == "all" and season in season_list:
                total_episodes = len(eps)
                low = 1
                high = total_episodes + 1
            else:
                total_episodes = 1
                try:
                    low = int(episode) - int(start_ep) + 1
                except:
                    pass
                high = low + 1
            
            # 有幾個 episode 就要有幾組資料
            new_datas = []
            for _ in range(total_episodes):
                new_datas += copy.deepcopy(datas) 


            for ep in range(low, high):
                img_ep = eps[ep - 1].select_one(".hover-over-image").text.split(',')[-1].replace('Ep','').strip()
                print(f"Episode {img_ep} is exist.")
                subtitle = eps[ep - 1].select_one('a').get('title')
                print(subtitle)
                imdbUrl_ep = "https://www.imdb.com" + eps[ep - 1].select_one('a').get('href')
                thumbnail_series = {}
                try:
                    thumbnail224x126 = eps[ep - 1].select_one("img.zero-z-index").get('src')
                    thumbnail600x600 = thumbnail224x126
                    if thumbnail600x600[-21:-19] == "CR" and thumbnail600x600 != None:
                        thumbnail600x600 = thumbnail600x600[:-25] + "1067" + thumbnail600x600[-22:-15] + "600,600" + thumbnail600x600[-8:]
                    elif thumbnail600x600 == None:
                        thumbnail600x600 = thumbnail224x126
                    else:
                        thumbnail600x600 = thumbnail600x600[:-17] + "1067_CR0,0,600,600_AL_.jpg"
                    thumbnail_series["224x126"] = thumbnail224x126
                    thumbnail_series["600x600"] = thumbnail600x600
                except:
                    thumbnail_series["224x126"] = ""
                    thumbnail_series["600x600"] = ""

                # 進入 episode 頁面 
                sleep(random.randint(3, 6))
                res = requests.get(imdbUrl_ep, headers=headers)
                print(f"Episode {img_ep} check:{res.status_code}")
                soup = BeautifulSoup(res.text, 'html.parser')

                # Excerpt、IMDB 環節
                # title_check = soup.select_one(".sc-afe43def-1").text
                try:
                    excerpt = soup.select_one(".sc-cd57914c-2").text
                except:
                    excerpt = ""

                try:
                    iMDB = float(soup.select_one(".sc-bde20123-1").text)
                except:
                    iMDB = ""

                # 抓取 Year、Age 、Length 資料 (避免資料有誤，故都用try)
                yal = soup.select_one(".sc-afe43def-4").contents
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
                    img1 = soup.select_one(".sc-385ac629-7")
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
                    img2 = soup.select_one(".sc-385ac629-8")    
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
                da_list = []
                try: 
                    da_checks = soup.select_one(".sc-52d569c6-3")
                    da_check = da_checks.select(".ipc-metadata-list__item") # 如果沒有任何 Directors、Writers、Stars 的話，這邊會 error > except
                    for check in da_check:
                        try:
                            # 抓取 Director Name、More 資料
                            if check.select_one(".ipc-metadata-list-item__label").text == "Director" or check.select_one(".ipc-metadata-list-item__label").text == "Directors":
                                director_name = check.select_one(".ipc-metadata-list-item__list-content-item").text
                                director_more = "https://www.imdb.com/" + check.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                                da_list.append({"data": {"Name": director_name,
                                                        "More": director_more}})
                            # 抓取 Actors Name、More 資料
                            elif check.select_one(".ipc-metadata-list-item__label").text == "Stars" or check.select_one(".ipc-metadata-list-item__label").text == "Star":
                                actors = check.select(".ipc-inline-list__item")
                                for actor in actors:
                                    actor_name = actor.select_one(".ipc-metadata-list-item__list-content-item").text
                                    actor_more = "https://www.imdb.com/" + actor.select_one(".ipc-metadata-list-item__list-content-item").get('href')
                                    if len(da_list) == 0:
                                        da_list.append({"data": {"Name": "",
                                                                "More": ""}})
                                        da_list.append({"data": {"Name": actor_name,
                                                                "More": actor_more}})
                                    else:
                                        da_list.append({"data": {"Name": actor_name,
                                                                "More": actor_more}})
                            else:
                                da_list.append({"data": {"Name": "",
                                                        "More": ""}})
                        except:
                            pass

                    # 如果 Director、Actor 的資料不齊全或是格式不對的話修正
                    while True:
                        if da_list[1]["data"]["Name"] == "":
                            da_list.pop(1)

                        if len(da_list) < 4:
                            da_list.append({"data": {"Name": "",
                                                    "More": ""}})
                        else:
                            break

                    # 抓取 Director&Actors AllRole、Bio、Born、img 資料
                    for i in range(len(da_list)):
                        if da_list[i]["data"]["More"] != "":
                            sleep(random.randint(3, 6))
                            res = requests.get(da_list[i]["data"]["More"], headers=headers)
                            print(f"Profile \"{da_list[i]['data']['Name']}\" check:{res.status_code}")            
                            soup = BeautifulSoup(res.text, 'html.parser')
                            
                            # AllRole、Bio、Born 環節
                            bio = soup.select_one(".ipc-html-content-inner-div").text
                            try:
                                born = soup.select(".sc-dec7a8b-2")[1].text
                            except:
                                born = ""
                            
                            allRole_list = []
                            allRoles = soup.select_one(".sc-afe43def-4").contents
                            for allRole in allRoles:
                                allRole_list.append(allRole.text)

                            # 圖片url中有格式參數，直接進行調整
                            try:
                                img1 = soup.select_one(".sc-385ac629-7")
                                da400x532 = img1.select_one("img[class='ipc-image']")['src']
                                if da400x532[-18:-16] == "CR":
                                    pick = round(int(da400x532[-22:-19]) * (400 / int(da400x532[-12:-9])))
                                    da400x532 = da400x532[:-22] + str(pick) + da400x532[-19:-12] + "400,532" + da400x532[-5:]
                                else:
                                    pick = round(int(da400x532[-23:-20]) * (400 / int(da400x532[-12:-9])))
                                    da400x532 = da400x532[:-23] + str(pick) + da400x532[-20:-12] + "400,532" + da400x532[-5:]
                            except:
                                da400x532 = ""

                            try:
                                img2 = soup.select_one(".sc-385ac629-8")
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
                        
                        da_list[i]["data"]["AllRole"] = allRole_list
                        da_list[i]["data"]["Bio"] = bio
                        da_list[i]["data"]["Born"] = born
                        da_list[i]["data"]["400x532"] = da400x532
                        da_list[i]["data"]["600x600"] = da600x600
                        print(f"Data \"{da_list[i]['data']['Name']}\" is ok!")
                except:
                    for _ in range(4 - len(da_list)):
                        da_list.append({"data": {"AllRole": "",
                                                "Bio": "",
                                                "Born": "",
                                                "Name": "",
                                                "More": "",
                                                "400x532": "",
                                                "600x600": ""}})
                    print(f"Episode {img_ep}\'s director and actors do not exist.")

            
                # 將 Series 資料存入 datas 中
                new_datas[ep - low]["Series"]["Subtitle"] = subtitle
                new_datas[ep - low]["Series"]["Year"] = year
                new_datas[ep - low]["Series"]["Thumbnail"] = thumbnail_series
                new_datas[ep - low]["Series"]["Age"] = age
                new_datas[ep - low]["Series"]["IMDB"] = iMDB
                new_datas[ep - low]["Series"]["Length"] = length
                new_datas[ep - low]["Series"]["Director"] = da_list[0]["data"]
                new_datas[ep - low]["Series"]["Actors"] = [da_list[1]["data"], da_list[2]["data"], da_list[3]["data"]]
                new_datas[ep - low]["Series"]["Episode"] = img_ep
                print(f"Episode {img_ep} done.")
                print("=" * 20)

        
            # 存入 Json 檔中
            if total_episodes > 1:
                episode = "All"
            with open(f'imdb_{title.replace(" ","_").replace(",","_").replace(":","_")}_Season{season}_Episode{episode}.json', 'w', encoding='utf-8') as file:
                json.dump(new_datas, file, indent=4, ensure_ascii=False)
                print(f"{title} : Season{season} Episode{episode} done!")
                print("=" * 20)

    else:
        print("URL may be wrong, please check again.")







if __name__ == "__main__":
    
    while True:
        menu()
        user_choice = input("Please choose what you want:")
        if user_choice == "1":
            url = input("Please enter url:")
            imdb_movie_scrapy(url)
        elif user_choice == "2":
            url = input("Please enter url:")
            season = input("Please enter season(Enter \"all\" = the entire episode):")
            episode = input("Please enter episode(Enter \"all\", the entire season ):")
            imdb_season_scrapy(url, season, episode)
        else:
            print("Bye bye.")
            break
    


    '''
    url = 'https://www.imdb.com/title/tt6315640/episodes?season=4'
    user_Agent = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:65.0) Gecko/20100101 Firefox/65.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko", # ok
        "Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; M351 Build/KTU84P) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30"]
    headers = {
        "User-Agent": random.choice(user_Agent),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache"
    }
    
    print(headers["User-Agent"])
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_season = soup.select_one("select[id='bySeason']").select('option')
    all_year = soup.select_one("select[id='byYear']").select('option')

    season_list = [season.text.strip() for season in all_season]
    year_list = [year.text.strip() for year in all_year]
    print(season_list)
    print(year_list)
    '''


    # imdb_movie_scrapy("https://www.imdb.com/title/tt1630029/")
    # imdb_season_scrapy("https://www.imdb.com/title/tt0245612/?ref_=ttep_ep_tt", "2028", "")



"session-id=144-7915252-0316834; session-id-time=2082787201l; uu=eyJpZCI6InV1OGI0YThiYjM3ZTIyNDYxZGI5NjYiLCJwcmVmZXJlbmNlcyI6eyJmaW5kX2luY2x1ZGVfYWR1bHQiOmZhbHNlfX0=; ubid-main=134-5298642-9184706; session-token=p1cE8MUYAEK8zONMTEp0rYFYkQ/2rQvCUJXh+fde/5bJDIMHMbIWAyylk1hWHwaI6l7qpvH8p7pai4vHesx94m6r8lGM0Wqbu0OY0ele0d7lkeujooRcmV+Jg+lOFJD8Wi63OITNNN+VKWiCS571Q0wT6G/44Aad19TDaQP7OBSTMo3ijuzpYECc5HKuKmqjSdnDCmpR6AWMOtgCZ2i7wG2BSTuO44ACw6BR4VrUPms; csm-hit=tb:JSACDF4X76EHRRRM90N8+s-W1XMEQ9N1Y130NNNS5SP|1685934384198&t:1685934384198&adb:adblk_no"
"session-id=144-7915252-0316834; session-id-time=2082787201l; uu=eyJpZCI6InV1OGI0YThiYjM3ZTIyNDYxZGI5NjYiLCJwcmVmZXJlbmNlcyI6eyJmaW5kX2luY2x1ZGVfYWR1bHQiOmZhbHNlfX0=; ubid-main=134-5298642-9184706; session-token=p1cE8MUYAEK8zONMTEp0rYFYkQ/2rQvCUJXh+fde/5bJDIMHMbIWAyylk1hWHwaI6l7qpvH8p7pai4vHesx94m6r8lGM0Wqbu0OY0ele0d7lkeujooRcmV+Jg+lOFJD8Wi63OITNNN+VKWiCS571Q0wT6G/44Aad19TDaQP7OBSTMo3ijuzpYECc5HKuKmqjSdnDCmpR6AWMOtgCZ2i7wG2BSTuO44ACw6BR4VrUPms; csm-hit=tb:77AMHM0VY213GQVH5P6W+s-1XHXG2XTGGQ5VE83VN8A|1685932850652&t:1685932850652&adb:adblk_no"
"session-id=144-7915252-0316834; session-id-time=2082787201l; uu=eyJpZCI6InV1OGI0YThiYjM3ZTIyNDYxZGI5NjYiLCJwcmVmZXJlbmNlcyI6eyJmaW5kX2luY2x1ZGVfYWR1bHQiOmZhbHNlfX0=; ubid-main=134-5298642-9184706; session-token=p1cE8MUYAEK8zONMTEp0rYFYkQ/2rQvCUJXh+fde/5bJDIMHMbIWAyylk1hWHwaI6l7qpvH8p7pai4vHesx94m6r8lGM0Wqbu0OY0ele0d7lkeujooRcmV+Jg+lOFJD8Wi63OITNNN+VKWiCS571Q0wT6G/44Aad19TDaQP7OBSTMo3ijuzpYECc5HKuKmqjSdnDCmpR6AWMOtgCZ2i7wG2BSTuO44ACw6BR4VrUPms; csm-hit=tb:77AMHM0VY213GQVH5P6W+s-FSRDBG5WN6VN7E61K3XB|1685931181500&t:1685931181500&adb:adblk_no"



'''
https://m.media-amazon.com/images/M/MV5BZjc2MzQ1N2QtNWMyMy00ODIwLWJjYTktMDY1YTBhOTIyMTdlXkEyXkFqcGdeQXVyNzI1NzMxNzM@._V1_QL75_UY281_CR4,0,190,281_.jpg 190w, 
https://m.media-amazon.com/images/M/MV5BZjc2MzQ1N2QtNWMyMy00ODIwLWJjYTktMDY1YTBhOTIyMTdlXkEyXkFqcGdeQXVyNzI1NzMxNzM@._V1_QL75_UY422_CR5,0,285,422_.jpg 285w, 
https://m.media-amazon.com/images/M/MV5BZjc2MzQ1N2QtNWMyMy00ODIwLWJjYTktMDY1YTBhOTIyMTdlXkEyXkFqcGdeQXVyNzI1NzMxNzM@._V1_QL75_UY562_CR7,0,380,562_.jpg 380w
'''


