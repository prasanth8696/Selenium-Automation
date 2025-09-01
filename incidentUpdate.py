import os
import logging
import pandas as pd
from datetime import datetime
from pandas import DataFrame,Series
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import WebDriverException
from selenium_handler import (
    getShadowRoot,
    waitForElement,
    selectAriaDropDown,
    snowInitialProcessForTasks,
    getNextRecordBtnTag,
    getTabSectionSpanTag
)
from handler import settings
from functions import  getVulnerblityDetailsForMachine
from errorDetails import errorsInfo
from csv_handler import convert_csv_to_xlsx



#enable logging
logger: logging.getLogger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
if not os.path.exists(settings["Log_path"]):
    os.mkdir(settings["Log_path"])

fullLogName: str = os.path.join(settings["Log_path"],eval(settings["Selenium_log_name"]))
fh = logging.FileHandler(fullLogName)
fh.setLevel(logging.DEBUG)


# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(fh)

if settings['Console_logs'] :
    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def updateSingleIncidentInSnow(driver: webdriver, qulaysReport: DataFrame | Series, cmdbReport: DataFrame | Series ) -> dict :

    try : 
        #initiate snow initial porcess for sc tasks
        logger.info("Snow initial process for current task - Started")
        response: bool = snowInitialProcessForTasks(driver)

        if not response:
            logger.error("Snow initial process is failed, program exiting")
            raise WebDriverException
        
        logger.info("Snow initial process for catalog tasks - Done")

        #find the incident number ID
        logger.info("Extracting incident number from service now form UI - Started")
        incidentNumberTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_readonly\\.incident\\.number")
        if not incidentNumberTag :
            logger.critical("Unable to find the incident number tag from the incident page")
            raise WebDriverException

        incidentNumber: str = incidentNumberTag.get_attribute("value")
        logger.debug(f"currently working on  task number: {incidentNumber}")
        logger.info("Extracting incident number from service now form UI - Done")

        #find the affected equipment number
        logger.info("Extracting affected Equipment number from service now form UI - Started")
        affectedEquipmentTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.incident\\.u_pid_or_affected_equipment")
        if not affectedEquipmentTag :
            logger.critical("Unable to find the affected equipment tag  from the incident page")
            raise WebDriverException

        affectedEquipment: str = affectedEquipmentTag.get_attribute("value")
        logger.debug(f"affected Equipment for current incident: {affectedEquipment}")
        logger.info("Extracting affected Equipment number from service now form UI - Started")

        #check affected equipment is present or not
        #If not skip the incident ticket for update
        if not affectedEquipment :
            return {"status": False, "errorDetails": errorsInfo["MACHINE_NOT_FOUND"],"data": {"incidentNumber" : incidentNumber}}

        

        #update workNotes
        #here we have three tabs 
        #find which tabs is currently selected
        #here we need "Comments and Work Notes" tab for update the worknotes
        logger.info("working on the worknotes tab from service now form UI - Started")
        workNotesTab = getTabSectionSpanTag(driver,"Comments and Work Notes")
        #if worknotes tab is none then raise an Exception
        if not workNotesTab :
            logger.debug("Unable to find Comments and worknotes tab ,raising exception")
            raise WebDriverException
        

        #check it is selected or not using aria-selected attribute
        #while pharsing from html it will come as string so compare with string boolean
        #if it is not selected then click the tab
        isWorkNotesSelected: str = workNotesTab.get_attribute("aria-selected")
        if isWorkNotesSelected == "false" :
            logger.debug("Comments and Work Notes Section not selected,selecting the section")
            workNotesTab.click()
            logger.debug("Comments and Work Notes Section selected")
        else:
            logger.debug("Comments and Work Notes Section selected")
        
        logger.info("working on the worknotes tab from service now form UI - Done") 

        
        #find worknotes Tag
        logger.info("working on the worknotes tag from service now form UI - Started")
        workNotesTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"textarea#activity-stream-textarea")
        vulnerablityDetails: str = getVulnerblityDetailsForMachine(affectedEquipment,qualysReport,cmdbReport)
        #add vulnerablities details in the worknotes
        #for longer text selenium will inefficient to add the text using send_keys so using javascript method to add
        #if asset count + last detcted more than 50 try with javscript else use selenium default methods
        
        if ( vulnerablityDetails["totalVulnerablities"] > 13 ) :
            logger.debug("attempting javascript method to fill the workotes")
            #driver.execute_script("arguments[0].value = arguments[1]",workNotesTag,nonRemediatedStr)
            driver.execute_script("document.querySelector('#activity-stream-textarea').value = arguments[0]",vulnerablityDetails["vulnerablityDetailsString"])
            time.sleep(1.2)
            #if update values using worknotes , it is updating but while saving it is not got updated in backend
            #updating one space to post entire worknotes
            workNotesTag.send_keys(" ")
            
        else:
            logger.debug("attempting selenium default send_keys method to fill the workotes")
            workNotesTag.send_keys(vulnerablityDetails["vulnerablityDetailsString"])
        
        logger.info("working on the worknotes tag from service now form UI - Done")

        input()

        #find save button Tag
        #save the record using save button
        saveBtnTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"button#sysverb_update_and_stay")

        #send click event
        saveBtnTag.click()
        time.sleep(1)
        logger.info("successfully clicked the save button")
        logger.info("successfully saved the changes for current task")
        return { "status": True, "data": {"incidentNumber" : incidentNumber} }
    


    except WebDriverException as e :
        logger.exception("General webdriver exception raised",e)
        logger.info("skipping to another task")
        return { "status" : False, "errorDetails" : errorsInfo["WEBDRIVER_EXCEPTION"]}
    except Exception as e :
        logger.exception("something went wrong for additional info",e)
        return { "status" : False, "errorDetails" : errorsInfo["WEBDRIVER_EXCEPTION"]}
    

