import os
import json
import time
import getpass
import logging
from datetime import datetime
from errorDetails import errorsInfo
from handler import settings
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
    findAllVulnerablityTags,
    findAssetCountElement,
    getNextRecordBtnTag,
    getTabSectionSpanTag
)

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



def getCurrentUserDetails(currentUserID: str ) -> dict:

    logger.info("getCurrentUserDetails function - Started")
    currentUserDetails: dict = {}
    for assignedToID,assignedToDetails in settings["Assigned_to"].items() :
        if currentUserID == assignedToDetails["User_id"] :

            logger.debug(f"currentUserID is matched with default assignTo(f{assignedToDetails["User_id"]}) details in settings ")
            currentUserDetails = {"snowID": assignedToID,"userDetails":assignedToDetails}
            logger.debug("match found so breakin the loop")
            break
    
    logger.info("getCurrentUserDetails function - Done")
    return currentUserDetails


def getSnowLinkandUserDetails(currentMode: str)  :
    
    logger.info("getSnowLinkandUserDetails function - Started")
    #AvailbleModes => currentUser,open,all
    #required Details snoe link and currentUser Details
    requiredDetails: dict = {}

    #logger.debug("getting currentUserId from who invoke the script")
    # currentUser: str = getpass.getuser()
    #logger.debug(f"script is invoked by {currentUser}")
    # currentUser = currentUser.split("\\")[-1]
    currentUser = "adharmalingam"

    currentUserDetails: dict = getCurrentUserDetails(currentUser)

    requiredDetails["currentUserDetails"] = currentUserDetails

    logger.debug("checking currentUser details is null or not")
    if not currentUserDetails:
        logger.debug("current user is null so details  not present in the settings.json")
        return False
    else:
        logger.debug(f"currentUserDetails: {currentUserDetails}")
    
    if currentMode == "currentUser":
        logger.info("currentUser mode selected")
        
        logger.info("getting snow link for currentuser - Started" )
        #get the  open task list snow link and add ID at the bottom
        logger.debug("getting the snow link froms settings")
        openTaskSnowLink: str = settings["currentUserTasksLink"]
        #for testing you can change give your ID directly here
       
        requiredDetails["snowLink"] = openTaskSnowLink + currentUserDetails["snowID"] + "%26sysparm_first_row%3D1%26sysparm_view%3D"
        logger.debug(f"snow link for current user: {requiredDetails["snowLink"]} ")
        logger.info("getting snow link for currentuser - Done" )

    elif currentMode == "open":

        logger.info("open mode selected")
        logger.info("getting snow link for open tasks - Started" )
        requiredDetails["snowLink"] = settings["openTasksLink"]
        logger.debug(f"snow link for open tasks: {requiredDetails["snowLink"]} ")
        logger.info("getting snow link for open tasks - Done" )
    elif currentMode == "all" :

        logger.info("all mode selected")
        logger.info("getting snow link for all tasks - Started" )
        requiredDetails["snowLink"] = settings["allTasksLink"]
        logger.debug(f"snow link for all tasks: {requiredDetails["snowLink"]} ")
        logger.info("getting snow link for all tasks - Done" )
    else :
        logger.debug("current settings not maching with available modes settings")
        return False 

    logger.info("getSnowLinkandUserDetails function - Done")
    return requiredDetails


#get the Non validated tasks
#if selenium close one ticket, it will skip one ticket in the snow table
def getNonValidatedTasks(validatedTaskList: dict,completedTaskList: list[str],currentUserDetails: dict[str,str]) -> list[dict] :

    currentMode: str = getCurrentConfigMode()

    nonValidatedTasks : dict = {}
    #for currentuser tickets validation mode
    if currentMode == "currentUser" :
        nonValidatedTasks = { taskNumber : taskDetails for taskNumber,taskDetails in validatedTaskList.items() if (taskDetails["Assigned To"] == currentUserDetails["Full_name"] and taskDetails["Number"] not in completedTaskList) }

    #for open tickets validation mode
    elif currentMode == "open" :
        nonValidatedTasks = { taskNumber : taskDetails for taskNumber,taskDetails in validatedTaskList.items() if (taskDetails["task State"].lower() == "open" and taskDetails["Number"] not in completedTaskList)}
   #for all tickets validation mode
    else :
        nonValidatedTasks = validatedTaskList 
        #currentModeTasks = list(set(validatedTaskList.keys()) - set(completedTaskList) )
    
    return nonValidatedTasks


# def getTaskDetails(validatedTaskList: dict,taskNumber: str)-> dict :

