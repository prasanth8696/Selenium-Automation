import os
import json
import pandas as pd
from pandas import DataFrame,Series



#load the settings.json file   
if not os.path.exists("./settings.json") :
    print("settings file not Found")
    exit(-1)
with open("./settings.json","r") as file :
    settings: dict = json.load(file)
        

def getVulnerablityName(qualysReport: DataFrame | Series,QIDList: list ) -> str :

    vulnerablityName: str = ""
    if QIDList :
        #for equal we need to use loc (dontknow)
        specificQIDreport = qualysReport.loc[qualysReport["QID"]  == QIDList[0]]
        if not specificQIDreport.empty :
            vulnerablityName = specificQIDreport.iloc[0].Title
    
    return vulnerablityName

def getAssigmentGroup(groupID: str) -> str :
    assignmentGroup = groupID
    if settings["Assignments_groups"] :
        for grpID,assignment_grp in settings["Assignments_groups"].items() :
            if groupID == grpID :
                assignmentGroup = assignment_grp
                break
    return assignmentGroup



def getAssignedTo(userID) -> str :
    userName = userID
    if settings["Assigned_to"] :
        for assignedToID,assignedTo in settings["Assigned_to"].items() :
            if userID == assignedToID :
                userName = assignedTo
                break
    return userName

def getTaskState(stateID: str) -> str :
    taskStateStr = stateID
    if settings["Task_state"] :
        for taskStateID,taskState in settings["Task_state"].items() :
            if stateID == taskStateID :
                userName = taskState
                break
    return taskStateStr



def createReport(validatedTaskList: list) -> str :

    #convert the dictionary to Json format
    if not os.path.isdir("./reports") :
        os.mkdir("./reports")
    with open("./reports/validatedTaskList.json",'w') as file :
        json.dump({"records" : validatedTaskList},file)
    #convert to Xlsx format
    df = pd.DataFrame(validatedTaskList)
    df.to_excel("./reports/validatedTaskList.xlsx",sheet_name="Vulnerablity Tasks Report",index=False)



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