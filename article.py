import json
import os
import re
import time
from urllib.request import urlopen

import requests
import translators as ts
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def chrome_geturl(url):
    service = ChromeService(executable_path='./chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options,service=service) # type: ignore
    driver.get(url)
    wait = WebDriverWait(driver, 20) 
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    html_driver = driver.page_source
    driver.quit()
    return html_driver

class Article:
    #公共成员
    Main_Index=False  #用户指定
    Journal_Index=False  #get_impact_factor

    Html='' 
    Html_Driver=''

    Url=''
    Title='' #依赖html, get_title()
    Date='' #依赖html_driver
    Journal_Name='' #依赖html_driver get_journal_name()
    Abstract=''  #依赖 Html
    Abstract_Translation=''

    #主要成员
    Keywords=[]    #依赖html
    References_Link=[] #依赖html_driver
    Similar_Type=False #false 表示不筛选
    Similar_Link=[]
    #参考成员
    Impact_Factor='' #依赖html_driver
    Doi='' #依赖 html_driver get_doi()
    #Ris_Index=False
#_________________________________________________________
    def __str__(self):
        return ('Title:{}\n\nDate:{}\n\nJournal_Name:{}\n\nImpact_Factor:{}\n\nKeywords:{}\n\nDoi:{}\n\nUrl:{}\n\nReferences_Link:{}\n\nSimilar_Link:{}\n\nAbstract:{}\n\nAbstract_Translation:{}\n'
                .format(self.Title,
                        self.Date,
                        self.Journal_Name,
                        self.Impact_Factor,
                        self.Keywords,
                        self.Doi,
                        self.Url,
                        self.References_Link,
                        self.Similar_Link,
                        self.Abstract,
                        self.Abstract_Translation)
        )
#_________________________________________________________

    def __init__(self,
                 url='',
                 title='',
                 main_index=False, 
                 ris_index=False, 
                 do_nothing=False):
        #TODO 初始化时,可以选择是否需要下载RIS 因为下载RIS时需要打开文章网页,并进行点击操作,若下载不再初始化的时候就完成,第二时间去下载又要访问一次网页,浪费时间
        self.Url=url
        self.Main_Index=main_index
        self.Title=title
        
        '''        
        for key, wd in kwargs:
            
            if key =='Title' or 'title':
                self.Title=wd
            if key =='Keywords' or 'Keyword':
                self.Keywords=wd
            if key =='Abstract' or 'abstract':
                self.Abstract=wd
        '''
        if do_nothing:
            #print("什么都没做,但可能传入了链接和main_index")
            return
        if url or title:

            #self.get_html()
            #self.get_html_driver()
            #self.get_journal_index()

            if self.Main_Index:
                self.get_title()
                self.get_date()
                self.get_abstract()
                self.get_keywords()
                self.get_reference_link()
                self.get_similar_link()
            else:
                if ris_index:
                    self.get_ris()
                self.get_title()
                self.get_date()
                self.get_journal_name()
                self.get_abstract()
                self.get_impact_factor()
                self.get_doi()

        else:
            print("警告,该文章类没有传入链接,文章未定义")

        '''
        if self.Html:
            self.get_abstract()
            self.get_title()
            self.get_date()

        if self.Html_Driver:
            self.get_journal_name()
            self.get_abstract()
            self.get_title()
        '''
#_________________________________________________________

    def reset(self):
        self.Journal_Index=False
        self.Html=''
        self.Html_Driver=''
        self.Url=''
        self.Title=''
        self.Date=''
        self.Journal_Name=''
        self.Abstract=''
        self.Abstract_Translation=''
        self.Keywords=[]
        self.References_Link=[]
        self.Impact_Factor=''
        self.Doi=''
        self.Similar_Link=[]
        #Ris_Index=False  
        return True
#_________________________________________________________

    def get_all(self):
        if self.Url or self.Title:
            self.get_title() #无需检测值是否存在,函数内自己会检测
            self.get_date()
            self.get_journal_name()
            self.get_abstract()
            self.get_impact_factor()
            self.get_doi()
            return True
        else:
            print('get_all: 缺失信息')
            return False
#_________________________________________________________

    def get_url(self,url=''):
        if url:
            self.reset()
            self.Url=url
            return True
        elif self.Url:
            #print('no need getting url')
            return True
        elif self.Title:
            url = ("https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=" + self.Title).replace(' ', '%20') # type: ignore
            html_driver = chrome_geturl(url)
            bs = BeautifulSoup(html_driver, 'lxml')
            self.Url = 'https://ieeexplore.ieee.org' + bs.find('h3', {'class': "text-md-md-lh"}).find('a').get('href')# type: ignore
            return True
        else:
            print('没有标题和链接,无法初始化')
            return False     
#_________________________________________________________

    def get_title(self,title=''):
        #print("get_title")
        if title:
            self.reset()
            self.Title=title
            return True
        elif self.Title:
            #print('已有标题')
            return True
        
        elif self.get_html():
            bs=BeautifulSoup(self.Html,"lxml")
            self.Title=bs.find("title").find_next_sibling().get('content') # type: ignore
            return True
        else:
            print('get_title:获取标题失败,文章未定义,链接缺失')
            return False
#_________________________________________________________

    def get_html(self):
        #print("get_html")
        #if self.Url:  #如果加了这行, 后面很多函数在 做 get_html之前不用再检测  //更新下,这行不能要
        #为何不在这里检测Url?? 是为了防止循环 例如在get_abstract 中没有 if self.Url检测,则陷入循环
        if self.Html:
            return True
        elif self.get_url():
            self.Html=urlopen(self.Url).read().decode() #byte类型->字符型
            return True
        return False
#_________________________________________________________

    def get_html_driver(self):
        #print("get_html_driver")
        #注意驱动的位置
        if self.Html_Driver:
            return True
        
        elif self.get_url():
            url=self.Url+'references#references' if self.Url[-1]=='/' else self.Url+'/references#references'
            self.Html_Driver = chrome_geturl(url)
            return True
        else:
            return False
#_________________________________________________________

    def get_abstract(self):
        #print("get_abstract")
        #如果发生异常,需要修改包'translators'的源码,将链接translate.google.cn改为.com
        if self.Abstract:
            #print('已有摘要')
            return True
    
        elif self.get_html():
            bs=BeautifulSoup(self.Html,"lxml")
            try:
                self.Abstract = bs.find('meta', {'property': 'twitter:description'})['content']# type: ignore #.replace('\n','')
            except:
                print(f'该文章没有摘要{self.Url}')
                return True
            
            if self.Abstract:
                try:
                    #5.16日之后的tranlators 包修改了方法,如果报错没有该方法,请根据官网文档自行修改
                    self.Abstract_Translation=ts.google(self.Abstract,from_language="en",to_language='zh', host_url="https://translate.google.com/") # type: ignore
                    return True
                except:
                    print(f'翻译失败{self.Url}')
                    return True
            return True
           
        #elif self.Url:
        #        self.get_html()
        #        self.get_abstract()
        #        return True
        #elif self.Title:
        #    self.get_url()
        #    self.get_abstract()
        #    return True
        else:
            print('get_abstract:获取摘要失败,文章未定义,链接标题缺失')
            return False

#_________________________________________________________      

    def get_date(self):
        #print("get_date")
        if self.Date:
            #print('已有日期')
            return True
        
        #elif self.Html_Driver:
        elif self.get_html_driver():
            bs_driver=BeautifulSoup(self.Html_Driver,"lxml")
            try:
                if bs_driver.find('strong', text='Date of Publication:'):
                    self.Date=bs_driver.find('strong', text='Date of Publication:').next_sibling # type: ignore
                    return True

                elif bs_driver.find('strong', text='Date of Conference: '):
                    self.Date=bs_driver.find('strong', text='Date of Conference: ').next_sibling # type: ignore
                    return True
                print(f'无日期信息{self.Url}')
                return False
            except:
                print(f'无日期信息{self.Url}')
                return False
        else:
            print('get_date:获取日期失败,文章未定义,链接缺失')
            return False
#_________________________________________________________

    def get_doi(self):
        #print("get_doi")
        if self.Doi:
            #print("已经有了Doi")
            return True
        
        elif self.get_html_driver():
            bs_driver=BeautifulSoup(self.Html_Driver,"lxml")
            try:
                self.Doi=bs_driver.find('strong', text='DOI: ').find_next_sibling().get_text() # type: ignore
                #Doi_link='https://doi.org/'+doi
                return True
            except:
                print(f'没有Doi{self.Url}')
                return False
        else:
            print('获取doi失败,文章未定义,链接缺失')
            return False
#_________________________________________________________

    def get_journal_name(self):
        #print("get_journal_name")
        if self.Journal_Name:
            #print("已经有了期刊名/会议名")
            return True
        
        elif self.get_html_driver():
            bs_driver=BeautifulSoup(self.Html_Driver,"lxml")
            try:
                self.Journal_Name=bs_driver.find('strong', text='Published in: ').find_next_sibling().get_text() # type: ignore
                return True
            except:
                print(f'没有期刊名{self.Url}')
        else:
            print('get_journal_name:获取期刊名/会议名失败,文章未定义,链接缺失')
            return False
#_________________________________________________________

    def get_keywords(self,kw=[]): #Html
        #print("get_keywords")
        if kw:
            self.Keywords=kw
            return True
        elif self.Keywords:
            #print("已经有了关键词")
            return True
        elif self.get_html():
            match=re.search(r'"Author Keywords\s*","kwd":\[.*?\]',self.Html,re.DOTALL)
            if match:
                match=re.search(r'\[.*\]',match.group(),re.DOTALL)
                self.Keywords=json.loads(match.group())
                return True
            else:
                print('没有作者关键词')
                return True
        else:
            print("get_keywords:获取关键词失败,文章未定义,链接缺失")
            return False
#_________________________________________________________

    def get_journal_index(self):
        #print("get_journal_index")
        if self.get_html_driver():
            bs_driver=BeautifulSoup(self.Html_Driver,"lxml")

            if bs_driver.find(href="/browse/periodicals/title/"):
                self.Journal_Index=True  #this is a Journals or Magazines paper'
                return True
            else:
                return True
        else:
            print("get_journal_index:获取期刊会议指标失败,文章未定义,链接缺失")
            return False
#_________________________________________________________

    def get_impact_factor(self):
        if self.Impact_Factor:
            #print('已有影响因子')
            return True
        #print("get_impact_factor")
        #elif self.Html_Driver:
        #    self.get_journal_index()
        elif self.get_journal_index():
            if self.Journal_Index:

                bs_driver=BeautifulSoup(self.Html_Driver,"lxml")

                if bs_driver.find(href="/browse/periodicals/title/"):

                    try:
                        self.Journal_Index=True  #this is a Journals or Magazines paper'

                        journal_link='https://ieeexplore.ieee.org'+bs_driver.find('strong', text='Published in: ').find_next_sibling().get('href') # type: ignore
                        journal_html = chrome_geturl(journal_link)

                        bs_temp=BeautifulSoup(journal_html,"lxml")
                        self.Impact_Factor=bs_temp.find('a',{'class':'stats-jhp-impact-factor'}).find('span',{'class':'text-md-md-lh'}).get_text() # type: ignore
                    except:
                        print(f'无法获取因子{self.Url}')
                    return True
                else :
                    self.Impact_Factor=''
                    return True
        else:
            print("get_impact_factor:获取因子失败,文章未定义,链接缺失")
            return False
#_________________________________________________________

    def get_reference_link(self):
        #print("get_reference_link")
        if self.References_Link:
            return True
        if self.get_html_driver():
            bs_driver=BeautifulSoup(self.Html_Driver,"lxml")
            View_Article=bs_driver.find_all("a",{"class":'stats-reference-link-viewArticle'})
            #CrossRef=bs_driver.find_all("a",{"class":'stats-reference-link-crossRef'})
            if not View_Article:
                print('没有IEEE上的参考文献')
                return True
            
            View_Article_list=[]
            #CrossRef_list=[]

            for article in View_Article:
                if article:
                    View_Article_list.append(article.get("href"))
            
            temp=['https://ieeexplore.ieee.org'+link for link in View_Article_list]
            self.References_Link=sorted(set(temp),key=temp.index)
            
            '''
            for article in CrossRef:
                if article:
                    CrossRef_list.append(article.get("href"))
            '''
            return True
        else:
            print("get_reference_link:获取参考文献失败,文章未定义,链接缺失")
            return False   
#_________________________________________________________

    def get_pdf(self, save_path='./pdf/'):#需要添加异常处理,如没有获取到文档
        if self.get_doi():

            scihub_link='https://sci-hub.se/'+self.Doi
            scihub_html=urlopen(scihub_link).read()
            bs_pdf=BeautifulSoup(scihub_html,"lxml")
            pdf_link='https:'+bs_pdf.find('embed',{'type':"application/pdf"}).get('src') # type: ignore
        
            if not pdf_link:
                print('no pdf file')
                return True
            
            response = requests.get(pdf_link)
            file_name =self.Title+'.pdf' if self.Title else os.path.basename(pdf_link)+'.pdf' # type: ignore

            with open(save_path+file_name, 'wb') as f:
                f.write(response.content)
            print(f'下载完成,文件在{save_path}{file_name}')
            return True
        else:
            print("get_pdf:获取pdf失败,文章未定义,链接缺失")
            return False
#_________________________________________

    def get_ris(self,save_path='./ris/'):
        if self.get_title():
            try:
                service = ChromeService(executable_path='./chromedriver.exe')
                options = webdriver.ChromeOptions()
                options.add_argument('--headless=new')
                driver = webdriver.Chrome(options=options,service=service) # type: ignore
                driver.get(self.Url)
                wait = WebDriverWait(driver, 20) 
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                
                if self.Html_Driver :
                    self.Html_Driver = driver.page_source

                cite_this_button=driver.find_element(By.XPATH, '//button[text()="Cite This"]')
                cite_this_button.click()

                ris_button = driver.find_element(By.XPATH, '//a[@class="document-tab-link" and @title="RIS"]')
                ris_button.click()

                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                element = wait.until(EC.presence_of_element_located((By.XPATH, '//pre[contains(concat(" ", normalize-space(@class), " "), "text ris-text")]')))
                
                save_path=save_path if save_path[-1]=='/' else save_path+'/'
                with open(save_path+self.Title+'.ris','w') as f:
                    f.write(element.text)
            except:
                print(f'下载RIS失败{self.Url}')
                return False
        else:
            print("get_ris:下载ris失败,没有标题,且链接缺失")
            return False

#_________________________________________________________

    def get_similar_link(self,**index): # index筛选选项 TODO 有问题
        if self.Similar_Link and not index :
            print('已有相似文献链接')
            return True
        elif index and index['similar type']!=self.Similar_Type:
            self.Similar_Type=index

        if self.get_keywords():
            base_url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText="
            query = " OR ".join('("%s":"%s")' % ("All Metadata", item) for item in self.Keywords)
            endline='&refinements=ContentType:Journals&refinements=ContentType:Magazines'
            url = (base_url + query+endline) if self.Similar_Type else (base_url + query)

            service = ChromeService(executable_path='./chromedriver.exe')
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            driver = webdriver.Chrome(options=options,service=service) # type: ignore
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME,'text-md-md-lh')))
            
            html_driver = driver.page_source
            driver.quit()

            #html_byte=urlopen(url).html.read()

            soup = BeautifulSoup(html_driver, features="lxml")
            results = soup.find_all("h3")
            link_list=[]

            for results_i in results:
                if results_i.find("a"):
                    href=results_i.find("a").get("href")
                    link_list.append(href)

            link_list=sorted(set(link_list),key=link_list.index)

            self.Similar_Link= ['https://ieeexplore.ieee.org'+link for link in link_list]
            return True
        else:
            print('失败')
            return False

if __name__=="__main__":
    url_conference="https://ieeexplore.ieee.org/document/7809977"
    url_trans='https://ieeexplore.ieee.org/document/5165285'

    conference=Article(url_conference,main_index=True)
    trans=Article(url_trans,ris_index=True)
    print(conference)
    print(trans)