def updateIncidentsInSnow(qulaysReport: DataFrame | Series,cmdbReport: DataFrame | Series):

    logger.info("updateIncidentsInSnow function started")
    
    try :
        logger.info("Initilizing the selenium webdriver - Started")
        driverPath: str = settings["CHROME_DRIVER_PATH"]
        serviceObj: Service = Service(driverPath)

        driver: webdriver.Chrome = webdriver.Chrome(service=serviceObj)
        driver.maximize_window()
        logger.info("Initilizing the selenium webdriver - Done")

        #browse the link
        logger.info("browsing the snow link - Started")
        snowIncidentsLink: str = settings["allIncidentsLink"]
        driver.get(snowIncidentsLink)
        input("once gave your crends press anykey")
        logger.info("browsing the snow link - Done")

        logger.info("Snow initial process for incidents - Started")
        #initiate snow initial porcess for sc tasks
        response: bool = snowInitialProcessForTasks(driver)
        

        if not response:
            logger.error("Snow initial process is failed, program exiting")
            return False
        logger.info("Snow initial process for catalog tasks - Done")


        #get the table details
        logger.info("processing service now table UI - Started")
        tableTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"table#task_table")

        #get the total rows in the table
        logger.debug("getting the total tasks count - Started")
        totalRows: int = int(tableTag.get_attribute("grand_total_rows"))
        if totalRows == 0:
            logger.debug("no current records to update,so closing the browser")
            driver.quit()
            return True
        
        logger.debug(f"total tasks count: {totalRows}")
        logger.info("getting the total tasks count - Done")
        
        #get the first tr tag in the list tr in the tbody
        logger.info("getting first dirst Tr tag and form link - Started")
        firstTrTag: WebElement = tableTag.find_element(By.CSS_SELECTOR,"tbody.list2_body").find_elements(By.TAG_NAME,'tr')[0]
        logger.info("first Tr tag identified successfuly")

        if firstTrTag :
            ankerTag: webdriver = waitForElement(firstTrTag,By.CSS_SELECTOR,"a.formlink")
            logger.info("form anker tag identified successfully")
            if ankerTag :
                logger.debug("clicking the anker tag for getting task form")
                ankerTag.click()

                #once clicked come out of the iframe
                logger.debug('exiting from frame for getting the normal content')
                driver.switch_to.default_content()
                logger.info("getting first dirst Tr tag and form link - Done")
        else :
            logger.critical("unable to find table Tr tag from incident page")
            return False 
        
        logger.info("processing service now table UI - Done")
         

        validatedRowCount: int = 0
        emptyMachineIncidents: list = []
        while True :

            snowValidationDetails: dict = updateSingleIncidentInSnow(driver,qualysReport,cmdbReport)
            
            if snowValidationDetails["status"] :
                pass

            elif not snowValidationDetails["status"] and snowValidationDetails["errorDetails"]["title"] == "MACHINE_NOT_FOUND" :
                emptyMachineIncidents.append(snowValidationDetails["data"]["incidentNumber"])
            
            elif snowValidationDetails["errorDetails"]["title"] == "SNOW_INITIAL_ERROR" :
                logger.debug(f"Snow Valiation Error : {snowValidationDetails['errorDetails']['title']}")
                break 

            else :
                logger.debug(f"Something went wrong : {snowValidationDetails['errorDetails']['title']}")
                break


            
            
            #find next arrow click button to get the next record
            logger.info("Extracting next click record anker button - Started")
            nextRecordBtnTag: WebElement = getNextRecordBtnTag(driver)
            logger.info("next record button extracted successfully")
            nextRecordBtnTagTitle: str = nextRecordBtnTag.get_attribute("title")
            logger.debug(f"next record button title: {nextRecordBtnTagTitle}")
            isNextRecordBtnTagDisabled: str = nextRecordBtnTag.get_attribute("disabled")
            logger.debug(f"next record button disabled: {isNextRecordBtnTagDisabled}")
            logger.info("Extracting next click record anker button - Done")

            if nextRecordBtnTagTitle == "Bottom of list displayed" or isNextRecordBtnTagDisabled == "true" :
                
                validatedRowCount += 1  
                logger.info(f"{snowValidationDetails['data']['incidentNumber']} validated sucessfully - {validatedRowCount}/{totalRows}")
                break

            else:
                #click next button record
                nextRecordBtnTag.click()
                logger.debug("clicking the next record button to get the next record")
                driver.switch_to.default_content()
                logger.debug("exiting the frame for getting the normal content")
            
            validatedRowCount += 1
            logger.info(f"{snowValidationDetails['data']['incidentNumber']} validated sucessfully - {validatedRowCount}/{totalRows}")

        return emptyMachineIncidents
            

    except WebDriverException as e :
        logger.exception("General webdriver exception raised")
        return False
    except Exception as e :
        logger.exception("something went wrong for additional info",e)
        return False
    finally:
        driver.quit()


