#Declare sample schemas here


#Task Details Schema
#set possible to close as true ,if no machine details i will go to else part
taskSchema: dict = {
    "Sys_ID" : "",
    "Number": "",
    "Vulnerablity Name": "",
    "task State": "",
    "Assigned To": "",
    "Assignment Group": "",
    "QID List": [],
    "Physical": False,
    "Total Asset Count ": 0,
    "In Service Count ": 0,
    "In Stock Count": 0,
    "Other CI Status Count": 0,
    "Last Detected Count(15days)": 0,
    "Actual Asset Count": 0,
    "Possible to Close": True,
    "Aging Ticket": False,
    "Total Task Days": 0,
    "vulnerablityDetails": {"rootCause": "","solution": "","fixedDeployed": ""},
    "Non-Remediated String": ""
    }