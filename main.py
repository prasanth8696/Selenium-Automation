import os
import json
import logging
from datetime import datetime
import pandas as pd
from pandas import DataFrame,Series
from csv_handler import convert_csv_to_xlsx
from functions import getMachineList,getQIDList,getNonRemediatedDetails,findAgingTicket,findVulnerablityDetails
from handler import getAssigmentGroup,getAssignedTo,getVulnerablityName,createReport,getTaskState,fileCleanup,settings
from models import taskSchema
from task_update import updateTasksInSnow


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


def main() :
    logger.info("main function started")
    fileCleanup()
    logger.info("get all the required path from settings - Started")
    CMDB_FILE_PATH: str = settings["CMDB_FILE_PATH"]
    TASK_REPORT_PATH: str = settings["TASK_REPORT_PATH"]
    QUALYS_RAW_REPORT_PATH: str = settings["QUALYS_RAW_REPORT_PATH"]
    QUALYS_REPORT_PATH: str = eval(settings["QUALYS_REPORT_PATH"])
    logger.info("get all the required path from settings - Done")
    #Note: for csv and xlsx format we have limitations 
    # we can store 32000+ characters in excel and csv formats but our description sometimes will cross this limit
    #for that using JSON format


    #load CMDB details
    logger.info(f"Loding CMBD data  from {CMDB_FILE_PATH} - Started")
    computerList: DataFrame | Series = pd.read_excel(CMDB_FILE_PATH)
    logger.info(f"CMDB data data succcessfully loaded - Done")

    #load tasklist from json file
    logger.info(f"Loding service now  vulnerablities tasks  from {TASK_REPORT_PATH} - Started")
    with open(TASK_REPORT_PATH,'r') as file :
        taskList = json.load(file)
        logger.info(f"service now vulnerablities tasks succcessfully loaded - Done")

    #Load Qulays report and convert if converted xlsx is not yet created
    logger.info(f"Loding Qualys latest report  from {QUALYS_REPORT_PATH} - Started")
    logger.info(f"checking {QUALYS_REPORT_PATH} path is exists or not ")
    if not os.path.isfile(QUALYS_REPORT_PATH) :

        logger.debug(f"{QUALYS_REPORT_PATH}  Qualys report path not exists")
        logger.info(f"converting  Qulays Raw data  to normal report from {QUALYS_RAW_REPORT_PATH}")
        response: dict = convert_csv_to_xlsx(file_path=QUALYS_RAW_REPORT_PATH)
        if response["status_code"] != 0 :
            logging.error("unable to Extract the original report from Qulays Raw report")
            exit(-1)
        logger.info(f"created Qulays report from qualys report successfully")

    #Load Qulays report   
    qualysReport: DataFrame | Series = pd.read_excel(QUALYS_REPORT_PATH)
    logger.info("Qualys report loaded successfully - Done")
   

    validatedTaskList: list = []
    #create another dict for json
    validatedTaskDict: dict = {}
    logger.info(f"total task Count: {len(taskList['records'])}")
    logger.info("Looping all tasks to get the consolidated details")
    for task in taskList['records'] :
        
        try:
            logger.info(f"##### getting the consolidated details for Task Number: {task['number']} - Started #####")
            #check task is under Desktop Infra Support or Desktop Configuration Management or Desktop Engineering
            logger.debug(f"checking current task in under deafult Assignment Groups")
            assignmentGrpDetails: dict = getAssigmentGroup(task["assignment_group"])
            
            #if ticket is not under desktop , skip the iteration
            if not assignmentGrpDetails["isDesktop"] :
                logger.debug(f"current Task Number: {task['number']} is not under Deafult Assigments groups")
                logger.debug("skipping the current iteration")
                continue
            logger.debug(f"current task {task['number']} assignment groups is {assignmentGrpDetails['groupName']}")
            logger.info(f"checking current task in under deafult Assignment Groups successfully - Done")

            logger.info("getting task Schema fro nonremediated details")
            taskDetails: dict = taskSchema.copy()
            taskDescription: str = task["description"]

            logger.info("getting the all machine names list from task description - Started")
            machineList: list = getMachineList(taskDescription)
            logger.info(f"getting the all machine names list from task description successfully - Done")

            logger.info(f"getting the all QID list from task description - Started")
            QIDList: list = getQIDList(taskDescription)
            logger.info(f"getting the all QID list from task description  successfully- Done")
            
            logger.info("getting vulnerablity title from the Qualys report using QID - Started")
            vulnerablityName: str = getVulnerablityName(qualysReport=qualysReport,QIDList=QIDList)
            logger.info("getting vulnerablity title from the Qualys report using QID  is successfully - Done")

            logger.info(f"getting root cause,solution,remediation details for Task Number: {task['number']} - Started" )
            vulnerablityDetails: dict = findVulnerablityDetails(vulnerablityName,taskDescription)
            logger.info(f"getting root cause,solution,remediation details for Task Number: {task['number']} sucessfully - Done")

            #Filter the report using QIDList and nonRemediated machines
            logger.info("filtering active nonremdiated machine details from qulays report using QID and machine list - Started")
            currentTaskReport = qualysReport[(qualysReport["QID"].isin(QIDList)) & (qualysReport["DNS"].isin(machineList))]
            logger.debug(f"active nonRemediated machine count(with duplicate): {len(currentTaskReport)} ")
            logger.info("filtering active nonremdiated machine details from qulays report using QID and machine list successfully - Done")

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
            logger.info(f"getting the Aging report for TaskNo: {task['number']} - Started")
            agingDetails: dict = findAgingTicket(task["opened_at"])
            logger.debug(f"current task is aging: {agingDetails['isAging']} ")
            logger.info(f"getting the Aging report for TaskNo: {task['number']} - Done")

            taskDetails["Aging Ticket"] = agingDetails["isAging"]
            taskDetails["Total Task Days"] = agingDetails["taskDays"]
            taskDetails["vulnerablityDetails"] = vulnerablityDetails
            
            logger.debug("checking all machines are remediated or not - Started")
            if len(currentTaskReport) > 0 :
                
                logger.debug(f"currently active non remediated count is {len(currentTaskReport)} ")
                logger.info(f"getting non remediated count details for {task['number']} - Started")

                #for standard machines we need to count only in-service machines only
                logger.info("checking current task is for physical machine or virual machine - Started")
                if currentTaskReport.iloc[0]["DNS"].startswith("wxe") :
                    logger.info(f"current Task {task['number']} is reported for physical machine")
                    nonRemediatedDetails = getNonRemediatedDetails(currentTaskReport,computerList,physical=True)
                    taskDetails["Physical"] = True 
                #for virtual we need to count inservice and instock as well
                else :
                    logger.info(f"current Task {task['number']} is reported for virual machine")
                    nonRemediatedDetails = getNonRemediatedDetails(currentTaskReport,computerList,physical=False) 
                    taskDetails["Physical"] = False
                logger.info("checking current task is for physical machine or virual machine - Done")
                logger.info(f"Adding required asset count details into list for Task No: {task['number']} - Started")
                #total non remediated asset count
                taskDetails["Total Asset Count "] = nonRemediatedDetails["totalAssetCount"]
                taskDetails["In Service Count "] = nonRemediatedDetails["inServiceCount"]
                taskDetails["In Stock Count"] = nonRemediatedDetails["inStockCount"]
                taskDetails["Other CI Status Count"] = nonRemediatedDetails["otherCIStatusCount"]
                taskDetails["Last Detected Count(15days)"] = nonRemediatedDetails["lastDetected15"]
                taskDetails["Actual Asset Count"] = nonRemediatedDetails["actualAssetCount"]
                taskDetails["Possible to Close"] = True if nonRemediatedDetails["actualAssetCount"] == 0 else False
                taskDetails["Non-Remediated String"] = nonRemediatedDetails["nonRemediatedString"]

                logger.info(f"Adding required asset count details into list for Task No: {task['number']} - Done")
                logger.info(f"getting non remediated count details for {task['number']} - Done")

            else:
                taskDetails["Non-Remediated String"] = "all assets are remediated so closing the ticket"
                logger.debug(f"active machines not found for {task['number']} ")

            

            logger.info("adding current task details to list to create report")
            validatedTaskList.append(taskDetails)
            validatedTaskDict[task["number"]] = taskDetails
            logger.info(f"##### getting the consolidated details for Task Number: {task['number']} - Done #####")
        
        except KeyError as e:
            logger.exception(f"got key error while processing the current task {e}")
            logger.debug("Skipping current task")
            continue

        except ValueError as e:
            logger.exception(f"got value error while processing the current task {e}")
            logger.debug("Skipping current task")
            continue

        except Exception as e :
            logger.exception(f"got key error while processing the current task {e}")
            logger.debug("Skipping current task")
            continue
 
            

    #create the report
    logger.info("creating report for non remediated details for each tasks - Started")
    createReport(validatedTaskList=validatedTaskList,validatedTaskDict=validatedTaskDict)
    logger.info("creating report for non remediated details for each tasks - Done")

    #if ticket update is enabled then update the tickets in snow
    logger.info("checking Ticket_update is enabled or not in settings for invoke selenium - Started")
    if settings["Ticket_update"] :
        logger.debug("Ticket_update is enabled in the settings")

        logger.info("Invoking selenium to update the tickets in service now - Started")
        response: bool = updateTasksInSnow(validatedTaskDict)
        logger.info("Invoking selenium to update the tickets in service now - Done")

        logger.debug(f"response from updateTaskInSnow: {response}")
        if response :
            logger.info("tickets are updated successfully")
        else:
            logger.error("tickets are not updated sucessfully")
    else:
        logger.debug("Ticket_update is not enabled in the settings")

    logger.info("checking Ticket_update is enabled or not in settings for invoke selenium - Done")

    


    
    


    
if __name__ == "__main__" :
    logger.info("user invoked this script as main script")
    main()
