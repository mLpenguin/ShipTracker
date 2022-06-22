#!/usr/bin/env python
# coding: utf-8

# In[1]:


#import requests

#import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
#from selenium.webdriver import ActionChains
import pandas as pd

import csv
import os.path
import datetime

import sys #import args
import os

#STATION_URL = "https://www.gasbuddy.com/station/38348"

options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# ## Get Fleet

# In[2]:


def getURL(URL, pageNum):
    return URL.split('?')[0] + '?page='+str(pageNum) + '&' + URL.split('?')[1]


# In[3]:


def getFleet(URL, browser):
    VESSELS = []
    
    browser.get(URL)
    
    pageNumber = browser.find_element(By.CSS_SELECTOR, ".column.vfix.pagination.top").text
    pageNumber = int(pageNumber.split('/')[1].replace(' ',''))
    
    now = datetime.datetime.now(datetime.timezone.utc)
    addDate = datetime.timedelta(1)

    PrevDay = (now-addDate).strftime("%m-%d")
    
    for i in range(1, pageNumber+1):
        print('Page: '+str(i)+' of '+str(pageNumber))
        url_pageNum = getURL(URL, i)
        browser.get(url_pageNum)
    
        name = browser.find_elements(By.CLASS_NAME, "v2")
        year = browser.find_elements(By.CLASS_NAME, "v3")
        gt = browser.find_elements(By.CLASS_NAME, "v4")
        dwt = browser.find_elements(By.CLASS_NAME, "v5")
        size = browser.find_elements(By.CLASS_NAME, "v6")
        shipLink = browser.find_elements(By.CLASS_NAME, "ship-link")

        NAME = []
        YEAR = []
        GT = []
        DWT = []
        SIZE = []
        SHIPLINK = []

        for x in range(len(name)):
            NAME.append(name[x].text)
        for x in range(1, len(year)):
            YEAR.append(year[x].text)
        for x in range(1, len(gt)):
            GT.append(gt[x].text)
        for x in range(1, len(dwt)):
            DWT.append(dwt[x].text)
        for x in range(1, len(size)):
            SIZE.append(size[x].text)
        for x in range(len(shipLink)):
            SHIPLINK.append(shipLink[x].get_attribute('href'))
        

        for x in range(len(NAME)):
            temp = [NAME[x].split('\n')[0], NAME[x].split('\n')[1], YEAR[x], GT[x], DWT[x], SIZE[x], SHIPLINK[x], PrevDay]
            VESSELS.append(temp)
    columns = ['Name','Type','Year','GT','DWT','Size','URL', 'Next_Check_Date']    
    df = pd.DataFrame(VESSELS, columns=columns)
    
    return df


# In[ ]:


'''


# In[7]:


URL = r"https://www.vesselfinder.com/vessels?type=601&flag=US"
t = getFleet(URL, browser)
t.to_csv("Ship_List/USOilTanker.csv", index=False)


# In[ ]:


'''


# In[14]:


def WithinTimeframe(time, days):
    dt = datetime.datetime.strptime(time, '%m-%d')
    dt = dt.replace(year=datetime.datetime.now().year)
    now = datetime.datetime.now()

    if((dt-now).days > days):
        return True
    else:
        return False


# In[19]:


time = '12-30'
WithinTimeframe(time, 180)


# ## Get Vessel Port Data

# In[8]:


