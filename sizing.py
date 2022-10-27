from asyncio.windows_events import NULL
from queue import Empty
import threading
import math
import pandas as pd
import warnings

def sizing( no_cores,
            storage_needed,
            smallestNoRacks=True,
            verbose=False,
            ignore_BaseSystem=True,
            use_DBServerExpansions=True,
            use_StorageExpansions=True
            ): #This function sizes the environment

    Requirements={
            "MaximumNumberOfOCPUs":no_cores,
            "TotalUsableDiskCapacity(TB)": storage_needed
        }

    Exadata_Configs=pd.read_csv("Exadata X9 Configurations.csv", sep=',').fillna(0)
    exadata_configs=Exadata_Configs.head(4)
    expansion_configs=Exadata_Configs.tail(2)

    StorageOCPURatio=float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["TotalUsableDiskCapacity(TB)"]/exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["MaximumNumberOfOCPUs"])
    print("StorageOCPURatio:",StorageOCPURatio)

    if ignore_BaseSystem:
        exadata_configs=exadata_configs[exadata_configs["Configuration"]!="Base system"]
    requirements=Requirements.copy()
    if verbose:
        print(requirements)

    evaluation=pd.DataFrame()
    evaluation["Configuration"]=list(exadata_configs["Configuration"])

    def evaluate(condition,value):
        conditionLine=[]
        for index,row in exadata_configs.iterrows():
            if row[condition]>0:
                if use_DBServerExpansions and use_StorageExpansions:
                    conditionLine.append(value/row[condition])
                elif not use_DBServerExpansions and condition=="MaximumNumberOfOCPUs":
                    conditionLine.append(math.ceil(value/row[condition]))
                elif not use_StorageExpansions and condition=="TotalUsableDiskCapacity(TB)":
                    conditionLine.append(math.ceil(value/row[condition]))
                else:
                    conditionLine.append(value/row[condition])
            else:
                conditionLine.append(0) 
        return(conditionLine)

    final_config=[]

    #Check the initial requirements
    while all(list(map(lambda item: item[1]>0, requirements.items()))):
        evaluation=pd.DataFrame()
        evaluation["Configuration"]=list(exadata_configs["Configuration"])

        for condition,value in requirements.items():
            evaluation[condition]=evaluate(condition,value)


        evaluation["Number"]=evaluation.apply(
            lambda row:
                row["MaximumNumberOfOCPUs"] if not use_DBServerExpansions and use_StorageExpansions else 
                row["TotalUsableDiskCapacity(TB)"] if not use_StorageExpansions and use_DBServerExpansions else
                math.floor(max(row[list(requirements.keys())])) if not use_DBServerExpansions and not use_StorageExpansions else 
                math.floor(min(row[list(requirements.keys())])) 
        ,axis=1)
        evaluation=evaluation.sort_values(by=["Number"])
        evaluation=evaluation[evaluation["Number"]>0]
        if verbose:
            print(evaluation)    # if needed we can print out how the sizing iteration works
        if evaluation.empty:
            break
        chosen=evaluation.iloc[0]
        for req in requirements:
            if requirements[req]>0:
                requirements[req]=requirements[req]-int(float(exadata_configs[exadata_configs["Configuration"]==chosen["Configuration"]][req].to_string(index=False)))*chosen["Number"]
    
        final_config.append({"Configuration":chosen["Configuration"],"Number":chosen["Number"]})
        del evaluation

    #Consolidate the racks
    configChanged=True
    while configChanged:
        configChanged=False
        for index in range(len(final_config)):
            if math.floor(int(float(final_config[index]["Number"]))/2)>0:  #if the number of racks can be divide by two
                current_index=exadata_configs[exadata_configs["Configuration"]==final_config[index]["Configuration"]].index.tolist()[0]
                if current_index<3:
                    if smallestNoRacks:
                        configChanged=True
                    final_config.append({"Configuration":exadata_configs.iloc[[current_index+1]]["Configuration"].to_string(index=False),"Number":math.floor(int(float(final_config[index]["Number"]))/2)})
                    if math.fmod(int(float(final_config[index]["Number"])),2)==0: #and if there is no remainder delete the original config
                        del final_config[index]
                    if index>0 and final_config[index]["Configuration"]==final_config[index-1]["Configuration"]:
                        final_config[index-1]["Number"]+=final_config[index]["Number"]
                        del final_config[index]
                        index=0
        

    #Check if there are extension possibilitites
    StorageExpansionPossibility=DBServerExpansionPossibility=0

    for config in final_config:
        StorageExpansionPossibility+=int(float(
            exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["AdditionalStorageCellPossibility"])
            *int(config["Number"]))
        DBServerExpansionPossibility+=(config["Number"]*8)-int(float(
            exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["NumberOfDatabaseServers"])
            *int(config["Number"]))

    # Calculate how many DB Server Extension would be needed
    NoCPUExpansions=NoStorageExpansions=0
    if requirements["MaximumNumberOfOCPUs"]>0:
        NoCPUExpansions=math.ceil(requirements["MaximumNumberOfOCPUs"]/int(float(expansion_configs[expansion_configs["Configuration"]=="DB Server Expansion"]["MaximumNumberOfOCPUs"])))
        if verbose:
            print("We need additional {} DB Server Expansions, and we have {} expansion possibilities in the Existing configurations".format(NoCPUExpansions,DBServerExpansionPossibility))

    #Calculate how many Storage Cell Extension needed 
    if requirements["TotalUsableDiskCapacity(TB)"]>0:
        NoStorageExpansions=math.ceil(
            requirements["TotalUsableDiskCapacity(TB)"]
            /int(float(expansion_configs[expansion_configs["Configuration"]=="Storage Expansion"]["TotalUsableDiskCapacity(TB)"])))
        if verbose:
            print("Additional {} Storage Expansions needed. We have {} extension possibilities in the current configuration".format(NoStorageExpansions,StorageExpansionPossibility))


    if NoStorageExpansions>StorageExpansionPossibility or NoCPUExpansions>DBServerExpansionPossibility:
        NoQRStorage=math.ceil((NoStorageExpansions-StorageExpansionPossibility)/(int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["AdditionalStorageCellPossibility"]))))
        NoQRCPU=math.ceil((NoCPUExpansions-DBServerExpansionPossibility)/(8-int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))))
        NoQR=max(NoQRStorage,NoQRCPU)
        if verbose:
            print("We need additional {} QRs with 3 existing and 9 Storage and 2 existing and 6 DB server extension possibilities each, to host the remaining {} Storage and {} DB Server Extensions".format(NoQR,max(0,NoStorageExpansions-StorageExpansionPossibility),max(0,NoCPUExpansions-DBServerExpansionPossibility)))
        final_config.append({"Configuration":"Quarter Rack","Number":NoQR})
        NoStorageExpansions=math.ceil(
            (requirements["TotalUsableDiskCapacity(TB)"]
            -int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["TotalUsableDiskCapacity(TB)"]))*NoQR)
            /int(float(expansion_configs[expansion_configs["Configuration"]=="Storage Expansion"]["TotalUsableDiskCapacity(TB)"])))
        NoCPUExpansions=math.ceil(
            (requirements["MaximumNumberOfOCPUs"]
            -int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["MaximumNumberOfOCPUs"]))*NoQR)
            /int(float(expansion_configs[expansion_configs["Configuration"]=="DB Server Expansion"]["MaximumNumberOfOCPUs"])))
    if NoStorageExpansions>0:   
        final_config.append({"Configuration":expansion_configs[expansion_configs["Configuration"]=="Storage Expansion"]["Configuration"].to_string(index=False),"Number":NoStorageExpansions})
    if NoCPUExpansions>0:
        final_config.append({"Configuration":expansion_configs[expansion_configs["Configuration"]=="DB Server Expansion"]["Configuration"].to_string(index=False),"Number":NoCPUExpansions})

    def sortingFunction(e):
        return e['Configuration']

    def sortByConfigSize(e):
        if e["Configuration"] in exadata_configs["Configuration"].to_list():
            return 3-exadata_configs[exadata_configs["Configuration"]==e["Configuration"]].index.to_list()[0]
        else:
            return expansion_configs[expansion_configs["Configuration"]==e["Configuration"]].index.to_list()[0]


    # Grouping the configurations together
    final_config.sort(key=sortingFunction)
    for index in range(len(final_config)-1):
        while index<len(final_config)-1 and final_config[index]["Configuration"]==final_config[index+1]["Configuration"]:
            final_config[index]["Number"]+=final_config[index+1]["Number"]
            del final_config[index+1]

    final_config.sort(key=sortByConfigSize)
    return(final_config)

