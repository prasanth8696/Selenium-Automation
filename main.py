import os
import json
import pandas as pd
from pandas import DataFrame,Series
from csv_handler import convert_csv_to_xlsx
from functions import getMachineList,getQIDList,getNonRemediatedDetails,findAgingTicket,findVulnerablityDetails
from handler import getAssigmentGroup,getAssignedTo,getVulnerablityName,createReport,getTaskState,settings
from models import taskSchema




def main() :

    CMDB_FILE_PATH: str = settings["CMDB_FILE_PATH"]
    TASK_REPORT_PATH: str = settings["TASK_REPORT_PATH"]
    QUALYS_RAW_REPORT_PATH: str = settings["QUALYS_RAW_REPORT_PATH"]
    QUALYS_REPORT_PATH: str = eval(settings["QUALYS_REPORT_PATH"])
    #Note: for csv and xlsx format we have limitations 
    # we can store 32000+ characters in excel and csv formats but our description sometimes will cross this limit
    #for that using JSON format


    #load CMDB details
    computerList: DataFrame | Series = pd.read_excel(CMDB_FILE_PATH)

    #load tasklist from json file
    with open(TASK_REPORT_PATH,'r') as file :
        taskList = json.load(file)

    #Load Qulays report and convert if converted xlsx is not yet created
    if not os.path.isfile(QUALYS_REPORT_PATH) :
        response: dict = convert_csv_to_xlsx(file_path=QUALYS_RAW_REPORT_PATH)
        if response["status_code"] != 0 :
            print("unable to convert the raw report file")
            exit(-1)

    #Load Qulays report    
    qualysReport: DataFrame | Series = pd.read_excel(QUALYS_REPORT_PATH)


    validatedTaskList: list = []
    #create another dict for json
    validatedTaskDict: dict = {}
    for task in taskList['records'] :

        #check task is under Desktop Infra Support or Desktop Configuration Management or Desktop Engineering
        assignmentGrpDetails: dict = getAssigmentGroup(task["assignment_group"])
        
        #if ticket is not under desktop , skip the iteration
        if not assignmentGrpDetails["isDesktop"] :
            print(f"{task['number']} is not under desktop ")
            continue

        taskDetails: dict = taskSchema.copy()
        taskDescription: str = task["description"]
        machineList: list = getMachineList(taskDescription)
        QIDList: list = getQIDList(taskDescription)
        
        vulnerablityName: str = getVulnerablityName(qualysReport=qualysReport,QIDList=QIDList)
        vulnerablityDetails: dict = findVulnerablityDetails(vulnerablityName,taskDescription)

        #Filter the report using QIDList and nonRemediated machines
        currentTaskReport = qualysReport[(qualysReport["QID"].isin(QIDList)) & (qualysReport["DNS"].isin(machineList))]

        #ADD all the required values to taskDetails
        taskDetails["Sys_ID"] = task["sys_id"]
        taskDetails["Number"] = task["number"]
        print(task["number"])
        taskDetails["Vulnerablity Name"] = vulnerablityName
        taskDetails["task State"] = getTaskState(task["state"])
        taskDetails["Assigned To"] = getAssignedTo(task["assigned_to"])
        taskDetails["Assignment Group"] = assignmentGrpDetails["groupName"]
        taskDetails["QID List"] = QIDList

        #get aging details
        agingDetails: dict = findAgingTicket(task["opened_at"])
        taskDetails["Aging Ticket"] = agingDetails["isAging"]
        taskDetails["Total Task Days"] = agingDetails["taskDays"]
        taskDetails["vulnerablityDetails"] = vulnerablityDetails
         
        if len(currentTaskReport) > 0 :
            
            #for standard machines we need to count only in-service machines only
            if currentTaskReport.iloc[0]["DNS"].startswith("wxe") :
                nonRemediatedDetails = getNonRemediatedDetails(currentTaskReport,computerList,physical=True)
                taskDetails["Physical"] = True 
            #for virtual we need to count inservice and instock as well
            else :
                nonRemediatedDetails = getNonRemediatedDetails(currentTaskReport,computerList,physical=False) 
                taskDetails["Physical"] = False
            #total non remediated asset count
            taskDetails["Total Asset Count "] = nonRemediatedDetails["totalAssetCount"]
            taskDetails["In Service Count "] = nonRemediatedDetails["inServiceCount"]
            taskDetails["In Stock Count"] = nonRemediatedDetails["inStockCount"]
            taskDetails["Other CI Status Count"] = nonRemediatedDetails["otherCIStatusCount"]
            taskDetails["Last Detected Count(15days)"] = nonRemediatedDetails["lastDetected15"]
            taskDetails["Actual Asset Count"] = nonRemediatedDetails["actualAssetCount"]
            taskDetails["Possible to Close"] = True if nonRemediatedDetails["actualAssetCount"] == 0 else False
            taskDetails["Non-Remediated String"] = nonRemediatedDetails["nonRemediatedString"]

        validatedTaskList.append(taskDetails) 
        validatedTaskDict[task["number"]] = taskDetails

    #create the report
    createReport(validatedTaskList=validatedTaskList,validatedTaskDict=validatedTaskDict)
    
    


    
if __name__ == "__main__" :
    main()