def getPortData(URL, browser):
    #Get Data

    browser.get(URL)

    times = browser.find_elements(By.CLASS_NAME, "_1GQkK")
    names = browser.find_elements(By.CSS_SELECTOR, ".flx._rLk.t5UW5")
    
    #Get ETA
    try:
        eta = browser.find_element(By.CLASS_NAME, "_mcol12")
        eta = eta.text
        eta = eta.split('ETA: ')[1].split(',')[0]
        #print(eta)
        eta = datetime.datetime.strptime(eta, '%b %d').strftime("%m-%d")
        #eta = setYear(eta).strftime("%m-%d-%Y")
    except:
        try:
            eta = browser.find_element(By.CSS_SELECTOR, ".v3.red")
            eta = eta.text
        except:
            eta = 'None'

    TIMES = []
    NAMES = []

    for x in range(len(times)):
        TIMES.append(times[x].text)
    for x in range(len(names)):
        NAMES.append(names[x].text)
        
    #Parse Data
    PortData = []
    for x in range(len(TIMES)//3):
        PortData.append([NAMES[x], TIMES[x*3], TIMES[(x*3)+1], TIMES[(x*3)+2]])

    columns = ['Port', 'Arrival', 'Departure', 'Time in Port']

    df = pd.DataFrame(PortData, columns=columns)
    

    return df,eta


# ## Save Port Data

# In[9]:


def savePortData(inputFile, outputFile, df):

    folder='Port_Data/'+inputFile.split('.csv')[0]
    filename=outputFile+'.csv'

    isExist = os.path.exists(folder)

    if not isExist:

      # Create a new directory because it does not exist 
      os.makedirs(folder)
      print("The new directory is created!")


    #Create new file or Append Data
    if (os.path.isfile(filename)):
        importedDf = pd.read_csv (filename)

        #Combine Df
        combined = df.append(importedDf)
        combined.drop_duplicates(keep='first', inplace=True)

        df = combined

    df.to_csv(folder+'/'+filename, index=False)


# In[ ]:


'''


# In[22]:


#Port Data
importFile = "USOilTanker.csv"
df = pd.read_csv ('Ship_List/'+importFile)

for x in range(len(df)):
    print(str(x)+' of '+str(len(df)))
    URL = df.iloc[x]['URL']

    if ('-' in df.iloc[x]['Next_Check_Date']):
        dt = datetime.datetime.strptime(df.iloc[x]['Next_Check_Date'], "%m-%d")
        dt = dt.replace(year=datetime.datetime.now().year)
        now = datetime.datetime.now()

        if ((dt-now).days < -1) or WithinTimeframe(df.iloc[x]['Next_Check_Date'], 180):
            ship_name = URL.split('-IMO-')[0].split('/')[-1]

            print('Updating ' +ship_name)
            portDf, nextSaveDate = getPortData(URL, browser)
            df.at[x, 'Next_Check_Date'] = nextSaveDate
            savePortData(importFile,ship_name, portDf)


df.to_csv("Ship_List/"+importFile, index=False)


# In[21]:


options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(r'load-extension=' + r"C:/Users/truee/AppData/Local/Google/Chrome/User Data/Default/Extensions/cjpalhdlnbpafiamejdnhcphjbkeiagm/1.43.0_0")
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# In[12]:


#df = pd.read_csv ('Ship_List/'+importFile)
df


# In[ ]:


df.at[x, 'Next_Check_Date']


# In[ ]:


'''


# ## Python File Args

# In[ ]:


options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('load-extension=' + r'C:\Users\truee\AppData\Local\Google\Chrome\User Data\Default\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm\1.43.0_0')
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

command = str(sys.argv[1]).replace("\'", "")
arg1 = str(sys.argv[2]).replace("\'", "")

try:
    arg2 = str(sys.argv[3]).replace("\'", "")
except:
    pass

if command=="getportdata":
    
    importFile = arg1
    df = pd.read_csv ('Ship_List/'+importFile)



    for x in range(len(df)):
        print(str(x)+' of '+str(len(df)))
        URL = df.iloc[x]['URL']

        if ('-' in df.iloc[x]['Next_Check_Date']):
            dt = datetime.datetime.strptime(df.iloc[x]['Next_Check_Date'], "%m-%d")
            dt = dt.replace(year=datetime.datetime.now().year)
            now = datetime.datetime.now()

            if ((dt-now).days < -1) or WithinTimeframe(df.iloc[x]['Next_Check_Date'], 180):
                ship_name = URL.split('-IMO-')[0].split('/')[-1]

                print('Updating ' +ship_name)
                portDf, nextSaveDate = getPortData(URL, browser)
                df.at[x, 'Next_Check_Date'] = nextSaveDate
                savePortData(importFile,ship_name, portDf)


    df.to_csv("Ship_List/"+importFile, index=False)
    
elif command=='getfleet':
    
    URL = arg1
    t = getFleet(URL, browser)
    t.to_csv('Ship_List/'+arg2, index=False)
    
    
browser.quit()


# In[ ]:




