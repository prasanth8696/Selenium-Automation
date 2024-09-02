import time
import getpass
from handler import settings
import pandas as pd
from pandas import DataFrame,Series
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
# from selenium.common.exceptions import ElementNotVisibleException, ElementNotInteractableException
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException
from selenium_handler import getShadowRoot,waitForElement,selectAriaDropDown,chooseSelectDropDown,findAllVulnerablityTags,findAssetCountElement



def getCurrentUserDetails(currentUserID: str ) -> dict:

    currentUserDetails: dict = {}
    for assignedToID,assignedToDetails in settings["Assigned_to"].items() :
        if currentUserID == assignedToDetails["User_id"] :
            currentUserDetails["snowID": assignedToID,"userDetails":assignedToDetails]
            break
    return currentUserDetails


def getSnowLinkandUserDetails(currentMode: str)  :
    
    #AvailbleModes => currentUser,open,all
    #required Details snoe link and currentUser Details
    requiredDetails: dict = {}

    currentUser: str = getpass.getuser()
    currentUser = currentUser.split("\\")[-1]

    currentUserDetails: dict = getCurrentUserDetails(currentUser)

    requiredDetails["currentUserDetails"] = currentUserDetails

    if not currentUserDetails:
        print("current user detail is not present in the settings.json")
        return False
    
    if currentMode == "currentUser":
        
        #get the  open task list snow link and add ID at the bottom
        openTaskSnowLink: str = settings["openTasksLink"]
        #for testing you can change give your ID directly here
        requiredDetails["snowLink"] = openTaskSnowLink + currentUserDetails["snowID"]

    elif currentMode == "open":
        requiredDetails["snowLink"] = settings["openTasksLink"]
    elif currentMode == "all" :
        requiredDetails["snowLink"] = settings["allTasksLink"]
    else :
        print("current settings not maching with available modes settings")
        return False 

    return requiredDetails

def getTaskDetails(validatedTaskList: DataFrame | Series,taskNumber: str)-> dict :
    
    #get the task details for respective task number
    taskDataFrame: DataFrame | Series = validatedTaskList[validatedTaskList["Number"] == taskNumber]

    if not taskDataFrame.empty :
        return taskDataFrame.to_dict()
    else :
        return {}
    

#get the current mode
def getCurrentConfigMode():
    #get the current config settings for updating the snow
    currentMode: str = settings["Current_mode"]

    #if current mode is null then take deafult value in the settings
    try:
        if not currentMode:
            defaultMode: str = settings["Deafult_mode"]
  
            #check default mode is null or not
            #if null raise exception 
            if not defaultMode:
                raise ValueError
            #if deafult there then take deafult mode as current mode
            currentMode = defaultMode
        
        return currentMode
    except ValueError as e :
        print("Deafult mode must be configured ")
        return False

    except Exception as e :
        print("something went wrong for additinal info",e)
        return False