if __name__ == "__main__" :

    #load Qualys report
    QUALYS_REPORT_PATH: str = eval(settings["QUALYS_REPORT_PATH"])
    if not os.path.exists(QUALYS_REPORT_PATH) :      
        logger.debug(f"{QUALYS_REPORT_PATH}  Qualys report path not exists")
        logger.info(f"converting  Qulays Raw data  to normal report from {settings['QUALYS_RAW_REPORT_PATH']}")  
        res : dict = convert_csv_to_xlsx(settings["QUALYS_RAW_REPORT_PATH"])
    
    qualysReport: DataFrame | Series = pd.read_excel(QUALYS_REPORT_PATH)

    #load CMDB details
    CMDB_FILE_PATH: str = settings["CMDB_FILE_PATH"]
    if not os.path.exists(CMDB_FILE_PATH) :
        logger.critical(f"{CMDB_FILE_PATH} cmdb report not exists")
        exit(-1)
    cmdbReport: DataFrame | Series = pd.read_excel(CMDB_FILE_PATH)

    response: bool | list = updateIncidentsInSnow(qualysReport,cmdbReport)

    if not response :
        logger.debug(f"Incident update failed : {response}")
        exit(-1)
    logger.info(f"follwing incidents not having the affected equipemnet details: {','.join(response)}")
    print(response)
    

