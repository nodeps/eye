#coding=utf-8
import requests
from bs4 import BeautifulSoup
from PIL import Image
import os
import sqlite3

import sys
import json

conn = sqlite3.connect('face.db')
c = conn.cursor()
all_url = 'http://m.mm131.com/xinggan/'
api_server = "https://api-cn.faceplusplus.com/facepp/v3/detect"

#http请求头
Hostreferer = {
    'User-Agent':'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
    'Referer':'http://m.mm131.com'
}
Picreferer = {
    'User-Agent':'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
    'Referer':'http://img1.mm131.me/'
}
start_html = requests.get(all_url,headers = Hostreferer)

#保存地址
rootPath = os.path.abspath('.')
picPath  = rootPath + '/131/'
starPath = rootPath + '/star/'
facePath = rootPath + '/face/'
if (not os.path.exists(starPath)):
    os.makedirs(starPath)
if (not os.path.exists(facePath)):
    os.makedirs(facePath)
#找寻最大页数
soup = BeautifulSoup(start_html.content, 'lxml')
page = soup.find_all('span',class_='rw')
max_page = page[-1].text.split('/')[1].replace('页','')
print('页数: '+str(max_page))
same_url = 'http://m.mm131.com/xinggan/list_6_'
def facePP(image, type):
    data = {
        'api_key': 'WHdONELB_PcGZSV_J9qcbJMZ3Fzjx75N',
        'api_secret': '_bGpn2n9Cr4cZWNz32A1ACLdrrr2PNW3',
        'return_attributes':'beauty,gender,age,smiling,emotion',
    }
    files = {
        'image_file': image
    }
    try:
        res = requests.post(api_server, data=data, files=files, headers = Hostreferer)
        params = json.loads(res.text)
        n = len(params['faces'])
        if n < 1:
            print( '未识别出人脸')
            return False
        for face in params['faces']:
            faceR = face['face_rectangle']
            faceArea = (faceR['left'], faceR['top'], faceR['left']+faceR['width'], faceR['top']+faceR['height'])
            if face['attributes']:
                sc = face['attributes']['beauty']['female_score']
                if sc > 80:
                    print('发现高颜值美女: '+str(sc))
                    return [sc, faceArea]
                else:
                    print('颜值: '+str(sc)+' 跳过')
                    return [0, 0]
            else:
                print('未识别 跳过')
                return [0, 0]
    except Exception as e:
        print(e)
for n in range(1,int(max_page)+1):
    if(n == 1):
        url = 'http://m.mm131.com/xinggan/'
    else:
        url = same_url+str(n)+'.html'
    start_html = requests.get(url, headers = Hostreferer)
    soup = BeautifulSoup(start_html.content, 'lxml')
    all_a = soup.find_all('div',class_='post-content')
    for content in all_a:
        a = content.a
        cover = requests.get(a.img['data-img'], headers = Hostreferer)
        coverImg= a.img['data-img'].split(r'/')[-2]+'.jpg'
        img = open(starPath + coverImg,'wb')
        img.write(cover.content)
        img.close()
        ssc = facePP(cover.content, 2) or [0, 0]
        if ssc[0] > 80:
            title = a.find('img').get('alt') #提取文本
            title_preview = str(int(ssc[0]*1000)) 
            # title = a.img['data-img'].split(r'/')[-2]
            sql_find = "select id from FACE where id = %d" % (int(a.img['data-img'].split(r'/')[-2]))
            results = c.execute(sql_find)
            all_faces = results.fetchall()
            
            if len(all_faces) == 0:
                
                # 防止颜值每次打分有细微差别导致多生成一次图片
                sql = "insert into FACE (id,name,score) values(%d,'%s',%r)" % (int(a.img['data-img'].split(r'/')[-2]), a.find('img').get('alt'), ssc[0])
                c.execute(sql)

                # 生成人脸小图
                img = Image.open(starPath + coverImg)
                cropped_img = img.crop(ssc[1]).convert('RGB')
                cropped_img.save(facePath + title_preview + '.jpg')
                print('插入数据库成功')
                conn.commit()
                
            
            if(title != ''):
                print("准备扒取："+title)
                #win不能创建带？的目录
                if(os.path.exists(picPath+title.strip().replace('?',''))):
                    #print('目录已存在')
                    flag=1
                else:
                    os.makedirs(picPath+title.strip().replace('?',''))
                    flag=0
                os.chdir(picPath + title.strip().replace('?',''))
                href = a['href'].replace('www','m')
                
                html = requests.get(href,headers = Hostreferer)
                mess = BeautifulSoup(html.content, 'lxml')
                pic_max = mess.find_all('span',class_='rw')
                pic_max = pic_max[-1].text #最大页数
                pic_max = pic_max.split(r'/')[-1].replace('页','')
                print('共'+str(pic_max)+'张')
                if(flag == 1 and len(os.listdir(picPath+title.strip().replace('?',''))) >= int(pic_max)):
                    print('已经保存完毕，跳过')
                    continue
                for num in range(1,int(pic_max)+1):
                    if(num == 1):
                        pic = href
                    else:
                        pic = href.replace('.html', '')+'_'+str(num)+'.html'
                    html = requests.get(pic,headers = Hostreferer)
                    mess = BeautifulSoup(html.content, 'lxml')
                    pic_url = mess.select('img[src*="http://img1.mm131.me/pic/"]')[0]
                    html = requests.get(pic_url['src'],headers = Hostreferer)
                    file_name = pic_url['src'].split(r'/')[-1]
                    f = open(file_name,'wb')
                    f.write(html.content)
                    f.close()
                print('完成')
    print('第',n,'页完成')
conn.close()