#     #get the task details for respective task number
#     taskDetails: dict = validatedTaskList.get(taskNumber,None)

#     return taskDetails is not None
    
    

#get the current mode
def getCurrentConfigMode():

    logger.info("getCurrentConfigMode function - Started")
    #get the current config settings for updating the snow
    currentMode: str = settings["Current_mode"]
    logger.debug(f"selected current mode is {currentMode}")

    #if current mode is null then take deafult value in the settings
    try:
        if not currentMode:
            logger.debug(f"current mode is empty, getting default mode")
            defaultMode: str = settings["Default_mode"]
            logger.debug(f"the default mode is {defaultMode}")
  
            #check default mode is null or not
            #if null raise exception 
            if not defaultMode:
                logger.debug(f"default is empty - {defaultMode},raising valueError")
                raise ValueError
            #if deafult there then take deafult mode as current mode
            logger.info("setting default mode  as current mode")
            currentMode = defaultMode
        
        logger.info("getCurrentConfigMode function - Done")
        return currentMode
    except ValueError as e :
        logger.exception("default mode must be configured")
        return False

    except Exception as e :
        logger.exception("something went wrong for additinal info",e)
        return False


def updateSingleTaskInSnow(driver: webdriver,currentUserDetails: dict,validatedTaskList: dict) -> dict :

    try : 
        #initiate snow initial porcess for sc tasks
        logger.info("Snow initial process for current task - Started")
        response: bool = snowInitialProcessForTasks(driver)

        if not response:
            logger.error("Snow initial process is failed, program exiting")
            return { "status" : False, "taskNumber": "", "errorDetails" : errorsInfo["SNOW_INITIAL_ERROR"]}
        
        logger.info("Snow initial process for catalog tasks - Done")

        #find the tasknumber ID and get the validated details for the respective task number
        logger.info("Extracting task number from service now form UI - Started")
        taskNumberTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sc_task\\.number")
        taskNumber: str = taskNumberTag.get_attribute("value")
        logger.debug(f"currently working on  task number: {taskNumber}")
        logger.info("Extracting task number from service now form UI - Done")
        

        if taskNumber :
            #need to get the validated details
            taskDetails: dict = validatedTaskList.get(taskNumber,None)
            logger.debug(f"taskDetails : {taskDetails}")
            if not taskDetails :
                logger.warning("for current task unable to find the validated details, skipping the update")   
                return { "status" : False, "taskNumber" : taskNumber, "errorDetails" : errorsInfo["TASK_NOT_FOUND"]}


        
        #find all tab1 elements
        #get the assignment group Tag
        logger.info("working on assignment group tag from service now form UI - Started")
        assigmentGrpTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assignment_group")
        assigmentGrpTagValue: str = assigmentGrpTag.get_attribute("value")
        logger.debug(f"assigmentgrp value: {assigmentGrpTagValue}")

        #if assignment group is not Desktop Configuration Management then change assignmnet group to Desktop Configuration Management
        logger.info("checking assignment grp is Default group - Started")
        if assigmentGrpTagValue != settings["Default_assignment_grp"]:
            logger.debug("task assignement grp is not matched with default assignment group,so changing to default grp")
            selectAriaDropDown(driver,assigmentGrpTag,settings["Default_assignment_grp"])
        else:
            logger.debug("assignment grp is matched with default grp")
        logger.info("checking assignment grp is Default group - Done")
        logger.info("working on assignment group tag from service now form UI - Done")


        #get the AssignedTo Tag
        logger.info("working on assignTo tag from service now form UI - Started")
        assignedTo: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assigned_to")

        assignedToTagValue: str = assignedTo.get_attribute("value")
        logger.debug(f"assignTo value: {assignedToTagValue}")
        #check if it is null then it is open task, assign the task who running this script
        if not assignedToTagValue :
            logger.debug(f"assigned to value is empty, assigning current task({taskNumber}) to currentUser{currentUserDetails["userDetails"]["User_id"]}")
            selectAriaDropDown(driver,assignedTo,currentUserDetails["userDetails"]["User_id"])
        else:
            logger.debug("assignTo is not empty")

        logger.info("working on assignTo tag from service now form UI - Done")
        
        #find taskState selection tag
        logger.info("working on taskState tag from service now form UI - Started")
        selectTaskState: WebElement = waitForElement(driver,By.CSS_SELECTOR,"select#sc_task\\.state")
        taskState: Select = Select(selectTaskState)
        taskStateText: str = (taskState.first_selected_option).text
        logger.debug(f"currently selected option: {taskStateText} ")

        #get the actual asset count for validation
        # index 13 is Actual Asset Count in our DataFrame
        actualAssetCount: int = taskDetails["Actual Asset Count"]

        #if task is open here we have two sceniros
        #if task open and assignTo is not null then it is reopen task
        #if task is open and assignTo is null then it is open task
        #initilize the openTask as False for laster validation
        openTask: bool = False
        if taskStateText == "Open" :
            logger.debug("checking open ticket")
            if assignedToTagValue :
                logger.debug("this is reopen task so changing the task state based on actual asset count")
            else :
                logger.debug("this is open task so changing the task state based on actual asset count")
                #for manual validation once set openTask as true for later validation
                openTask = True

            if actualAssetCount == 0 :
                logger.debug(f"actual asset count is {actualAssetCount} so closing the {taskNumber}")
                taskState.select_by_value("3")
            else:
                logger.debug(f"actual asset count is {actualAssetCount} so changing  the state of {taskNumber} to work In Progress")
                taskState.select_by_value("2") #work In Progress
        
        #if task state is Work In Progress then check the asset count if it zero close the case
        #if asset count not zero then dont the chane the state
        if taskStateText == "Work in Progress" :
            logger.debug("checking Work In Progress ticket")
            if actualAssetCount == 0 :
                logger.debug(f"actual asset count is {actualAssetCount} so closing the {taskNumber}")
                taskState.select_by_value("3") 

        logger.info("working on taskState tag from service now form UI - Done")


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


        #find which tabs is currently selected
        #find request Variable section tab
        logger.info("working on the request variable tab from service now form UI - Started")
        requestVariableTab = getTabSectionSpanTag(driver,"Request Variables")

        #if requestVariableTab is none then raise an Exception
        if not requestVariableTab :
            logger.debug("Unable to find Request Variables tab ,raising exception")
            raise WebDriverException
        
        
        #check it is selected or not using aria-selected attribute
        #while pharsing from html it will come as string so compare with "true" or "false" string
        #if it is not selected then click the tab
        isRequestVariableSelected: str = requestVariableTab.get_attribute("aria-selected")
        if isRequestVariableSelected == "false" :
            logger.debug("request variable tab is not selected,selecting the section")
            requestVariableTab.click()
            logger.debug("request variables section selected")
        
        logger.info("working on the request variable tab from service now form UI - Done")

        #find asset count Tag
        logger.info("working on asset count tag from service now form UI - Started")
        assetCountTag: WebElement = findAssetCountElement(driver)
        assetCountTag.clear()
        assetCountTag.send_keys(actualAssetCount)
        logger.debug(f"added actual asset count: {actualAssetCount} in asset count tag")
        logger.info("working on asset count tag from service now form UI - Done")


        logger.info("working on vulnerablity tags from service now form UI - Started")
        #find rootcause,solution and remediation status tags
        vulnerablityTags = findAllVulnerablityTags(driver)
        logger.info("extracted successfully vulnerbality tags")
        #get the vulnerablityDetails in taskDetails 
        vulnerablityDetails: dict = taskDetails["vulnerablityDetails"]
        
        #rootCause Tag
        rootCauseTag: WebElement = vulnerablityTags["rootCauseTag"]
        #get the value of rootCause tag 
        #if already value is there skip the update
        rootCauseTagValue: str = rootCauseTag.get_attribute("value")
        if not rootCauseTagValue :
            logger.debug(f"rootcause tag is empty adding rootcause as {vulnerablityDetails["rootCause"]}")
            rootCauseTag.send_keys(vulnerablityDetails["rootCause"])

        #solution Tag
        solutionTag: WebElement = vulnerablityTags["solutionTag"]
        #get the value of solution tag 
        #if already value is there skip the update
        solutionTagValue: str = solutionTag.get_attribute("value")
        if not solutionTagValue :
            logger.debug(f"solution tag is empty adding solution as {vulnerablityDetails["solution"]}")
            solutionTag.send_keys(vulnerablityDetails["solution"])

        #remediation Tag
        remediationTag: WebElement = vulnerablityTags["remediationTag"]
        #get the value of remediation tag 
        #if already value is there skip the update
        remediationTagValue = remediationTag.get_attribute("value")
        if not remediationTagValue :
            
            logger.debug(f"remediationStatus tag is empty")
            #if current task is open task then update as newTask for manual validation
            if openTask:
                logger.debug("this is open task,adding value as newTask")
                remediationTag.send_keys("newTask")
            else:
                logger.debug(f"Adding value as {vulnerablityDetails["fixedDeployed"]}")
                remediationTag.send_keys(vulnerablityDetails["fixedDeployed"])

            logger.info("working on vulnerablity tags from service now form UI - Done")

        #find save button Tag
        #save the record using save button
        saveBtnTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"button#sysverb_update_and_stay")

        #send click event
        saveBtnTag.click()
        time.sleep(1)
        logger.info("successfully clicked the save button")
        logger.info("successfully saved the changes for current task")
        return { "status" : True ,"taskNumber" : taskNumber }
    
    except WebDriverException as e :
        logger.exception("General webdriver exception raised",e)
        logger.info("skipping to another task")
        return { "status" : False, "errorDetails" : errorsInfo["WEBDRIVER_EXCEPTION"]}
    except Exception as e :
        logger.exception("something went wrong for additional info",e)
        return { "status" : False, "errorDetails" : errorsInfo["WEBDRIVER_EXCEPTION"]}
    

