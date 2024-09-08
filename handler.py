import os
import json
import logging
from datetime import datetime
import pandas as pd
from pandas import DataFrame,Series



#load the settings.json file

if not os.path.exists("./settings.json") :
    print("settings.json not found")
    exit(-1)

with open("./settings.json","r") as file :
    settings: dict = json.load(file)


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



 

        

def getVulnerablityName(qualysReport: DataFrame | Series,QIDList: list ) -> str :

    vulnerablityName: str = ""
    logger.info("getVulnerablityName function - Started")
    if QIDList :
        #for equal we need to use loc (dontknow)
        logger.debug("filtering the qualys report using first qualys QID")
        specificQIDreport = qualysReport.loc[qualysReport["QID"]  == QIDList[0]]
        logger.debug("checking filtered records it empty or not")
        if not specificQIDreport.empty :
            logger.debug("filtered records is not empty so getting title from the firsr record")
            vulnerablityName = specificQIDreport.iloc[0].Title
        else:
            logger.debug("filtered record is empty,returning empty name")

    logger.info("getVulnerablityName function - Done")
    return vulnerablityName

def getAssigmentGroup(groupID: str) -> dict :
    
    logger.info("getAssignmentGroup function - Started")
    assignmentGrpDetails: dict = { "isDesktop" : False,"groupName" : groupID } 
    if settings["Assignments_groups"] :
        logger.debug("Looping all the deafault assignment groups in the setings and matching with current one")
        for grpID,assignment_grp in settings["Assignments_groups"].items() :
            if groupID == grpID :
                logger.debug(f"current record {grpID}-{assignment_grp} is matching with current task grp ID {groupID}")
                assignmentGrpDetails["groupName"] = assignment_grp
                assignmentGrpDetails["isDesktop"] = True 
                logger.debug("match found so breaking the loop")
                break
        if not assignmentGrpDetails["isDesktop"] :
            logger.debug("match not found with current desktop assignments grp")

    logger.info("getAssignmentGroup function - Done")
    return assignmentGrpDetails



def getAssignedTo(userID) -> str :

    logger.info("getAssignTo function - Started")
    logger.debug("setting the userID valud as deafult value to username to return if mactches not found")
    userName: str = userID
    if settings["Assigned_to"] :
        for assignedToID,assignedToDetails in settings["Assigned_to"].items() :
            if userID == assignedToID :
                userName = assignedToDetails["Full_name"]
                logger.debug("Match Found ,so breaking the loop")
                break

    logger.info("getAssignTo function - Done")
    return userName

def getTaskState(stateID: str) -> str :

    logger.info("getTaskState function - Started")
    logger.debug("setting the input taskstate value as deafult value to output taskstate to return if mactches not found")
    taskStateStr = stateID
    if settings["Task_state"] :
        for taskStateID,taskState in settings["Task_state"].items() :
            if stateID == taskStateID :
                taskStateStr = taskState
                logger.debug("Match Found ,so breaking the loop")
                break
    logger.info("getTaskState function - Done")
    return taskStateStr



def createReport(validatedTaskList: list,validatedTaskDict: dict) -> str :
    
    #convert the dictionary to Json format
    logger.info("createReport function - Started")

    logger.debug("checking ./reports directory exists status")
    if not os.path.isdir("./reports") :
        logger.debug("./reports directory not exists")
        logger.info("creating ./reports  directory - Started")

        os.mkdir("./reports")
        logger.info("creating ./reports  directory - Done")

    logger.info("creating report as json format - Started")
    with open("./reports/validatedTaskList.json",'w') as file :
        json.dump(validatedTaskDict,file,indent=2)
    logger.info("creating report as json format - Done")

    #convert to Xlsx format
    logger.info("creating report as xlsx format - Started")
    df = pd.DataFrame(validatedTaskList)
    df.to_excel("./reports/validatedTaskList.xlsx",sheet_name="Vulnerablity Tasks Report",index=False)
    logger.info("creating report as xlsx format - Done")

    logger.info("createReport function - Done")



"""
NOTE: we can use one function for getting value from settings.json but 
im using multiple functions for others readablity
you can use this function for getting all values from settings
def getValueFromsettings(ID: str,variableName: str) -> str :
    value = ID
    if settings.get(variableName,None) != None  :
        for varID,varValue in settings["variableName"].items() :
            if ID == varID :
                value = varValue
                break
    return value
        HAPPY CODING!!!
"""