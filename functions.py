import re
import os
import json
import logging
from datetime import datetime
import pandas as pd
from handler import settings
from pandas import DataFrame,Series


#enable logging
logger: logging.getLogger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
if not os.path.exists(settings["Log_path"]):
    os.mkdir(settings["Log_path"])

fullLogName: str = os.path.join(settings["Log_path"],eval(settings["Log_name"]))
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



#load all nessacery json files
if os.path.exists("vulnerablityDetails.json") and os.path.exists("request_variables.json") :
    with open("vulnerablityDetails.json","r") as file1 :
        vulnerablityDetails: list = json.load(file1)

    #load request_variables.json
    with open("request_variables.json","r") as file2 :
        requestVariables: dict = json.load(file2)
else :
    print("request_variables.json or vulnerablityDetails.json doesnt exist in the current directory")
    os.exit(-1)



#Get the unique machine names from the ticket description
def getMachineList(descriptionString: str,searchPattern: str = r"wx[ev].*|epam.*" ) -> list :

    logger.info("getMachineList function - Started")
    logger.info("Finding the machine pattern match in description string - Started")
    totalMachinesString: list = re.findall(searchPattern,descriptionString)
    logger.info("Finding the machine pattern match in description string - Done")
    finalmachinesList = []

    logger.info("splitting and remove the duplicate devices - Started")
    [ finalmachinesList.extend(machineString.split()) for machineString in totalMachinesString ]

    #remove duplicate machines and return the machinelist as list
    logger.info("splitting and remove the duplicate devices - Done")
    logger.info("getMachineList function - Done")
    return list(set(finalmachinesList))

#Get the unique QID lists from the ticket description
def getQIDList(descriptionString: str,searchPattern: str = r"QID[: ].*") -> list :

    logger.info("getQIDList function  - Started")
    logger.info("Finding the QID pattern match in description string - Started")
    totalQIDString = re.findall(searchPattern,descriptionString)
    logger.info("Finding the QID pattern match in description string - Done")

    finalQIDList = []
    #Extract the QID from the RAW string and convert QID as integer
    logger.info("splitting and remove the duplicate QID's - Started")
    extractQIDLogicString = "list(map(int,QIDString.split(':')[-1].strip().split(',')))"
    [ finalQIDList.extend(eval(extractQIDLogicString)) for QIDString in totalQIDString ]

    #remove duplicate QID's and return the QIDList as list
    logger.info("splitting and remove the duplicate QID's - Done")
    logger.info("getQIDList function  - Done")
    return list(set(finalQIDList))

def getNonRemediatedString(activeMachineDetails: DataFrame | Series) -> str :

    logger.info("getNonRemediatedString function - Started")
    nonRemediatedString: str = "Non Remediated:\n\n"
    lastDetectedString: str = "\n\nLast Detected More Than 15 days\n"
    activeMachineDetails = activeMachineDetails.reset_index()
    actualCount: int = 0; lastDetected15: int = 0
    for _,activeMachine in activeMachineDetails.iterrows() :
        
        #exclude if last detcted more than 15 days
        if activeMachine["Last Detected(In Days)"] <= 15 :
            if activeMachine["Last Detected(In Days)"] < 5 :
                nonRemediatedString += f"{activeMachine['NetBIOS'].lower()} \n"
            else:
                nonRemediatedString += f"{activeMachine['NetBIOS'].lower()} - last detected {activeMachine["Last Detected(In Days)"]} Days \n"

        else:
            lastDetectedString += f"{activeMachine['NetBIOS'].lower()} - last detected {activeMachine['Last Detected(In Days)']} Days- \n"

    logger.info("getNonRemediatedString function - Done")
    return nonRemediatedString + lastDetectedString

    