def updateTasksInSnow(validatedTaskList: DataFrame | Series):

    
    #get the current mode based on the settings
    currentMode: str = getCurrentConfigMode()

    if not currentMode :
        return False
    
    requiredDetails = getSnowLinkandUserDetails(currentMode)

    if not requiredDetails :
        return False
    
    try :
        driverPath: str = settings["CHROME_DRIVER_PATH"]
        serviceObj: Service = Service(driverPath)

        #initilize the driver
        driver: webdriver.Chrome = webdriver.Chrome(service=serviceObj)
        driver.maximize_window()

        #browse the link
        if not requiredDetails["snowLink"] :
            print("no snow link to browse")
            return False
        
        driver.get(requiredDetails["snowLink"])
        input("once gave your crends press anykey")

        while True :
            #find Shadow Host
            shadowHost1: WebElement = waitForElement(driver,By.TAG_NAME,"macroponent-f51912f4c700201072b211d4d8c26010")
            #Find the shadow root from the shadow host
            shadowRoot: WebElement = getShadowRoot(shadowHost1)
            #find the mainIframe and switch to iframe
            mainIframe: WebElement = shadowRoot.find_element(By.CSS_SELECTOR,"iframe#gsft_main")

            #switch to mainframe
            driver.switch_to.frame(mainIframe)

            #find the tasknumber ID and get the validated details for the respective task number
            taskNumberTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sc_task\\.number")
            taskNumber: str = taskNumberTag.get_attribute("value")

            if taskNumber :
                #need to get the validated details
                taskDetails: dict = getTaskDetails(validatedTaskList,taskNumber)
                if not taskDetails:
                    print("for current task unable to find the validated details, skipping the update")
                    continue
            
            #find all tab1 elemnets
            #get the assignment group Tag
            assigmentGrpTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assignment_group")
            assigmentGrpTagValue: str = assigmentGrpTag.get_attribute("value")

            #if assignment group is not Desktop Configuration Management then change assignmnet group to Desktop Configuration Management
            if assigmentGrpTagValue != "Desktop Configuration Management":
                selectAriaDropDown(assigmentGrpTag,"Desktop Configuration Management")
                
            #get the AssignedTo Tag
            assignedTo: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assigned_to")

            assignedToTagValue: str = assignedTo.get_attribute("value")
            #check if it is null then it is open task, assign the task who running this script
            if not assignedToTagValue :
                selectAriaDropDown(assigmentGrpTag,"Ayyappan Dharmalingam")

            #find worknotes Tag
            workNotesTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"textarea#activity-stream-textarea")
            #add remediation string in the worknotes
            workNotesTag.send_keys(taskDetails["Non-Remediated String"][0])

            #find taskState selection tag
            selectTaskState: WebElement = waitForElement(driver,By.CSS_SELECTOR,"select#sc_task\\.state")
            taskState: Select = Select(selectTaskState)
            taskStateText: str = (taskState.first_selected_option).text
            #if task is open here we have two sceniros
            #if task open and assignTo is not null then it is reopen task
            #if task is open and assignTo is null then it is open task
            if taskStateText == "open" :
                if assignedToTagValue :
                    print("this is reopen task so changing the task state based on actual asset count")
                else :
                    print("this is open task so changing the task state based on actual asset count")
                    #for manual validation once set openTask as true for later validation
                    openTask: bool = True
                    
                if taskDetails["Actual Asset Count"][0] == 0 :
                    print(f"actual asset count is {taskDetails["Actual Asset Count"][0]} so closing the {taskNumber}")
                    #taskState.select_by_value("4") #for now comment this
                else:
                    print(f"actual asset count is {taskDetails["Actual Asset Count"][0]} so changing  the state of {taskNumber} to work In Progress")
                    taskState.select_by_value("2") #work In Progress
            
            #if task state is Work In Progress then check the asset count if it zero close the case
            #if not leave the tag
            if taskStateText == "Work In Progress" :
                if taskDetails["Actual Asset Count"][0] == 0 :
                    print(f"actual asset count is {taskDetails["Actual Asset Count"][0]} so closing the {taskNumber}")
                    #taskState.select_by_value("4") #for now comment this

            
                

            #find all second tab elements
            #currently comments and worknotes selected for that we need to click request variable then only selenium able to see the request variables
            requestvarTab: WebElement = driver.find_elements(By.CSS_SELECTOR,"span[role='tab']")[1]
            #click the request variable Tab section
            requestvarTab.click()

            #find asset count Tag
            assetCountTag: WebElement = findAssetCountElement(driver)
            assetCountTag.send_keys(taskDetails["Actual Asset Count"][0])

            #find rootcause,solution and remediation status tags
            vulnerablityTags = findAllVulnerablityTags()
            #get the vulnerablityDetails in taskDetails it will be in string mode
            #conver to dictionary using eval method
            vulnerablityDetails: str = taskDetails["vulnerablityDetails"][0]

            #check if it is None or not then convert to dict
            if vulnerablityDetails :
                vulnerablityDetails : dict = eval(vulnerablityDetails)
            
            #rootCause Tag
            rootCauseTag: WebElement = vulnerablityTags["rootCauseTag"]
            #get the value of rootCause tag 
            #if already value is there skip the update
            rootCauseTagValue: str = rootCauseTag.get_attribute("value")
            if not rootCauseTagValue :
                rootCauseTag.send_keys(vulnerablityDetails["rootCause"])

            #solution Tag
            solutionTag: WebElement = vulnerablityTags["solutionTag"]
            #get the value of solution tag 
            #if already value is there skip the update
            solutionTagValue: str = solutionTag.get_attribute("value")
            if not solutionTagValue :
                solutionTag.send_keys(vulnerablityDetails["solution"])

            #remediation Tag
            remediationTag: WebElement = vulnerablityTags["remediationTag"]
            #get the value of remediation tag 
            #if already value is there skip the update
            remediationTagValue = remediationTag.get_attribute("value")
            if not remediationTagValue :

                #if current task is open task then update as newTask for manual validation
                if openTask:
                    remediationTag.send_keys("newTask")
                else:
                    remediationTag.send_keys(vulnerablityDetails["fixedDeployed"])

            #find save button Tag
            #save the record using save button
            saveBtnTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"button#sysverb_update_and_stay")

            #send click event
            saveBtnTag.click()

            #wait 2 second for save the record
            time.sleep(2)














    except WebDriverException as e :
        print("General webdriver exception raised")
        return False
    except Exception as e :
        print("something went wrong for additional info",e)
    finally:
        driver.quit()

    
    
    
    
    