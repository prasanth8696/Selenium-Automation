import os
import pandas as pd


def convert_csv_to_xlsx(file_path:str) -> dict :

    excel_path = os.path.join( os.getcwd(),"Scheduled-Report-Cloud-Agent-Report-non_Superseded_New.xlsx" )

    columnList = ['IP', 'DNS', 'NetBIOS', 'QG Host ID', 'IP Interfaces', 'Tracking Method', 'OS', 'IP Status', 'QID', 'Title', 'Vuln Status', 'Type', 'Severity', 'Port', 'Protocol', 'FQDN', 'SSL', 'First Detected', 'Last Detected', 'Times Detected', 'Date Last Fixed', 'CVE ID', 'Vendor Reference', 'Bugtraq ID', 'CVSS', 'CVSS Base', 'CVSS Temporal', 'CVSS Environment', 'CVSS3.1', 'CVSS3.1 Base', 'CVSS3.1 Temporal', 'Threat', 'Impact', 'Solution', 'Exploitability', 'Results', 'PCI Vuln', 'Ticket State', 'Instance', 'OS CPE', 'Category', 'Associated Tags', 'QDS', 'ARS', 'ACS', 'TruRisk Score']


    df = pd.read_csv(file_path,header=None,delimiter=",",names=columnList,low_memory=False)

    index = df[df["DNS"] == "DNS"].index.tolist()[0]

    #delete unneccesry rows
    df.drop(df.index[0:index+1],axis=0,inplace=True)

    #convert csv to xlsx
    df.to_excel(excel_path,sheet_name="Scheduled-Report-Cloud-Agent-Re",index=False)

    print(f"{os.path.basename(excel_path)} converted successfully")

    return {"status_code" : 0,"file_path" : excel_path}