def getNonRemediatedDetails(qulaysReport: DataFrame | Series ,computerList: DataFrame | Series,physical: bool = True)  ->  dict :

    logger.info("getNonRemediatedDetails function - Started")
    nonRemediatedDetails = {}

    #Merge two dataframes to get the machine data
    logger.debug("Merging Qualys dataframe and CMDB dataframe")
    mergeData: DataFrame | Series = qulaysReport.merge(computerList,how="left",left_on=qulaysReport["NetBIOS"].str.lower(),right_on=computerList["Name"].str.lower())

    #Add Last Detected(In Days) column in existing dataframe
    logger.info("Adding new last detected cloumn in existing merged dataframe - Started")
    lamdaLogicString: str = 'abs((datetime.strptime(row["Last Detected"],r"%m/%d/%Y %H:%M:%S") - datetime.today()).days)'
    mergeData["Last Detected(In Days)"] = mergeData.apply(lambda row: eval(lamdaLogicString),axis=1 )
    logger.info("Adding new last detected cloumn in existing merged dataframe - Done")

    logger.info("getting all the require non remdiated CI status machines - Started")
    #find in-service machines
    inserviceMachinesData: DataFrame | Series = mergeData[mergeData["CI Status"].isin(["In Service"])]
    logger.debug("filtered inservice machine details successfully")

    #find in-stock machines 
    inStockMachinesData: DataFrame | Series = mergeData[mergeData["CI Status"].isin(["In Stock"])]
    logger.debug("filtered instock machine details successfully")

    #Get other CI status machines(it is included if machine dont have cmdb records)
    otherCIStatusMachinesData: DataFrame | Series = mergeData[~mergeData["CI Status"].isin(["In Service","In Stock"])]
    logger.debug("filtered other CIStatus machine details successfully")

    # #Get more than 15days machines
    # lastDetected15: DataFrame | Series = mergeData[mergeData["Last Detected(In Days)"] > 15]

    logger.info("getting all the require non remdiated CI status machines - Done")
    ## Add required values to nonRemediatedDetails dictionary
    nonRemediatedDetails["totalAssetCount"] = len(set(list(mergeData["DNS"])))
    nonRemediatedDetails["inServiceCount"] = len(set(list(inserviceMachinesData["DNS"])))
    nonRemediatedDetails["inStockCount"] = len(set(list(inStockMachinesData["DNS"])))
    nonRemediatedDetails["otherCIStatusCount"] = len(set(list(otherCIStatusMachinesData["DNS"])))
    logger.debug("checking current task is reported for physical or virutal machine")
    if physical == True :
        logger.debug("current task is reported for physical machine")
        logger.debug("getting total machine count as inservice machines for physical machines")
        totalMachinesData: DataFrame | Series = inserviceMachinesData  
    else :
        logger.debug("current task is reported for virtual machine")
        logger.debug("getting total machines count as inservice+ instock machines for virtual machines")
        totalMachinesData: DataFrame | Series = pd.concat([inserviceMachinesData,inStockMachinesData],axis=0)
    
    actualAssetData: DataFrame | Series = totalMachinesData[totalMachinesData["Last Detected(In Days)"] <= 15]
    actualLastDetected15: DataFrame | Series = totalMachinesData[totalMachinesData["Last Detected(In Days)"] > 15]
    nonRemediatedDetails["lastDetected15"] = len(set(list(actualLastDetected15["DNS"])))
    nonRemediatedDetails["actualAssetCount"] = len(set(list(actualAssetData["DNS"])))
 

    
    #Remove Duplicates 
    #Get NonRemediatedString
    logger.info("getting non remediated string for work notes - Started")
    uniqueActiveMachines = (totalMachinesData[["DNS","NetBIOS","Last Detected(In Days)"]]).drop_duplicates("DNS")
    if len(actualAssetData) != 0 :
        logger.debug("actual asset count is not zero so getting the non remdiated sting from getNonRemdiatedString function")
        nonRemediatedDetails["nonRemediatedString"] = getNonRemediatedString(uniqueActiveMachines)
    else :
        nonRemediatedDetails["nonRemediatedString"] = "all assets are remediated so closing the ticket"
        logger.info("getting non remediated string for work notes - Done")

    
    logger.info("getNonRemediatedDetails function - Done")
    return nonRemediatedDetails
    

#find ticket is aging ticket or not
#if tickets opened more than 30 days return true and taskDays
#need to change washington timezone(currently kolkata/mumbai timezone) so diffeence will be there
def findAgingTicket(taskOpenedDate: str) -> dict :
    logger.info("findAgingTicket function - Done")
    taskOpenedDays = abs((datetime.strptime(taskOpenedDate,r"%Y-%m-%d %H:%M:%S") - datetime.today()).days)

    if taskOpenedDays >= 30 :
        logger.debug("current task openedDays is greater than or equal to 30days")
        logger.info("findAgingTicket function - Done")
        
        return {"isAging" : True,"taskDays" : taskOpenedDays}
    else:
        logger.debug("current task openedDays is  less than  30days")
        logger.info("findAgingTicket function - Done")

        return {"isAging" : False,"taskDays" : taskOpenedDays}
    
#find root cause and solution and other vulnerablities related details 
#need to change function of this code beacuse this function will use O(n2) time complexicity
def findVulnerablityDetails(taskTitle: str,taskDescription: str) -> dict:
    currentTaskDetails: dict = requestVariables["default"]

    for record in vulnerablityDetails:
        titleMatched: bool = False
        resultMatched: bool = False

        if taskTitle.find(record["identificationString"]) != -1 :
            titleMatched = True

        for resultSection in record["results"] :
            if taskDescription.find(resultSection) != -1 :
                resultMatched = True
                break
        if titleMatched or resultMatched :
            currentTaskDetails = requestVariables.get(record["name"])

    return currentTaskDetails
            











