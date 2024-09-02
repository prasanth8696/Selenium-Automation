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


#if modify the path if platform is windows
# if os.name == "nt" :
#     for var,value in settings.items() :
#         if var.find("PATH") != -1 :
#             new = value.replace("\\\\","\\")
#             settings[var] = new
#             print(value.replace("\\\\","\\"))
#             print(settings[var])
# print(settings)


        

def getVulnerablityName(qualysReport: DataFrame | Series,QIDList: list ) -> str :

    vulnerablityName: str = ""
    if QIDList :
        #for equal we need to use loc (dontknow)
        specificQIDreport = qualysReport.loc[qualysReport["QID"]  == QIDList[0]]
        if not specificQIDreport.empty :
            vulnerablityName = specificQIDreport.iloc[0].Title
    
    return vulnerablityName

def getAssigmentGroup(groupID: str) -> dict :
    assignmentGrpDetails: dict = { "isDesktop" : False,"groupName" : groupID } 
    if settings["Assignments_groups"] :
        for grpID,assignment_grp in settings["Assignments_groups"].items() :
            if groupID == grpID :
                assignmentGrpDetails["groupName"] = assignment_grp
                assignmentGrpDetails["isDesktop"] = True 
                break
    return assignmentGrpDetails



def getAssignedTo(userID) -> str :
    userName: str = userID
    if settings["Assigned_to"] :
        for assignedToID,assignedToDetails in settings["Assigned_to"].items() :
            if userID == assignedToID :
                userName = assignedToDetails["Full_name"]
                break
    return userName

def getTaskState(stateID: str) -> str :
    taskStateStr = stateID
    if settings["Task_state"] :
        for taskStateID,taskState in settings["Task_state"].items() :
            if stateID == taskStateID :
                taskStateStr = taskState
                break
    return taskStateStr



def createReport(validatedTaskList: list) -> str :

    #convert the dictionary to Json format
    if not os.path.isdir("./reports") :
        os.mkdir("./reports")
    with open("./reports/validatedTaskList.json",'w') as file :
        json.dump({"records" : validatedTaskList},file,indent=2)
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