no_cores=392
storage_needed=392/2


Exadata_Configs=pd.read_csv("Exadata X9 Configurations.csv", sep=',').fillna(0)
exadata_configs=Exadata_Configs.head(4)
expansion_configs=Exadata_Configs.tail(2)
exadata_prices=pd.read_csv("ExaCC pricing.csv", sep=',').fillna(0)

final_config=sizing(    no_cores,
                        storage_needed,
                        smallestNoRacks=True,
                        ignore_BaseSystem=True,
                        verbose=True,
                        use_DBServerExpansions=True,
                        use_StorageExpansions=False)

# print the final configuration grouped
print("{:<20}{:<5}{:<5}{:<5}".format("Configuration","Number","CPU","Storage"))
print("-"*50)
totalCPU=0
totalStorage=0
totalNumber=0
totalCost=0
for config in final_config:
    if("Expansion" not in config["Configuration"]):
        CPUSize=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["MaximumNumberOfOCPUs"])*int(config["Number"]))
        StorageSize=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["TotalUsableDiskCapacity(TB)"])*int(config["Number"]))
    else:
        CPUSize=int(float(expansion_configs[expansion_configs["Configuration"]==config["Configuration"]]["MaximumNumberOfOCPUs"])*int(config["Number"]))
        StorageSize=int(float(expansion_configs[expansion_configs["Configuration"]==config["Configuration"]]["TotalUsableDiskCapacity(TB)"])*int(config["Number"]))

    print("{:<20}{:>5}{:>5}{:>5}".format(
    config["Configuration"],
    config["Number"],
    CPUSize,
    StorageSize
    ))
    totalNumber+=int(config["Number"])
    totalCPU+=CPUSize
    totalStorage+=StorageSize
    totalCost+=int(exadata_prices[exadata_prices["Configuration"]== config["Configuration"]]["Price"])*int(config["Number"])


print("-"*50)
print("Total:{:>20}{:>5}{:>5}".format(totalNumber,totalCPU,totalStorage))
print("Requirements:{:>18}{:>5.0f}".format(no_cores,storage_needed))
print("Total Monthly Cost: ${:,.0f}".format(totalCost))


