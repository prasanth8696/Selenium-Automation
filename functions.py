import re
import os
from datetime import datetime
import pandas as pd
from pandas import DataFrame,Series


#Get the unique machine names from the ticket description
def getMachineList(descriptionString: str,searchPattern: str = r"wx[ev].*") -> list :

    totalMachinesString = re.findall(searchPattern,descriptionString)
    finalmachinesList = []
    [ finalmachinesList.extend(machineString.split(',')) for machineString in totalMachinesString ]
    #remove duplicate machines and return the machinelist as list
    return list(set(finalmachinesList))

#Get the unique QID lists from the ticket description
def getQIDList(descriptionString: str,searchPattern: str = r"QID[: ].*") -> list :

    totalQIDString = re.findall(searchPattern,descriptionString)
    finalQIDList = []
    #Extract the QID from the RAW string and convert QID as integer
    extractQIDLogicString = "list(map(int,QIDString.split(':')[-1].strip().split(',')))"
    [ finalQIDList.extend(eval(extractQIDLogicString)) for QIDString in totalQIDString ]

    #remove duplicate QID's and return the QIDList as list
    return list(set(finalQIDList))

def getNonRemediatedString(activeMachineDetails: DataFrame | Series) -> str :

    nonRemediatedString: str = "Non Remediated:\n\n"
    lastDetectedString: str = "\n\nLast Detected More Than 15 days\n\n"
    activeMachineDetails = activeMachineDetails.reset_index()
    for _,activeMachine in activeMachineDetails.iterrows() :
        
        #exclude if last detcted more than 15 days
        if activeMachine["Last Detected(In Days)"] <= 15 :
            if activeMachine["Last Detected(In Days)"] < 5 :
                nonRemediatedString += f"{activeMachine["NetBIOS"]} \n"
            else:
                nonRemediatedString += f"{activeMachine["NetBIOS"]} - last detected {activeMachine["Last Detected(In Days)"]} Days \n"

        else:
            lastDetectedString += f"{activeMachine["NetBIOS"]} - last detected {activeMachine["Last Detected(In Days)"]} Days- \n"

    return nonRemediatedString + lastDetectedString

    

def getNonRemediatedDetails(qulaysReport: DataFrame | Series ,computerList: DataFrame | Series,physical: bool = True)  ->  dict :

    nonRemediatedDetails = {}

    #Merge two dataframes to get the machine data
    mergeData: DataFrame | Series = qulaysReport.merge(computerList,how="left",left_on=qulaysReport["NetBIOS"].str.lower(),right_on=computerList["Name"].str.lower())

    #Add Last Detected(In Days) column in existing dataframe
    lamdaLogicString: str = 'abs((datetime.strptime(row["Last Detected"],r"%m/%d/%Y %H:%M:%S") - datetime.today()).days)'
    mergeData["Last Detected(In Days)"] = mergeData.apply(lambda row: eval(lamdaLogicString),axis=1 )

    #find in-service machines
    inserviceMachinesData: DataFrame | Series = mergeData[mergeData["CI Status"].isin(["In Service"])]

    #find in-stock machines 
    inStockMachinesData: DataFrame | Series = mergeData[mergeData["CI Status"].isin(["In Stock"])]

    #Get other CI status machines
    otherCIStatusMachinesData: DataFrame | Series = mergeData[~mergeData["CI Status"].isin(["In Service","In Stock"])]

    #Get more than 15days machines
    lastDetected15: DataFrame | Series = mergeData[mergeData["Last Detected(In Days)"] > 15]

    ## Add required values to nonRemediatedDetails dictionary
    nonRemediatedDetails["totalAssetCount"] = len(set(list(mergeData["DNS"])))
    nonRemediatedDetails["inServiceCount"] = len(set(list(inserviceMachinesData["DNS"])))
    nonRemediatedDetails["inStockCount"] = len(set(list(inStockMachinesData["DNS"])))
    nonRemediatedDetails["otherCIStatusCount"] = len(set(list(otherCIStatusMachinesData["DNS"])))
    nonRemediatedDetails["lastDetected15"] = len(set(list(lastDetected15["DNS"])))
    lastDetected15List: list = set(list(lastDetected15["DNS"]))
    if physical == True :
        totalMachinesData: DataFrame | Series = inserviceMachinesData  
        actualAssetData: DataFrame | Series = inserviceMachinesData[~inserviceMachinesData["DNS"].isin(lastDetected15List)]
        nonRemediatedDetails["actualAssetCount"] = len(set(list(actualAssetData["DNS"])))
    else :
        totalMachinesData: DataFrame | Series = pd.concat([inserviceMachinesData,inStockMachinesData],axis=0)
        actualAssetData: DataFrame | Series = totalMachinesData[~totalMachinesData["DNS"].isin(lastDetected15List)]
        nonRemediatedDetails["actualAssetCount"] = len(set(list(actualAssetData["DNS"])))
    
    #Remove Duplicates 
    #Get NonRemediatedString
    uniqueActiveMachines = (totalMachinesData[["DNS","NetBIOS","Last Detected(In Days)"]]).drop_duplicates("DNS")
    nonRemediatedDetails["nonRemediatedString"] = getNonRemediatedString(uniqueActiveMachines)

    return nonRemediatedDetails
    








