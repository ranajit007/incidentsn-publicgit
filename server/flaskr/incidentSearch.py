# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 12:03:09 2020

Clase para buscar incidentes en Service now:
import os
from IncidentSearch import IncidentSearch as BotSN
os.chdir(os.path.dirname(os.path.abspath(__file__)))
dictionary = [ { "ticket_number": "IM0035560457"},
              { "ticket_number": "INC00848976"} ]

worker = BotSN(user_id="....",
                        user_pass="....",
                        show_browser=True,
                        max_login=5)
lista_descrip = worker.process_list(dictionary);
print(lista_descrip)
@author: JorgeCarlosBustillos
"""
import traceback,os,pymongo, json, xmltodict, re, asyncio, httpx
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display
from sys import platform
import datetime
import time as time_os

class IncidentSearch:
    #Config
    sn_url = "https://nestle.service-now.com/nav_to.do?uri=%2F$sn_global_search_results.do%3Fsysparm_search%3D"
    sn_title = "PROD"
    def __init__(self,
                 mongo_ip,
                 user_id,
                 user_pass,
                 show_browser=False,
                 max_login=5,
                 max_connections = 5
                 ):     
        '''
        Instancia de la búsqueda de descripción de incidentes

        Parameters
        ----------
        mongo_ip: string
            BD mongo.        
        user_id : string
            Usuario para ServiceNow.
        user_pass : string
            Contraseña para ServiceNow.
        show_browser : bool, optional
            Si se desea mostrar el navegador. The default is False.
        max_login : int, optional
            Intentos máximos login. The default is 5.

        Returns
        -------
        None.

        '''
        self.show_browser = show_browser
        self.max_login = max_login
        self.user_id = user_id
        self.user_pass = user_pass
        self.mongo_ip = mongo_ip        
        self.db_client = pymongo.MongoClient(mongo_ip)
        self.max_connections = max_connections
        self.db_col = self.db_client["service_now"]["incidents_ewm_full"]
        self.session = False
        self.session_aio = False
        self.display = None
        self.driver = None

    
    def __del__(self):
        if self.driver != None:
            self.driver.quit()
        if self.driver != None:
            self.display.stop()
         
    def _initialize_browser(self,do_login=True):
        '''
        Initializes Firefox Webbrowser using selenium
        Returns
        -------
        None.

        '''
        location = os.path.dirname(os.path.abspath(__file__))
        location = location + "/geckodriver"
        if platform == "linux" or platform == "linux2":
            if self.driver != None:
                self.display.stop()
                self.display = None
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference('intl.accept_languages', 'en-us')
        firefox_profile.set_preference('permissions.default.stylesheet', 2)
        firefox_profile.set_preference('permissions.default.image', 2)
        firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        
        options = Options()
        if self.show_browser == False:
            options.add_argument('--headless')            
        self.driver = webdriver.Firefox(firefox_profile=firefox_profile,
                                        executable_path=location,
                                        timeout=30,
                                        options=options)
        self.driver.set_window_position(0,0)
        self.driver.set_window_size(1000,600)
        self.wait  = WebDriverWait(self.driver, 30)    
        if do_login == True:
            self._do_login()
        return self.driver
        
    def _do_login(self):
        '''
        Logins in service now

        Returns
        -------
        None.

        '''
        time_os.sleep(2)
        print("LOGIN " + self.user_id)
        #Ir a login
        if "sts02.nestle.com" not in self.driver.current_url:
            self.driver.get(self.sn_url)
            self.wait.until(
                EC.title_contains("Sign")
            )
        #Ya inicio sesión
        if "sts02.nestle.com" not in self.driver.current_url:
            return 
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "userNameInput"))
        )
        #Inicio de Sesión
        input_username= self.driver.find_element_by_name("UserName")
        input_password= self.driver.find_element_by_name("Password")
        input_username.clear()
        input_password.clear()
        input_username.send_keys(self.user_id)
        input_password.send_keys(self.user_pass)
        input_password.send_keys(Keys.RETURN)
        iframe_id= "gsft_main"
        self.wait.until(
            EC.visibility_of_element_located((By.ID, iframe_id))
        )
        self.wait.until(
            EC.title_contains(self.sn_title)
        )
        return

    async def _get_cookies_async(self):
        '''
        Generates a AIO ClientSession

        Returns
        -------
        ARRAY
            Dictionary of cookies.

        '''
        if self.session_aio != False:
            return self.session_aio
        self._initialize_browser()
        cookies = self.driver.get_cookies()
        if self.driver != None:
            self.driver.quit()        
        self.session_aio = {}
        for cookie in cookies:
            self.session_aio[cookie['name']] = cookie['value']
        return self.session_aio

    async def new_requests(self, save_num=20):
        '''
        Gets the new incident list from service now
        Updates worknotes
        Updates categories
        Parameters
        ----------
        save_num : INTEGER, optional
            Number of items before saving to database. The default is 20.

        Returns
        -------
        bool
            Indicator if request was successful.

        '''
        url = "https://nestle.service-now.com/incident_list.do?sysparm_query=assignment_group%3D6ff9c022db8cab00856c8a3a48961975%5EORassignment_group%3D207b3c74db5c089468a4f7131d9619d0%5EORassignment_group%3Da7f9c022db8cab00856c8a3a48961999%5EORassignment_group%3De10ac422db8cab00856c8a3a4896199b%5EORassignment_group%3Da461483edb55a780856c8a3a48961932%5EORassignment_group%3De7f9c022db8cab00856c8a3a489619a7%5EORassignment_group%3D73f9c022db8cab00856c8a3a489619b3%5EORassignment_group%3De7f9c022db8cab00856c8a3a48961986%5EORassignment_group%3Ddfa37036db8b7b405848ff261d9619fe%5EORassignment_group%3Dc3331d32db44e7005ac9d18c68961946%5EORassignment_group%3Dcf62a6fadb2833c8ceccff261d9619bf%5EORassignment_group%3D5168906fdb29d0148aa20ae5f39619e7%5EORassignment_group%3D22696b2adbec1094b7a6d844ca9619a8%5Esys_created_onBETWEENjavascript:gs.beginningOfLastWeek()@javascript:gs.endOfToday()&sysparm_first_row=1&sysparm_view=&JSONv2"
        cookies = await self._get_cookies_async()
        print("DOWNLOAD LAST WEEK BS_SC EWM_NAR_IBM  / BS_SC WH_IBM----")
        content = await self._get_url(url,cookies)
        j = json.loads(content)
        insertList = []
        total = len(j["records"])
        for idx, incident in enumerate(j["records"]):
            query = {"number": incident["number"]}
            incident["features_pending"] = True
            document = self.db_col.find_one(query)
            if document != None:
                del incident["work_notes"]
                newValues = { "$set": incident }
                self.db_col.update_one(query, newValues)
            else:
                insertList.append(incident)
            insertList = self._partial_save(insertList,idx, save_num, total)
        print("UPSERT BS_SC EWM_NAR_IBM / BS_SC WH_IBM ---- " + str(len(j["records"])) + " records")
        semaphore = asyncio.Semaphore(value=self.max_connections)
        await self.update_pending(cookies,semaphore)
        await asyncio.wait([
            self.update_all_work_notes(cookies,semaphore),
            self.update_all_category(cookies,semaphore),
            self.update_all_assignment(cookies,semaphore),
        ])
        return True

    async def prepare_requests(self, save_num=20):
        '''
        Gets all the incidents from service now

        Parameters
        ----------
        save_num : INTEGER, optional
            Number of items before saving to database. The default is 20.

        Returns
        -------
        None.

        '''
        cookies = await self._get_cookies_async()
        print("DOWNLOAD FULL BS_SC EWM_NAR_IBM / BS_SC WH_IBM ----")
        url = 'https://nestle.service-now.com/incident_list.do?sysparm_query=assignment_group%3D6ff9c022db8cab00856c8a3a48961975%5EORassignment_group%3D207b3c74db5c089468a4f7131d9619d0%5EORassignment_group%3Da7f9c022db8cab00856c8a3a48961999%5EORassignment_group%3De10ac422db8cab00856c8a3a4896199b%5EORassignment_group%3Da461483edb55a780856c8a3a48961932%5EORassignment_group%3De7f9c022db8cab00856c8a3a489619a7%5EORassignment_group%3D73f9c022db8cab00856c8a3a489619b3%5EORassignment_group%3De7f9c022db8cab00856c8a3a48961986%5EORassignment_group%3Ddfa37036db8b7b405848ff261d9619fe%5EORassignment_group%3Dc3331d32db44e7005ac9d18c68961946%5EORassignment_group%3Dcf62a6fadb2833c8ceccff261d9619bf%5EORassignment_group%3D5168906fdb29d0148aa20ae5f39619e7%5EORassignment_group%3D22696b2adbec1094b7a6d844ca9619a8&sysparm_first_row=1&sysparm_view=&JSONv2'
        content = await self._get_url(url,cookies)
        j = json.loads(content)
        insertList = []
        total = len(j["records"])
        for idx, incident in enumerate(j["records"]):
            query = {"number": incident["number"]}
            incident["description_pending"] = True
            document = self.db_col.find_one(query)
            if document != None:
                del incident["work_notes"]
                newValues = { "$set": incident }
                self.db_col.update_one(query, newValues)
            else:
                insertList.append(incident)
            insertList = self._partial_save(insertList,idx, save_num, total)
        print("UPSERT BS_SC EWM_NAR_IBM / BS_SC WH_IBM ---- " + str(len(j["records"])) + " records")
        
    def _partial_save(self,insertList,idx, save_num, total):
        '''
        Saves the insert list to the database

        Parameters
        ----------
        insertList : ARRAY
            List of documents to be inserted.
        idx : INTEGER
            Current index on the loop (Number of processed items).
        save_num : INTEGER
            Number of documentsto be processed before saving the database.
        total : INTEGER
            Total documentsto be saved on the databases.

        Returns
        -------
        insertList : ARRAY
            Updated document list to be inserted.

        '''
        idx_max = total - 1
        if idx%save_num == 0 or idx_max == idx:
            print("SAVING...")
            if len(insertList) != 0:
                self.db_col.insert_many(insertList)    
                insertList = []
        return insertList        

    async def new_worknote(self,number,content,uuid):
        '''
        Generates a new worknote on service now, the incident number must
        exist on the collection otherwise exception is raised.

        Parameters
        ----------
        number : STRING
            Incident number.
        content : STRING
            Worknote content.
        uuid : STRING
            Prediction UUID.
        Raises
        ------
        Exception
            This is raised if number not present in collection.

        Returns
        -------
        INTEGER
            HTTP Code from service now.

        '''
        query = {"number": number}
        document = self.db_col.find_one(query,{'sys_id': 1})
        if document == None:
            raise Exception('No incident found on EWM Collection')
        url = "https://nestle.service-now.com/incident.do?JSONv2&sysparm_action=update&sysparm_sys_id=" + str(document["sys_id"])
        json={'work_notes': str(content)}
        cookies = await self._get_cookies_async()
        status_code = self._post_url_json(url,cookies,json)
        if status_code == 200:
            self._set_predictions_set(number,uuid)
        return status_code

    def _set_predictions_set(self,number,uuid):
        incident = self.db_col.find_one({'number': number},{'_id': 1,'predictions': 1})
        mongo_id = incident['_id']
        for prediction in incident['predictions']:
            if prediction['uuid'] == uuid:
                prediction['feedback_sent'] = True
        newValues = { "$set": { 'predictions': incident['predictions'] } }
        self.db_col.update_one({'_id': mongo_id}, newValues)

    def _set_cookies_selenium(self,session,browser):
        browser.get("https://nestle.service-now.com/api")
        for c in session.cookies:
            browser.add_cookie({"name":c.name,"value":c.value})
        return browser

    #CATEGORY>
    def _get_category_query(self,number=None):
        query = { "category_incident": None }
        if number != None:
            query = { "number": number }
        fields = { 
            "_id": 1,
            "number": 1,
            "category_incident": 1
        }
        return query,fields        

    async def _initialize_category(self,number=None,cookies=None):
        if cookies == None:
            cookies = await self._get_cookies_async()
        query = self._get_category_query(number)
        return cookies,query        

    def _save_category(self,category,mongo_id):
        newValues = { "$set": { 'category_incident': category } }
        res = self.db_col.update_one({"_id": mongo_id}, newValues)
        return res

    async def update_all_category(self,cookies=None,semaphore=None):
        cookies,query = await self._initialize_category(cookies=cookies)
        if semaphore == None:
            semaphore = asyncio.Semaphore(value=self.max_connections)        
        documents = self.db_col.find(query[0],query[1])  
        tasks = []
        for document in documents:
            tasks.append(self.update_category(document["number"],cookies,semaphore))
        if len(tasks) != 0:
            await asyncio.wait(tasks)            
        print("Category -- Update finished")

    async def update_category(self,number,cookies,semaphore=None):
        #get semaphore
        await self.semaphore_activate(True,semaphore)        
        cookies,query = await self._initialize_category(number,cookies)
        document = self.db_col.find_one(query[0],query[1])
        if document == None:
            await self.semaphore_activate(False,semaphore)
            raise Exception("Ticket number not found")
        category = await self._get_category(number,cookies)
        if category == False:
            print("Category error: " + str(number))
            await self.semaphore_activate(False,semaphore)
            return
        self._save_category(category,document["_id"])
        print("Category saved: " + str(number))
        #release semafore
        await self.semaphore_activate(False,semaphore)        


    async def _get_category(self,number,cookies):
        #navigate to incident
        incident_url = "https://nestle.service-now.com/incident.do?sysparm_query=number=" + number
        content = await self._get_url(incident_url,cookies)
        if content == "":
            return False
        #Parse category
        tree = html.fromstring(content)
        xpath_item = tree.xpath('//select[@name="incident.category"]/option[@selected="SELECTED"]')
        if len(xpath_item) == 0:
            xpath_item = tree.xpath('//select[@name="sys_readonly.incident.category"]/option[@selected="SELECTED"]')
            if len(xpath_item) == 0:
                return ""
        category = xpath_item[0].text
        return category           
    #ASSIGNMENT GROUP>
    def _get_assignment_query(self,number=None):
        query = { "$or": [
            { "assignment_group_text": None },
            { "assignment_group_text": "" }
            ]}
        if number != None:
            query = { "number": number }
        fields = { 
            "_id": 1,
            "number": 1,
            "assignment_group_text": 1
        }
        return query,fields
        
    async def _initialize_assignment(self,number=None,cookies=None):
        if cookies == None:
            cookies = await self._get_cookies_async()
        query = self._get_assignment_query(number)
        return cookies,query   

    def _save_assignment(self,assignment_group_text,mongo_id):
        newValues = { "$set": { 'assignment_group_text': assignment_group_text } }
        res = self.db_col.update_one({"_id": mongo_id}, newValues)
        return res  

    async def update_all_assignment(self,cookies=None,semaphore=None):
        cookies,query = await self._initialize_assignment(cookies=cookies)
        if semaphore == None:
            semaphore = asyncio.Semaphore(value=self.max_connections)
        documents = self.db_col.find(query[0],query[1])
        tasks = []
        for document in documents:
                tasks.append(self.update_assignment(document["number"],cookies,semaphore))
        if len(tasks) != 0:
            await asyncio.wait(tasks)
        print("Assignment Group -- Update finished")      
    
    async def semaphore_activate(self,get=True,semaphore=None):
        if semaphore == None:
            return
        if get == True:
            await semaphore.acquire() 
        else:
            semaphore.release()

    async def update_assignment(self,number,cookies,semaphore=None):
        #get semaphore
        await self.semaphore_activate(True,semaphore)
        cookies,query = await self._initialize_assignment(number,cookies)
        document = self.db_col.find_one(query[0],query[1])
        if document == None:
            await self.semaphore_activate(False,semaphore)
            raise Exception("Ticket number not found")
        assignment = await self._get_assignment(document["number"],cookies)
        self._save_assignment(assignment,document["_id"])        
        print("Assignment Group saved: " + str(document["number"]))
        #release semafore
        await self.semaphore_activate(False,semaphore)

    async def _get_url(self,url,cookies):
        content = ""
        try:
            session = httpx.AsyncClient()
            r = await session.get(url, cookies=cookies)
            content = r.text
        except Exception as e:
            print(e)
            return ""
        finally:
            await session.aclose()
        return content
    async def _post_url_json(self,url,cookies,json):
        try:
            session = await httpx.AsyncClient()
            response = await session.post(url, cookies=cookies,json=json)
            await session.close()
            return response.status
        except Exception as e:
            print(e)
            await session.close()
            return 500
    async def _get_assignment(self,number,cookies):  
        #navigate to incident
        incident_url = "https://nestle.service-now.com/incident.do?sysparm_query=number=" + number
        content = await self._get_url(incident_url,cookies)
        try:
            #Parse WN
            tree = html.fromstring(content)
            xpath_item = tree.xpath('//input[@name="incident.assignment_group_label"]')
            if len(xpath_item) == 0:
                xpath_item = tree.xpath('//input[@name="sys_display.incident.assignment_group"]')
                if len(xpath_item) == 0:
                    return ""
            return xpath_item[0].get("value")
        except Exception as e:
            print("Error assignment: " + str(e))
            return ""

    #WORK NOTES>    
    def _get_work_notes_query(self,number=None):
        query = { "work_notes": "" }
        if number != None:
            query = { "number": number }
        fields = { 
            "_id": 1,
            "number": 1,
            "work_notes": 1
        }
        return query,fields
    
    async def _initialize_work_notes(self,number=None,cookies=None):
        if cookies == None:
            cookies = await self._get_cookies_async()
        query = self._get_work_notes_query(number)
        return cookies,query

    def _save_work_notes(self,work_notes,mongo_id):
        newValues = { "$set": { 'work_notes': work_notes } }
        res = self.db_col.update_one({"_id": mongo_id}, newValues)
        return res

    async def update_all_work_notes(self,cookies=None,semaphore=None):
        if semaphore == None:
            semaphore = asyncio.Semaphore(value=self.max_connections)        
        cookies,query = await self._initialize_work_notes(cookies=cookies)
        documents = self.db_col.find(query[0],query[1])
        tasks = []
        for document in documents:
                tasks.append(self.update_work_notes(document["number"],cookies,semaphore))
        if len(tasks) != 0:
            await asyncio.wait(tasks)
        print("Work notes -- Update finished")

 
    async def update_work_notes(self,number,cookies,semaphore=None):
        #get semaphore
        await self.semaphore_activate(True,semaphore)        
        cookies,query = await self._initialize_work_notes(number,cookies)
        document = self.db_col.find_one(query[0],query[1])
        if document == None:
            await self.semaphore_activate(False,semaphore)
            raise Exception("Ticket number not found")
        work_notes = await self._get_work_notes(number,cookies)
        if work_notes == False:
            print("Error getting work note")
            await self.semaphore_activate(False,semaphore)
            return
        self._save_work_notes(work_notes,document["_id"])
        print("Work Notes saved: " + str(number))
        #release semafore
        await self.semaphore_activate(False,semaphore)        

    async def _get_work_notes(self,number,cookies):        
        work_notes = []
        #navigate to incident
        incident_url = "https://nestle.service-now.com/incident.do?sysparm_query=number=" + number
        content = await self._get_url(incident_url,cookies)   
        if content == "":
            return False
        #Parse WN
        tree = html.fromstring(content)
        xpath_tree = tree.xpath('//*[@id="sn_form_inline_stream_entries"]/ul/li/div/div/span')
        xpath_tree_time = tree.xpath('//*[@id="sn_form_inline_stream_entries"]/ul/li/div/div/span/parent::div/parent::div/parent::li//div[contains(@class,\'date-timeago\')]')
        xpath_user_1 = tree.xpath('//*[@id="sn_form_inline_stream_entries"]/ul/li/div/div/span/parent::div/parent::div/parent::li//span[contains(@class,\'sn-presence-lite\')]')
        xpath_user_2 = tree.xpath('//*[@id="sn_form_inline_stream_entries"]/ul/li/div/div/span/parent::div/parent::div/parent::li//span[contains(@class,\'sn-card-component-createdby\')]')
        xpath_type = tree.xpath('//*[@id="sn_form_inline_stream_entries"]/ul/li/div/div/span/parent::div/parent::div/parent::li//span[contains(@class,"sn-card-component-time")]//span[1]')
        for index,item in enumerate(xpath_tree):
            note_type = xpath_type[index].text
            if note_type != "Work notes":
                continue
            try:
                time = xpath_tree_time[index].get("timeago")
                presence_id = xpath_user_1[index].get("data-presence-id")
                uname =  xpath_user_2[index].text
                username = re.search(r'\((.*?)@', uname, re.IGNORECASE)
                if username:
                    username = username.group(1)
                author = re.search(r'(.*?)\(',uname,re.IGNORECASE)
                if author:
                    author = author.group(1)[:-1]
                new_note = { 
                    'time': time,
                    'note': item.text, 
                    'presence_id':  presence_id,
                    "username": username,
                    "author": author
                }
                work_notes.append(new_note)
            except Exception as e:
                print(number + "Error extracting Work Note number " + str(index) + str(e))
                continue
        return work_notes

    #>update pending
    async def _initialize_pending(self,number=None,cookies=None):
        if cookies == None:
            cookies = await self._get_cookies_async()
        query = self._get_pending_query(number)
        return cookies,query    

    def _get_pending_query(self,number=None):
        query = { '$or': [{"close_code": ""},{"close_code": None}]}
        if number != None:
            query = { "number": number }
        fields = { 
            "_id": 1,
            "number": 1,
            "close_notes": 1
        }
        return query,fields    

    async def _get_update(self,number,cookies,mongo_id, semaphore):
        #get semaphore
        await self.semaphore_activate(True,semaphore)                
        #navigate to incident
        incident_url = "https://nestle.service-now.com/incident.do?JSONv2&sysparm_query=number=" + number
        content = await self._get_url(incident_url,cookies)  
        if content == "":
            await self.semaphore_activate(False,semaphore) 
            return
        j = json.loads(content)
        incident = j["records"][0]
        del incident["work_notes"]
        newValues = { "$set": incident }
        self.db_col.update_one({"_id": mongo_id}, newValues)
        #release semafore
        await self.semaphore_activate(False,semaphore) 
        await self.update_work_notes(number,cookies,semaphore)

    async def update_pending(self,cookies=None,semaphore=None):
        if semaphore == None:
            semaphore = asyncio.Semaphore(value=self.max_connections)
        cookies,query = await self._initialize_pending(cookies=cookies)
        documents = self.db_col.find(query[0],query[1])
        tasks = []
        for document in documents:
            tasks.append(self._get_update(document["number"],cookies,document["_id"],semaphore))
        if len(tasks) != 0:
            await asyncio.wait(tasks)            
        print("Pending -- Update finished")        


class check_custom_attribute(object):
  '''Waits based on aria-valuenow="100" 
  '''
  def __init__(self, locator, attributeName,attributeValue):
    self.locator = locator
    self.attributeName = attributeName
    self.attributeValue = attributeValue

  def __call__(self, driver):
    element = driver.find_element(*self.locator)   # Finding the referenced element
    if self.attributeValue == element.get_attribute(self.attributeName):
        return element
    else:
        return False

#THIS SECTION IS USED ONLY FOR TESTING
async def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    mongo_ip = "mongodb://127.0.0.1:27017/service_now"
    worker = IncidentSearch(mongo_ip=mongo_ip,
                            user_id="jorge.bustillos@nestle.com",
                            user_pass="",
                            show_browser=True,
                            max_login=5)
    #TESTS ASYNC:
    #await worker.prepare_requests()
    await worker.new_requests()


if __name__ == "__main__":
    asyncio.run(main())

