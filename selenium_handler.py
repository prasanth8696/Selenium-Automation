from handler import settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException,WebDriverException
from selenium.common.exceptions import ElementNotVisibleException, ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException



    
def waitForElement(driver: webdriver.Chrome,by,elementIdentifier: str,timeOut: int = 10) :
    
    try:
        isElementVisible = EC.presence_of_element_located((by,elementIdentifier))
        WebDriverWait(driver,timeOut).until(isElementVisible)
    
    except TimeoutException :
        print(f"timedOut waiting for {elementIdentifier}")
        return None
    
    return driver.find_element(by,elementIdentifier)

    


def getShadowRoot(driver,element) :
    return driver.execute_script("return arguments[0].shadowRoot",element)

def chooseSelectDropDown(element: WebElement,selectValue: str) :
    selectElement: Select = Select(element)
    #select one option
    selectElement.select_by_value(selectValue)


def selectAriaDropDown(driver: webdriver.Chrome,element: WebElement,inputValue: str) :
    element.clear()
    element.send_keys(inputValue)
    #wait upto elements are loaded
    try :
        WebDriverWait(driver,10).until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR,"*[role='option']"))
        )
        element.send_keys(Keys.ARROW_DOWN)
        ariaActiveDescendantID: str = element.get_attribute("aria-activedescendant")

        if ariaActiveDescendantID :
            element.send_keys(Keys.ENTER)
    
    except (TimeoutException, ElementNotVisibleException, ElementNotInteractableException) as e:
        raise Exception(f"The aria dropdown element was not found. Additional info: {str(e)}")

    
def findAssetCountElement(driver)  :
    trTag: WebElement = driver.find_element(By.CSS_SELECTOR,"div#container_row_7cd3e04b0fe04700d6cb05cce1050e92").find_elements(By.CSS_SELECTOR,"div.catalog-split")[-1].find_elements(By.CSS_SELECTOR,"tr[parent_container_id='7cd3e04b0fe04700d6cb05cce1050e92']")[-1]
    
    assetCountTag: WebElement = trTag.find_element(By.CSS_SELECTOR,"input.cat_item_option")

    return assetCountTag

def findAllVulnerablityTags(driver) -> dict :

    trTags: list = driver.find_element(By.CSS_SELECTOR,"div#container_row_d042ae9ddb98b70005d3a9a5ca961919").find_elements(By.CSS_SELECTOR,"tr[parent_container_id='d042ae9ddb98b70005d3a9a5ca961919']")

    #find root cause,remediation tag and solution tag
    #we will get three  tr tags(inefficient method but will work for now )
    #one is for root Cause
    #second one is for Remediation Status
    #third one is for solution
    if len(trTags) >= 3 :
        rootCauseTag: WebElement = trTags[0].find_element(By.CSS_SELECTOR,"textarea.question_textarea_input")

        remediationStatusTag: WebElement = trTags[1].find_element(By.CSS_SELECTOR,"input.cat_item_option")
        
        solutionTag: WebElement = trTags[2].find_element(By.CSS_SELECTOR,"textarea.question_textarea_input")

        return {
            "rootCauseTag" : rootCauseTag,
            "remediationTag": remediationStatusTag,
            "solutionTag": solutionTag
                
                }
    else:
        raise Exception


#snow initial selenium process for sc tasks
def snowInitialProcessForTasks(driver:webdriver.Chrome):
    try:
        #wait for Shadow Host
        shadowHost: WebElement = waitForElement(driver,By.TAG_NAME,"macroponent-f51912f4c700201072b211d4d8c26010")
        #Find the shadow root from the shadow host
        shadowRoot: WebElement = getShadowRoot(shadowHost)
        #find the mainIframe and switch to iframe
        mainIframe: WebElement = shadowRoot.find_element(By.CSS_SELECTOR,"iframe#gsft_main")

        #switch to mainframe
        driver.switch_to.frame(mainIframe)
        return True
    except WebDriverException as e :
        print("something went wrong for additinal info",e)
        return False
    
def getNextRecordBtnTag(driver: webdriver.Chrome) :

    try:
        headerTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"div#sc_task\\.form_header")
        #find the div tag which is contain class attribute record-paging-nowrap
        #this div contains two button tags last one is our next button tag
        nextRecordBtnTag = headerTag.find_element(By.CSS_SELECTOR,"div.record-paging-nowrap").find_elements(By.CSS_SELECTOR,"button.btn-icon")[-1]
        return nextRecordBtnTag
    
    except WebDriverException as e :
        print("something went wrong for additinal info",e)
        return False
    
def getTabSectionSpanTag(driver: webdriver.Chrome,tabName: str) :
    try:
        #wait for tabsection fully loaded
        tabSection: WebElement = waitForElement(driver,By.CSS_SELECTOR,"#tabs2_section[role='tablist']")

        #get the actual span tags from tabSection
        spanTags: WebElement = tabSection.find_elements(By.CSS_SELECTOR,"span[role='tab']")

        #for iterate and get the required tab
        for spanTag in spanTags :
            tabCaptionSpanTag: WebElement = spanTag.find_element(By.CSS_SELECTOR,"span.tab_caption_text")
            tabCaptionSpanTagValue : str = tabCaptionSpanTag.text
            print(tabCaptionSpanTagValue)
            print(tabCaptionSpanTag.get_attribute("outerHTML"))


            if (tabCaptionSpanTagValue == tabName) :
                return spanTag
            
        return False

    except WebDriverException as e :
        print("something went wrong for additinal info",e)
        return False


    

    


    

 


# driverPath: str = settings["CHROME_DRIVER_PATH"]
# serviceObj: Service = Service(driverPath)

