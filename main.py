import os
import json
import pandas as pd
from csv_handler import convert_csv_to_xlsx
from functions import getMachineList,getQIDList,getNonRemediatedDetails
from handler import getAssigmentGroup,getAssignedTo,getVulnerablityName,createReport,getTaskState,settings





def main() :



    CMDB_FILE_PATH = r"C:\Users\10731263\Downloads\cmdb_ci_computer.xlsx"
    QUALYS_REPORT_PATH = os.path.join(os.getcwd(),"Scheduled-Report-Cloud-Agent-Report-non_Superseded_New.xlsx")
    #Note: for csv and xlsx format we have limitations 
    # we can store 32000+ characters in excel and csv formats but our description sometimes will cross this limit
    #for that using JSON format
    TASK_REPORT_PATH = r"C:\Users\10731263\Downloads\sc_task (1).json"

    #load CMDB details
    computerList = pd.read_excel(CMDB_FILE_PATH)

    #load tasklist from json file
    with open(TASK_REPORT_PATH,'r') as file :
        taskList = json.load(file)

    #Load Qulays report and convert if converted xlsx is not yet created
    if not os.path.isfile(QUALYS_REPORT_PATH) :
        response = convert_csv_to_xlsx(file_path=r"C:\Users\10731263\Downloads\Scheduled-Report-Cloud-Agent-Report-non_Superseded_New-20240825054505.csv")
        if response["status_code"] != 0 :
            print("unable to conver the file")
            exit(-1)
        
    qualysReport = pd.read_excel(QUALYS_REPORT_PATH)


    validatedTaskList: list = []
    for task in taskList['records'] :

        taskDetails: dict = {}
        taskDescription: str = task["description"]
        machineList: list = getMachineList(taskDescription)
        QIDList: list = getQIDList(taskDescription)
        
        vulnerablityName: str = getVulnerablityName(qualysReport=qualysReport,QIDList=QIDList)

        #Filter the report using QIDList and nonRemediated machines
        currentTaskReport = qualysReport[(qualysReport["QID"].isin(QIDList)) & (qualysReport["DNS"].isin(machineList))]

        #ADD all the required values to taskDetails
        taskDetails["Number"] = task["number"]
        print(task["number"])
        taskDetails["Vulnerablity Name"] = vulnerablityName
        taskDetails["task State"] = getTaskState(task["state"])
        taskDetails["Assigned To"] = getAssignedTo(task["assigned_to"])
        taskDetails["Assignment Group"] = getAssigmentGroup(task["assignment_group"])
        taskDetails["QID List"] = QIDList
        
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
            taskDetails["possible to Close"] = True if nonRemediatedDetails["actualAssetCount"] == 0 else False
            taskDetails["Non-Remediated String"] = nonRemediatedDetails["nonRemediatedString"]

        validatedTaskList.append(taskDetails)

            


    #create the report
    createReport(validatedTaskList=validatedTaskList)
    


    
if __name__ == "__main__" :
    main()
