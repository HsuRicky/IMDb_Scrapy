import requests
from bs4 import BeautifulSoup

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

import random, copy, re, json
from time import sleep, time


# 選單
def menu():
    print("")
    print("******** MIDb Crawler System ********")
    print("1. Start to Scrapy")
    print("0 & else. Exit")
    print("***********************************")


def imdb_scrapy(imdbUrl:str, season:str, episode:str):
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
        "Cache-Control": "no-cache",
        "Cookie": "lc-main=en_US"
    }

    # 檢查網址格式是否有誤
    pattern = r"https:\/\/www.imdb.com\/title\/tt\d+\/"
    match = re.findall(pattern, imdbUrl)
    if match:
        print("URL is correct.")
        imdbUrl = match[0]

        res = requests.get(imdbUrl, headers=headers)
        print(f"Video check:{res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')

        # 電影與影集區分環節
        video_check = ""
        print("User checking...")
        try:
            stupid_check = soup.select_one('.sc-219085a0-1')
            if stupid_check == None:
                video_check = "movie"
                season_list = ["movie"]
            else:
                video_check = "series"

                # 1確認 season 是否是集 or 年
                if len(season) == 4:
                    imdbUrl_season = imdbUrl + f"episodes?year={season}"
                elif season.lower() == "all":
                    imdbUrl_season = imdbUrl + f"episodes?season=1"
                elif season.lower().strip() == "":
                    print("This URL is for series, so season is required, if you want to scrapy all season, please try again and enter \"all\".")
                    return False
                else:
                    imdbUrl_season = imdbUrl + f"episodes?season={season}"

                # 防呆檢查環節
                sleep(random.randint(3, 6))
                res =  requests.get(imdbUrl_season, headers=headers)
                print(f"Season & episode check:{res.status_code}")
                soup = BeautifulSoup(res.text, 'html.parser')

                # 2所有季數或年份儲存 
                if "season" in imdbUrl_season:
                    all_season = soup.select_one("select[id='bySeason']").select('option')
                    season_list = [season.text.strip() for season in all_season]
        
                if "year" in imdbUrl_season:
                    all_year = soup.select_one("select[id='byYear']").select('option')
                    season_list = [year.text.strip() for year in all_year]

                # 3檢查 season 是否存在
                if season.lower() != "all" and video_check == 'series':
                    try:
                        season_check = soup.select_one("#episode_top").text
                        if season != (season_check.replace("Season", "").lower().strip() or season_check):
                            print(f"Season(year) {season} does not exist.")
                            return False
                    except:
                        print(f"Season(year) {season} does not exist, maybe season's format is wrong or this URL is for the movie, please try again.")
                        return False

                # 4檢查 episode 是否存在
                try:
                    if season.lower() != "all" and video_check == 'series':
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
                
                # 5檢視最後要的 season
                if season.lower() != "all":
                    season_list = [season]
                print(f"Season: {(', ').join(season_list)}")

        except:
            print("Season may be wrong, please check again.")
            return False
        

        print(f"User ok...Type: {video_check}.")
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
            # title、Excerpt、IMDB 環節(for series)
            if video_check == "series":
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

            # title、Excerpt、IMDB 資料(for movie)
            if video_check == "movie":
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
            da_list = []
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
                    soup = BeautifulSoup(res.text, 'html.parser')
                    
                    # AllRole、Bio、Born 環節
                    try:
                        bio = soup.select_one(".sc-c1781ec7-1 .ipc-html-content-inner-div").text.replace("\n"," ")
                        if len(bio) >= 500:
                            bio = bio[:500] + "..."
                    except:
                        bio = ""
                    
                    try:
                        born = soup.select(".sc-dec7a8b-2")[1].text
                    except:
                        born = ""
                    
                    allRole_list = []
                    allRoles = soup.select(".sc-afe43def-4 li")
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
            if video_check == "series": 
                datas[0]["Video"]["Season"] = True
            else:
                datas[0]["Video"]["Season"] = False
                datas[0]["Series"] = False
                # 存入 Json 檔中
                with open(f'imdb_{title.replace(" ","_").replace(",","_").replace(":","_")}.json', 'w', encoding='utf-8') as file:
                    json.dump(datas, file, indent=4, ensure_ascii=False)
                    print(f"{title}: done!")
                    return True


            ############################### 處理 season 和 episode 環節 ###############################
            sleep(random.randint(3, 6))
            res = requests.get(imdbUrl_season, headers=headers)
            print("=" * 20)
            print(f"Season {season} check:{res.status_code}")
            print("=" * 20)
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
                subtitle = eps[ep - 1].select_one('a').get('title')
                print(f"Episode {img_ep} is exist: {subtitle}")
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
                            soup = BeautifulSoup(res.text, 'html.parser')
                            
                            # AllRole、Bio、Born 環節
                            try:
                                bio = soup.select_one(".sc-c1781ec7-1 .ipc-html-content-inner-div").text
                            except:
                                bio = ""
                            
                            try:
                                born = soup.select(".sc-dec7a8b-2")[1].text
                            except:
                                born = ""
                            
                            allRole_list = []
                            allRoles = soup.select(".sc-afe43def-4 li")
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
        user_choice = input("Please choose your want:")
        if user_choice == "1":
            url = input("Please enter url:")
            if url.strip() == "":
                print("URL is required, please try again.")
                continue

            season = input("Please enter season(or year)(Enter \"all\" = the entire episode):")
            episode = input("Please enter episode(Enter \"all\", the entire season ):")
            imdb_scrapy(url, season, episode)
        else:
            print("Bye bye.")
            break

    