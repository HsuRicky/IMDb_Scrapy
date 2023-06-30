# IMDb_Scrapy
>  first practice program，之後如果有新的網站實作，有機會在放在這邊
  
# 概述  
### **簡介:**    
>  抓取 IMDb 網站中電影及影集資料。
      
### **使用方式:**  
>  使用者輸入 IMDb 網站的電影或影集網址，若為電影網址，季數和集數不須輸入並可以抓取該電影各式資訊；若為影集網址，得輸入季數及集數，但若想爬全部季數影片，則季數輸入"all"，若想爬取某季數的影片，則級數輸入"all"。
  
# 更新環節
### 2023/6/15  
新增功能:  
>  1. 影集功能新增-全集數資料蒐集  
  
修正問題:
>  1. 修正集數的圖片bug  
>  2. 修正單集介紹頁面，若只有 stars 的話，輸出後star的第一個會跑到director那邊bug  
>  3. 修正多集數最後資料儲存會被覆蓋bug
***
### 2023/6/16  
新增功能:  
>  1. 影集和電影合併  
***
### 2023/6/19  
修正問題:  
>  1. 修正輸出中英混合，應為全英文  
>  2. 修正作者的個人資料因網站本身有缺漏導致程式bug及優化  
***
### 2023/6/20  
新增2.0版本(**之後1.0版本不再更新，以2.0為主**):  
>  1. 新增物件導向版本
>  2. 作者圖片格式跑掉，已修復  
***
### 2023/6/21  
更新:  
>  1. 優化輸出文字  
  
修正問題:  
>  1. 修正影集預覽圖格式不一致問題  
>  2. 修正影集級數內詳細資訊因格式不同而擷取不到bug  
***
### 2023/6/26  
修正問題:  
>  1. 修正作者的個人資料圖片某些格式會抓不到bug  
***
### 2023/6/27  
修正問題:  
>  1. 修正電影部分網站da環節，若只有director，導致程式直接跳到except的bug  
>  2. 修正輸入網址非IMDB 格式，直接跳error的bug  
>  3. 修正影集頁面yal(year,age,length)資料全缺的情況，會跳error的bug  
***
### 2023/6/28  
新增功能:  
>  1. 新增-執行進度條  
  
修正問題:  
>  1. 修正影片網頁結構有變化，導致沒抓到資料  
>  2. 修正影集級數頁面中，year、age、length資料缺陷的情況，漏掉case的bug  
***
### 2023/6/30  
更新:  
>  1. 優化程式排版，增加變數說明文字  
  