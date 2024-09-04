import os
import json
import time
import getpass
from handler import settings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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



def getCurrentUserDetails(currentUserID: str ) -> dict:

    currentUserDetails: dict = {}
    for assignedToID,assignedToDetails in settings["Assigned_to"].items() :
        if currentUserID == assignedToDetails["User_id"] :
            currentUserDetails = {"snowID": assignedToID,"userDetails":assignedToDetails}
            break
    return currentUserDetails


def getSnowLinkandUserDetails(currentMode: str)  :
    
    #AvailbleModes => currentUser,open,all
    #required Details snoe link and currentUser Details
    requiredDetails: dict = {}

    # currentUser: str = getpass.getuser()
    # currentUser = currentUser.split("\\")[-1]
    currentUser = "knatesan"

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

# def getTaskDetails(validatedTaskList: dict,taskNumber: str)-> dict :

#     #get the task details for respective task number
#     taskDetails: dict = validatedTaskList.get(taskNumber,None)

#     return taskDetails is not None
    


    

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





def updateTasksInSnow(validatedTaskList: dict):

    
    #get the current mode based on the settings
    currentMode: str = getCurrentConfigMode()

    if not currentMode :
        return False
    
    #sample => requiredDetails = {"snowLink": "",currentUserDetails: {"Full_name": "","User_id": ""}}
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
        
        #get the currentUserDetails
        currentUserDetails: dict = requiredDetails["currentUserDetails"]
        print(currentUserDetails)
        driver.get(requiredDetails["snowLink"])
        input("once gave your crends press anykey")

        # #initiate snow initial porcess for sc tasks
        # response: bool = snowInitialProcessForTasks(driver)

        # if not response:
        #     return False

        #wait for Shadow Host
        shadowHost: WebElement = waitForElement(driver,By.TAG_NAME,"macroponent-f51912f4c700201072b211d4d8c26010")
        #Find the shadow root from the shadow host
        shadowRoot: WebElement = getShadowRoot(driver,shadowHost)
        #find the mainIframe and switch to iframe
        mainIframe: WebElement = shadowRoot.find_element(By.CSS_SELECTOR,"iframe#gsft_main")

        #switch to mainframe
        driver.switch_to.frame(mainIframe)
        
        #get the table details
        tableTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"table#sc_task_table")

        #get the total rows in the table
        totalRows: int = int(tableTag.get_attribute("grand_total_rows"))
        if totalRows == 0:
            print("no current records to update,so closing the browser")
            driver.quit()
            return True
        
        print(f"total task count: {totalRows}")
        
        #get the first tr tag in the list tr in the tbody
        firstTrTag: WebElement = tableTag.find_element(By.CSS_SELECTOR,"tbody.list2_body").find_elements(By.TAG_NAME,'tr')[0]

        if firstTrTag :
            ankerTag: webdriver = waitForElement(firstTrTag,By.CSS_SELECTOR,"a.formlink")
            
            if ankerTag :
                ankerTag.click()
                #once clicked come out of the iframe
                driver.switch_to.default_content()
         

        validatedRowCount: int = 0
        while True :
            #find Shadow Host
            shadowHost1: WebElement = waitForElement(driver,By.TAG_NAME,"macroponent-f51912f4c700201072b211d4d8c26010")
            #Find the shadow root from the shadow host
            shadowRoot1: WebElement = getShadowRoot(driver,shadowHost1)
            #find the mainIframe and switch to iframe
            mainIframe1: WebElement = shadowRoot1.find_element(By.CSS_SELECTOR,"iframe#gsft_main")

            #switch to mainframe
            driver.switch_to.frame(mainIframe1)

            #find the tasknumber ID and get the validated details for the respective task number
            taskNumberTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sc_task\\.number")
            taskNumber: str = taskNumberTag.get_attribute("value")
            
            #find next arrow click button to ge the next record
            
            nextRecordBtnTag: WebElement = getNextRecordBtnTag(driver)
            nextRecordBtnTagTitle: str = nextRecordBtnTag.get_attribute("title")
            isNextRecordBtnTagDisabled: str = nextRecordBtnTag.get_attribute("disabled")
            if taskNumber :
                #need to get the validated details
                taskDetails: dict = validatedTaskList.get(taskNumber,None)
                print(taskDetails)
                if not taskDetails :
                    print("for current task unable to find the validated details, skipping the update")   
                    if nextRecordBtnTagTitle == "Bottom of list displayed" or isNextRecordBtnTagDisabled == "true" :
                        print("this is the last record so break the loop")
                        validatedRowCount += 1
                        break
                    #increase the count
                    validatedRowCount += 1
                    continue
            
            #find all tab1 elemnets
            #get the assignment group Tag
            assigmentGrpTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assignment_group")
            assigmentGrpTagValue: str = assigmentGrpTag.get_attribute("value")

            #if assignment group is not Desktop Configuration Management then change assignmnet group to Desktop Configuration Management
            if assigmentGrpTagValue != settings["Default_assignment_grp"]:
                selectAriaDropDown(assigmentGrpTag,settings["Default_assignment_grp"])
                
            #get the AssignedTo Tag
            assignedTo: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assigned_to")

            assignedToTagValue: str = assignedTo.get_attribute("value")
            #check if it is null then it is open task, assign the task who running this script
            if not assignedToTagValue :
                selectAriaDropDown(assigmentGrpTag,currentUserDetails["Full_name"])

            
            #find taskState selection tag
            selectTaskState: WebElement = waitForElement(driver,By.CSS_SELECTOR,"select#sc_task\\.state")
            taskState: Select = Select(selectTaskState)
            taskStateText: str = (taskState.first_selected_option).text

            #get the actual asset count for validation
            # index 13 is Actual Asset Count in our DataFrame
            actualAssetCount: int = taskDetails["Actual Asset Count"]

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

                if actualAssetCount == 0 :
                    print(f"actual asset count is {actualAssetCount} so closing the {taskNumber}")
                    taskState.select_by_value("4") #for now comment this
                else:
                    print(f"actual asset count is {actualAssetCount} so changing  the state of {taskNumber} to work In Progress")
                    taskState.select_by_value("2") #work In Progress
            
            #if task state is Work In Progress then check the asset count if it zero close the case
            #if asset count not zero then dont the chane the state
            if taskStateText == "Work In Progress" :
                if actualAssetCount == 0 :
                    print(f"actual asset count is {actualAssetCount} so closing the {taskNumber}")
                    taskState.select_by_value("4") #for now comment this


            
                

            #update workNotes
            #here we have three tabs 
            #find which tabs is currently selected
            #here we need "Comments and Work Notes" tab for update the worknotes
            workNotesTab = getTabSectionSpanTag(driver,"Comments and Work Notes")
            #if worknotes tab is none then raise an Exception
            if not workNotesTab :
                print("Unable to find Comments and worknotes tab ,raising exception")
                raise WebDriverException    

            #check it is selected or not using aria-selected attribute
            #while pharsing from html it will come as string so compare with string boolean
            #if it is not selected then click the tab
            isWorkNotesSelected: str = workNotesTab.get_attribute("aria-selected")
            if isWorkNotesSelected == "false" :
                print("Comments and Work Notes Section not selected,selecting the section")
                workNotesTab.click()
                print("Comments and Work Notes Section selected")

            #find worknotes Tag
            workNotesTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"textarea#activity-stream-textarea")
            #add remediation string in the worknotes
            workNotesTag.send_keys(taskDetails["Non-Remediated String"])


            #find which tabs is currently selected
            #find request Variable section tab
            requestVariableTab = getTabSectionSpanTag(driver,"Request Variables")
            print(requestVariableTab.get_attribute("outerHTML"))

            #if requestVariableTab is none then raise an Exception
            if not requestVariableTab :
                print("Unable to find Request Variables tab ,raising exception")
                raise WebDriverException
            
            #check it is selected or not using aria-selected attribute
            #while pharsing from html it will come as string so compare with "true" or "false" string
            #if it is not selected then click the tab
            isRequestVariableSelected: str = requestVariableTab.get_attribute("aria-selected")
            print(isRequestVariableSelected)
            if isRequestVariableSelected == "false" :
                print("request variable tab is not selected,selecting the section")
                requestVariableTab.click()
                print("request variables section selected")

            #find asset count Tag
            assetCountTag: WebElement = findAssetCountElement(driver)
            assetCountTag.clear()
            assetCountTag.send_keys(actualAssetCount)

            #find rootcause,solution and remediation status tags
            vulnerablityTags = findAllVulnerablityTags(driver)
            #get the vulnerablityDetails in taskDetails 
            vulnerablityDetails: dict = taskDetails["vulnerablityDetails"]
            
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
            validatedRowCount += 1
            print(f"{taskNumber} validated sucessfully - {validatedRowCount}/{totalRows}")

            #wait 2 second for save the record
            #time.sleep(2)

            if nextRecordBtnTagTitle == "Bottom of list displayed" or isNextRecordBtnTagDisabled == "true" :
                print("this is the bottom of the list so breaking the loop")
                break
            else:
                #get the next record
                print("getting the next record")
                #once clicked the save button the page will reload then our all webelements become stale element
                #find again nextRecordBtn tag
                nextRecordBtnTag = getNextRecordBtnTag(driver)
                nextRecordBtnTag.click()
                
                driver.switch_to.default_content()














    # except WebDriverException as e :
    #     print("General webdriver exception raised")
    #     return False
    except IndexError :
        print("index error")
    # except Exception as e :
    #     print("normal exceptio raised")
    #     print("something went wrong for additional info",e)
    finally:
        driver.quit()




if __name__ == "__main__":
    validatedtaskListPath: str = "./reports/validatedTaskList.json"
    if os.path.exists(validatedtaskListPath) :
        with open(validatedtaskListPath, "r") as file :
            validatedTaskList: dict = json.load(file)
        
        updateTasksInSnow(validatedTaskList)
    else:
        exit(-1)

    
    
    
    
    