import os
import logging
from datetime import datetime
import pandas as pd
from handler import settings


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




def convert_csv_to_xlsx(file_path:str) -> dict :
    logger.info("convert_csv_to_xlsx function  - Started")

    excel_path = os.path.join( os.getcwd(),"Scheduled-Report-Cloud-Agent-Report-non_Superseded_New.xlsx" )

    columnList = ['IP', 'DNS', 'NetBIOS', 'QG Host ID', 'IP Interfaces', 'Tracking Method', 'OS', 'IP Status', 'QID', 'Title', 'Vuln Status', 'Type', 'Severity', 'Port', 'Protocol', 'FQDN', 'SSL', 'First Detected', 'Last Detected', 'Times Detected', 'Date Last Fixed', 'CVE ID', 'Vendor Reference', 'Bugtraq ID', 'CVSS', 'CVSS Base', 'CVSS Temporal', 'CVSS Environment', 'CVSS3.1', 'CVSS3.1 Base', 'CVSS3.1 Temporal', 'Threat', 'Impact', 'Solution', 'Exploitability', 'Results', 'PCI Vuln', 'Ticket State', 'Instance', 'OS CPE', 'Category', 'Associated Tags', 'QDS', 'ARS', 'ACS', 'TruRisk Score']

    logger.debug("Loading raw qualys report from specified path")
    df = pd.read_csv(file_path,header=None,delimiter=",",names=columnList,low_memory=False)

    logger.info("Finding the first valid header index from the dataframe - Started")
    index = df[df["DNS"] == "DNS"].index.tolist()[0]
    logger.info("Finding the first valid header from Raw dataframe - Done")

    #delete unneccesry rows
    logger.debug("droping the unwanted rows from dataframe")
    df.drop(df.index[0:index+1],axis=0,inplace=True)

    #convert csv to xlsx
    logger.info("Converting the dataframe to xlsx format - Started")
    df.to_excel(excel_path,sheet_name="Scheduled-Report-Cloud-Agent-Re",index=False)
    logger.info("Converting the dataframe to xlsx format - Done")

    print(f"{os.path.basename(excel_path)} converted successfully")

    logger.info("convert_csv_to_xlsx function  - Done")
    return {"status_code" : 0,"file_path" : excel_path}