# # chrome_options = Options()
# # chrome_options.add_argument("user-data-dir=C:\\Users\\10731263\\AppData\\Local\\Google\\Chrome\\User Data")
# # chrome_options.add_argument("--profile.directory.profile=10")
# # chrome_options.add_argument("--no-sandbox")

# #driver: webdriver.Chrome = webdriver.Chrome(service=serviceObj,options=chrome_options)
# driver: webdriver.Chrome = webdriver.Chrome(service=serviceObj)
# driver.maximize_window()
# sysID = "4109cc229310de14102cf4647aba1023"
# driver.get(f"https://imf.service-now.com/now/nav/ui/classic/params/target/sc_task.do%3Fsys_id%3D{sysID}%26sysparm_stack%3D%26sysparm_view%3D")
# input()

# #shadowHost1: WebElement = driver.find_element(By.TAG_NAME,"macroponent-f51912f4c700201072b211d4d8c26010")
# shadowHost1: WebElement = waitForElement(driver,By.TAG_NAME,"macroponent-f51912f4c700201072b211d4d8c26010")

# #snowID: str = shadowHost1.get_attribute("now-id")
# #print(snowID)
# shadowRoot: WebElement = getShadowRoot(shadowHost1)

# mainIframe: WebElement = shadowRoot.find_element(By.CSS_SELECTOR,"iframe#gsft_main")

# driver.switch_to.frame(mainIframe)

# #taskNumber: WebElement = driver.find_element(By.CSS_SELECTOR,"input#sc_task\\.number")
# taskNumber: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sc_task\\.number")
# print(taskNumber.get_attribute("value"))

# # assigmentGrpTag: WebElement = driver.find_element(By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assignment_group")
# # assignedTo: WebElement = driver.find_element(By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assigned_to")
# assigmentGrpTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assignment_group")
# assignedTo: WebElement = waitForElement(driver,By.CSS_SELECTOR,"input#sys_display\\.sc_task\\.assigned_to")

# #get the worknotes textarea
# #workNotesTag : WebElement = driver.find_element(By.CSS_SELECTOR,"textarea#activity-stream-textarea")
# workNotesTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"textarea#activity-stream-textarea")
# print(workNotesTag)
# nonRemediatedStr = "Not Remediated:\n\nwxe147255.was.int.imf.org\nwxe151205.was.int.imf.org\n"
# workNotesTag.send_keys(nonRemediatedStr)
# #get the save button
# #saveBtnTag: WebElement = driver.find_element(By.CSS_SELECTOR,"button#sysverb_update_and_stay")
# saveBtnTag: WebElement = waitForElement(driver,By.CSS_SELECTOR,"button#sysverb_update_and_stay")

# #select tag handling
# selectTaskState: WebElement = driver.find_element(By.CSS_SELECTOR,"select#sc_task\\.state")
# chooseSelectDropDown(driver,selectTaskState,"2")
# # taskState: Select = Select(selectTaskState)
# # #find selected options:
# # selected_option = taskState.all_selected_options
# # print(selected_option)
# # #select one option
# # taskState.select_by_value("2")


# selectAriaDropDown(assigmentGrpTag,"Desktop Configuration Management")
# selectAriaDropDown(assignedTo,"Ayyappan Dharmalingam")


# # print(assigmentGrpTag.get_attribute("value"))
# # #clear inputTags
# # assigmentGrpTag.clear()
# # assigmentGrpTag.send_keys("Desktop Configuration Management")
# # time.sleep(3)
# # assigmentGrpTag.send_keys(Keys.ARROW_DOWN)
# # activeAriadescentantID = assigmentGrpTag.get_attribute("aria-activedescendant")
# # print(activeAriadescentantID)
# # higlightedOption = driver.find_element(By.CSS_SELECTOR,f"#{activeAriadescentantID}")

# # print("higglihted tag")
# # print(higlightedOption)
# # print(higlightedOption.get_attribute("outerHTML"))
# # print(higlightedOption.get_attribute("innerHTML"))

# # assigmentGrpTag.send_keys(Keys.ENTER)

# # assignedTo.clear()
# # assignedTo.send_keys("Ayyappan Dharmalingam")
# # time.sleep(3)
# # assignedTo.send_keys(Keys.ARROW_DOWN)
# # activeAriadescentantID1 = assignedTo.get_attribute("aria-activedescendant")
# # higlightedOption = driver.find_element(By.CSS_SELECTOR,f"#{activeAriadescentantID1}")
# # print("higglihted tag")
# # print(higlightedOption)
# # print(higlightedOption.get_attribute("outerHTML"))
# # print(higlightedOption.get_attribute("innerHTML"))
# # if activeAriadescentantID1 :
# #     assignedTo.send_keys(Keys.ENTER)


# #ele1: WebElement = shadowRoot.find_element(By.CSS_SELECTOR,f"sn-polaris-layout[component-id='{snowID}-polarisLayout']")

# #currently comments and worknotes selected for that we need to click request variable then only selenium able to see the request varibales
# requestvarTab: WebElement = driver.find_elements(By.CSS_SELECTOR,"span[role='tab']")[1]
# #print(requestvarTab.get_attribute("outerHTML"))
# requestvarTab.click()

# #find asset count tag
# assetCountTag: WebElement = findAssetCountElement()
# assetCount: int = 2
# assetCountTag.send_keys(assetCount)

# #fill all vulnerabilty tags
# vulnerablityTags = findAllVulnerablityTags()
# vulnerablityTags["rootCauseTag"].send_keys("UWP Apps")
# vulnerablityTags["solutionTag"].send_keys("MS Store")
# vulnerablityTags["remediationTag"].send_keys("Assess")
# saveBtnTag.click()
# input()
    
