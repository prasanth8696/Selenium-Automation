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

def updateSingleTaskInSnow(driver: webdriver,currentUserDetails: dict,validatedTaskList: dict) -> dict :

    try : 
        #initiate snow initial porcess for sc tasks
        logger.info("Snow initial process for current task - Started")
        response: bool = snowInitialProcessForTasks(driver)

        if not response:
            logger.error("Snow initial process is failed, program exiting")
            return False 
        
        logger.info("Snow initial process for catalog tasks - Done")

        #find the tasknumber ID and get the validated details for the respective task number
        # logger.info("Extracting task number from service now form UI - Started")
        # taskNumberTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sc_task\\.number")
        # taskNumber: str = taskNumberTag.get_attribute("value")
        # logger.debug(f"currently working on  task number: {taskNumber}")
        # logger.info("Extracting task number from service now form UI - Done")
        

        # if taskNumber :
        #     #need to get the validated details
        #     taskDetails: dict = validatedTaskList.get(taskNumber,None)
        #     logger.debug(f"taskDetails : {taskDetails}")
        #     if not taskDetails :
        #         logger.warning("for current task unable to find the validated details, skipping the update")   
        #         return { "status" : False, "taskNumber" : taskNumber, "errorDetails" : errorsInfo["TASK_NOT_FOUND"]}



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
        nonRemediatedStr: str = taskDetails["Non-Remediated String"]
        #add remediation string in the worknotes
        #for longer text selenium will inefficient to add the text using send_keys so using javascript method to add
        #if asset count + last detcted more than 50 try with javscript else use selenium default methods
        totalAssetCountInString: int = (taskDetails["Actual Asset Count"] + taskDetails["Last Detected Count(15days)"])
        if (totalAssetCountInString > 50) :
            logger.debug(f"total non remdiated sting machine count {totalAssetCountInString} is more than 50 ")
            logger.debug("attempting javascript method to fill the workotes")
            #driver.execute_script("arguments[0].value = arguments[1]",workNotesTag,nonRemediatedStr)
            driver.execute_script("document.querySelector('#activity-stream-textarea').value = arguments[0]",nonRemediatedStr)
            time.sleep(1)
            #if update values using worknotes , it is updating but while saving it is not got updated in backend
            #updating one space to post entire worknotes
            workNotesTag.send_keys(" ")
            
        else:
            logger.debug(f"total non remediated sting machine count {totalAssetCountInString} is more than or equal to 50 ")
            logger.debug("attempting selenium default send_keys method to fill the workotes")
            workNotesTag.send_keys(nonRemediatedStr)
        
        logger.info("working on the worknotes tag from service now form UI - Done")



        #find save button Tag
        #save the record using save button
        saveBtnTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"button#sysverb_update_and_stay")

        #send click event
        saveBtnTag.click()
        time.sleep(1)
        logger.info("successfully clicked the save button")
        logger.info("successfully saved the changes for current task")
        return True
    
    except WebDriverException as e :
        logger.exception("General webdriver exception raised",e)
        logger.info("skipping to another task")
        return { "status" : False, "errorDetails" : errorsInfo["WEBDRIVER_EXCEPTION"]}
    except Exception as e :
        logger.exception("something went wrong for additional info",e)
        return { "status" : False, "errorDetails" : errorsInfo["WEBDRIVER_EXCEPTION"]}
    

def updateIncidentsInSnow():

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
        tableTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"table#sc_task_table")

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
        
        logger.info("processing service now table UI - Done")
         

        validatedRowCount: int = 0
        while True :

            snowValidationDetails: dict = updateSingleTaskInSnow(driver,currentUserDetails,validatedTaskList) #need to check  => \

            if snowValidationDetails["status"]  :
                completedTaskList.append(snowValidationDetails["taskNumber"])
            
            elif snowValidationDetails["errorDetails"]["title"] == "TASK_NOT_FOUND" :
                completedTaskList.append(snowValidationDetails["taskNumber"])

            elif snowValidationDetails["errorDetails"]["title"] == "SNOW_INITIAL_ERROR" :
                break

            else : 
                pass
            
            
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
                logger.info(f"{snowValidationDetails['taskNumber']} validated sucessfully - {validatedRowCount}/{totalRows}")
                logger.debug("checking the missed tasks now")
 
                nonValidatedTasks: list = getNonValidatedTasks(validatedTaskList,completedTaskList,requiredDetails["currentUserDetails"]["userDetails"])

                if nonValidatedTasks :
                    logger.info(f"updating the nonValidated tasks : {','.join(nonValidatedTasks)}")
                    updateNonValidatedTasksInSnow(driver,nonValidatedTasks,currentUserDetails,{"validatedRowCount": validatedRowCount,"totalRows": totalRows})
                else :
                    logger.info("nonvalidated tasks are empty")
                    logger.info("this is the bottom of the list so breaking the loop")
                break
            else:
                #click next button record
                nextRecordBtnTag.click()
                logger.debug("clicking the next record button to get the next record")
                driver.switch_to.default_content()
                logger.debug("exiting the frame for getting the normal content")
            
            validatedRowCount += 1
            logger.info(f"{snowValidationDetails['taskNumber']} validated sucessfully - {validatedRowCount}/{totalRows}")

        return True
            

    except WebDriverException as e :
        logger.exception("General webdriver exception raised")
        return False
    except Exception as e :
        logger.exception("something went wrong for additional info",e)
        return False
    finally:
        #driver.quit()
        pass