def updateNonValidatedTasksInSnow(driver: webdriver,nonValidatedTaskList: list[dict],currentUserDetails: dict,validationDetails: dict) -> None:

    print(nonValidatedTaskList)
    for nonValidatedTaskDetails in nonValidatedTaskList.values() :
        snowTaskId: str =  nonValidatedTaskDetails['Sys_ID']
        driver.get(f"https://imf.service-now.com/now/nav/ui/classic/params/target/sc_task.do%3Fsys_id%3D{snowTaskId}%26sysparm_stack%3D%26sysparm_view%3D")
        snowValidationDetails = updateSingleTaskInSnow(driver,currentUserDetails,nonValidatedTaskList)

        if snowValidationDetails["errorDetails"]["title"] == "SNOW_INITIAL_ERROR" or snowValidationDetails["errorDetails"]["title"] == "WEBDRIVER_EXCEPTION" :
            continue
        validationDetails['validatedRowCount'] += 1
        logger.info(f"{snowValidationDetails['taskNumber']} validated sucessfully - {validationDetails['validatedRowCount']}/{validationDetails['totalRows']}")


def updateTasksInSnow(validatedTaskList: dict):

    completedTaskList: list = []
    logger.info("updateTasksInSnow function started")
    #get the current mode based on the settings

    currentMode: str = getCurrentConfigMode()

    if not currentMode :
        logger.error("current mode is empty,exiting the function")
        return False
    
    #sample => requiredDetails = {"snowLink": "",currentUserDetails: {  "snowID" : "","userDetails" : {"Full_name": "","User_id": ""}}
    requiredDetails = getSnowLinkandUserDetails(currentMode)

    if not requiredDetails :
        logger.error("required user and snow details is empty,exiting the function")
        return False
    
    try :
        logger.info("Initilizing the selenium webdriver - Started")
        driverPath: str = settings["CHROME_DRIVER_PATH"]
        serviceObj: Service = Service(driverPath)

        driver: webdriver.Chrome = webdriver.Chrome(service=serviceObj)
        driver.maximize_window()
        logger.info("Initilizing the selenium webdriver - Done")

        #browse the link
        logger.info("browsing the snow link - Started")
        if not requiredDetails["snowLink"] :
            logger.error("no snow link to browse")
            return False
        
        #get the currentUserDetails
        currentUserDetails: dict = requiredDetails["currentUserDetails"]
        driver.get(requiredDetails["snowLink"])
        input("once gave your crends press anykey")
        logger.info("browsing the snow link - Done")

        logger.info("Snow initial process for catalog tasks - Started")
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
        
        logger.debug(f"total taskss count: {totalRows}")
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




if __name__ == "__main__":

    logger.info("user invoked this script as main script")
    validatedtaskListPath: str = "./reports/validatedTaskList.json"
    logger.debug("checking json report file present in the reports directory")
    if os.path.exists(validatedtaskListPath) :
        logger.info("json file found,parsing the json file - Started")
        with open(validatedtaskListPath, "r") as file :
            validatedTaskList: dict = json.load(file)
        
        logger.info("parsing the json file - Done")
        logger.info("invoking updateTasksInSnow function to update the tasks in service now - Started")
        response: bool = updateTasksInSnow(validatedTaskList)

        if not response :
            logger.error("ticket update failed,program exiting")
        else:
            logger.info("ticket pdate successfully completed")
    else:
        logger.error("Report file not found,program exiting")
        exit(-1)







    
    
    
    
    