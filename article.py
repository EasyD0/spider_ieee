import time
from selenium import webdriver
#from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
import translators as ts
import json
import requests
import os
from selenium.webdriver.chrome.service import Service as ChromeService

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
    Similar_Link=[]
    #参考成员
    Impact_Factor='' #依赖html_driver
    Doi='' #依赖 html_driver get_doi()
    #Ris_Index=False
#_________________________________________________________
    def __str__(self):
        return ('Title:{}\n\
                Date:{}\n\
                Journal_Name:{}\n\
                Impact_Factor:{}\n\
                Keywords:{}\n\
                Doi:{}\n\
                Url:{}\n\
                References_Link:{}\n\
                Similar_Link:{}\n\
                Abstract:{}\n\
                Abstract_Translation:{}'
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

    def __init__(self,
                 url='',
                 title='',
                 main_index=False, 
                 ris_index=False, 
                 do_nothing=''):
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
        if do_nothing=='yes':
            print("什么都没做,但可能传入了链接和main_index")
            return True
        if url or title:

            '''            
            self.get_html()
            if not self.Main_Index:
                self.get_html_driver()
            '''

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
                self.get_title()
                self.get_date()
                self.get_journal_name()
                self.get_abstract()
                self.get_impact_factor()
                self.get_doi()
                if ris_index:
                    self.get_ris()
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

            # 注意驱动的位置
            service = ChromeService(executable_path='./chromedriver.exe')
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            driver = webdriver.Chrome(options=options,service=service) # type: ignore
            driver.get(url)
            time.sleep(5)
            html_driver = driver.page_source
            driver.quit()
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
            service = ChromeService(executable_path='./chromedriver.exe')
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            driver = webdriver.Chrome(options=options, service=service)
            #driver = webdriver.Chrome(executable_path='./chromedriver.exe',options=webdriver.ChromeOptions().add_argument('--headless=new')) # type: ignore
            driver.get(self.Url)
            time.sleep(10)
            self.Html_Driver = driver.page_source
            driver.quit()
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
            self.Abstract = str(bs.find('meta', {'property': 'twitter:description'})['content'])# type: ignore #.replace('\n','')
            #用str防止Nonetype 报错 !似乎不需要了
            
            if self.Abstract:
                #5.16日之后的tranlators 包修改了方法,如果报错没有该方法,请根据官网文档自行修改
                self.Abstract_Translation=ts.google(self.Abstract,from_language="en",to_language='zh', host_url="https://translate.google.com/")
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
        elif self.get_journal_index():
            bs_driver=BeautifulSoup(self.Html_Driver,"lxml")
            
            if self.Journal_Index:
                if bs_driver.find('strong', text='Date of Publication:'):
                    self.Date=bs_driver.find('strong', text='Date of Publication:').next_sibling # type: ignore
                    return True
                else:
                    print('无日期信息')
                    return False
            else:
                if bs_driver.find('strong', text='Date of Conference: '):
                    self.Date=bs_driver.find('strong', text='Date of Conference: ').next_sibling # type: ignore
                    return True
                else:
                    print('无日期信息')
                    return False    

        elif self.get_html_driver():
            self.get_date()
            return True
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
            self.Doi=bs_driver.find('strong', text='DOI: ').find_next_sibling().get_text() # type: ignore
            #Doi_link='https://doi.org/'+doi
            return True
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
            self.Journal_Name=bs_driver.find('strong', text='Published in: ').find_next_sibling().get_text() # type: ignore
            return True
        else:
            print('get_journal_name:获取期刊名/会议名失败,文章未定义,链接缺失')
            return False
#_________________________________________________________

    def get_keywords(self): #Html
        #print("get_keywords")
        if self.Keywords:
            #print("已经有了关键词")
            return True
        elif self.get_html():
            match=re.search(r'"Author Keywords\s*","kwd":\[.*?\]',self.Html,re.DOTALL)
            match=re.search(r'\[.*\]',match.group(),re.DOTALL)
            if match:
                self.Keywords=json.loads(match.group())
                return True
            else:
                print('没有作者关键词')
                return False
            '''            
            bs=BeautifulSoup(self.Html,"lxml")
            temp=bs.find("body",{"class","body-resp"}).find('div', id="LayoutWrapper").find('div', {"class",'col'}).find_all("script", type="text/javascript") # type: ignore
            for script_tag in temp:
                if script_tag:
                    script_text=script_tag.string
                    if script_text:
                        match = re.search(r'xplGlobal\.document\.metadata\s*=\s*(\{.*?\};)', script_text, re.DOTALL) #正则表达式匹配
                        if match:
                            metadata_text = match.group()
                            break
                    else:
                        continue
                else:
                    continue
            
            keywords_string=re.search(r'"keywords":\s*\[.*?\],"', metadata_text, re.DOTALL).group() # type: ignore
            All_Keywords_list_string=re.search(r'\[.*\]', keywords_string, re.DOTALL)
            self.Keywords=json.loads(All_Keywords_list_string.group())[3]['kwd'] # type: ignore
            return True
            '''

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
                    
                    self.Journal_Index=True  #this is a Journals or Magazines paper'

                    journal_link='https://ieeexplore.ieee.org'+bs_driver.find('strong', text='Published in: ').find_next_sibling().get('href') # type: ignore
                    
                    service = ChromeService(executable_path='./chromedriver.exe')
                    options = webdriver.ChromeOptions()
                    options.add_argument('--headless=new')
                    driver = webdriver.Chrome(options=options, service=service)
                    #driver = webdriver.Chrome(executable_path='./chromedriver.exe',options=webdriver.ChromeOptions().add_argument('--headless=new'))
                    driver.get(journal_link)
                    time.sleep(5)
                    journal_html = driver.page_source
                    driver.quit()

                    bs_temp=BeautifulSoup(journal_html,"lxml")
                    self.Impact_Factor=bs_temp.find('a',{'class':'stats-jhp-impact-factor'}).find('span',{'class':'text-md-md-lh'}).get_text() # type: ignore
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

    def get_pdf(self, save_path='.\\pdf\\'):#需要添加异常处理,如没有获取到文档
        if self.get_doi():

            scihub_link='https://sci-hub.se/'+self.Doi
            scihub_html=urlopen(scihub_link).read()
            bs_pdf=BeautifulSoup(scihub_html,"lxml")
            pdf_link='https:'+bs_pdf.find('embed',{'type':"application/pdf"}).get('src') # type: ignore

            response = requests.get(pdf_link)


            file_name =self.Title+'.pdf' if self.Title else os.path.basename(pdf_link)+'.pdf' # type: ignore

            with open(save_path+file_name, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print("get_pdf:获取pdf失败,文章未定义,链接缺失")
            return False
#_________________________________________

    def get_ris(self,save_path=''):
        if self.get_doi():
            #TODO 参考下载方法
            return True
        else:
            print("get_ris:下载ris失败,没有标题,且链接缺失")
            return False


        save_path = '.\\{}.pdf'.format(self.Title) if not save_path else save_path
        #TODO 具体算法

        return True
#_________________________________________________________

    def get_similar_link(self): #TODO
        if self.Similar_Link:
            return True
        elif self.get_keywords():
            base_url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText="
            query = " OR ".join('("%s":"%s")' % ("All Metadata", item) for item in self.Keywords)
            url = base_url + query
            service = ChromeService(executable_path='./chromedriver.exe')
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            MyDriver = webdriver.Chrome(options=options, service=service)
            #MyDriver = webdriver.Chrome(options=webdriver.ChromeOptions().add_argument('--headless=new'))# type: ignore
            MyDriver.get(url)
            time.sleep(5)
            html = MyDriver.page_source
            MyDriver.quit()

            #html_byte=urlopen(url).html.read()

            soup = BeautifulSoup(html, features="lxml")
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
'''    print(conference.Main_Index)
    print(conference.Journal_Index)
    print(conference.Title)
    print(conference.Date)
    print(conference.Journal_Name)
    print(conference.Abstract)
    print(conference.Abstract_Translation)
    print(conference.Keywords)
    print(conference.References_Link)
    print(conference.Impact_Factor)
    print(conference.Doi)

    print(trans.Main_Index)
    print(trans.Journal_Index)
    print(trans.Title)
    print(trans.Date)
    print(trans.Journal_Name)
    print(trans.Abstract)
    print(trans.Abstract_Translation)
    print(trans.Keywords)
    print(trans.References_Link)
    print(trans.Impact_Factor)
    print(trans.Doi)'''