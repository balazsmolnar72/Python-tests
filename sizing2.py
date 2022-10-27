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
            use_StorageExpansions=True): #This function sizes the environment

    Requirements={
            "MaximumNumberOfOCPUs":no_cores,
            "TotalUsableDiskCapacity(TB)": storage_needed
        }

    Exadata_Configs=pd.read_csv("Exadata X9 Configurations.csv", sep=',').fillna(0)
    exadata_configs_origin=Exadata_Configs.head(4)
    exadata_configs=exadata_configs_origin.sort_values(by=["NumberOfDatabaseServers"],ascending=False)
    del exadata_configs_origin
    expansion_configs=Exadata_Configs.tail(2)

    StorageOCPURatio=float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["TotalUsableDiskCapacity(TB)"]/exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["MaximumNumberOfOCPUs"])
    DBServerCPUSize=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["MaximumNumberOfOCPUs"]/exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
    StorageServerSize=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["TotalUsableDiskCapacity(TB)"]/exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
    MaxNoStorageServersInRack=int(float(exadata_configs[exadata_configs["Configuration"]=="Full Rack"]["NumberOfStorageServers"]))
    MaxNoDBServersInRack=int(float(exadata_configs[exadata_configs["Configuration"]=="Full Rack"]["NumberOfDatabaseServers"]))

    if ignore_BaseSystem:
        exadata_configs=exadata_configs[exadata_configs["Configuration"]!="Base system"]
        SmallestConfig="Quarter Rack"
    else:
        SmallestConfig="Base system"
    requirements=Requirements.copy()
    if verbose:
        print(requirements)
    
    NoDBServers=math.ceil(requirements["MaximumNumberOfOCPUs"]/DBServerCPUSize)
    NoStorageServers=math.ceil(requirements["TotalUsableDiskCapacity(TB)"]/StorageServerSize)

    final_config=[]

    if use_DBServerExpansions and use_StorageExpansions:
        if requirements["TotalUsableDiskCapacity(TB)"]/requirements["MaximumNumberOfOCPUs"]>StorageOCPURatio: #The configuration is storage heavy
            NoRacks=math.ceil(NoStorageServers/MaxNoStorageServersInRack)
            for item in range(NoRacks):
                if NoDBServers<2:
                    final_config.append({"Configuration":"Quarter Rack","Number":1})
                    NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
                    NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
                    continue
                for index,config in exadata_configs.iterrows():
                    if int(float(config["NumberOfDatabaseServers"])) <= NoDBServers:
                        final_config.append({"Configuration":config["Configuration"],"Number":1})
                        NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                        NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                        break
        else:
            NoRacks=math.ceil(NoDBServers/MaxNoDBServersInRack)
            for item in range(NoRacks):
                if NoStorageServers<2:
                    final_config.append({"Configuration":"Quarter Rack","Number":1})
                    NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
                    NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
                    continue
                for index,config in exadata_configs.iterrows():
                    if int(float(config["NumberOfStorageServers"])) <= NoStorageServers:
                        final_config.append({"Configuration":config["Configuration"],"Number":1})
                        NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                        NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                        break
    elif not use_DBServerExpansions and use_StorageExpansions: # you can use the Storage, but not the DB Server
        NoRacks=math.ceil(NoStorageServers/MaxNoStorageServersInRack)
        while NoDBServers>0 or NoRacks>0:
            if NoDBServers>int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))*NoRacks:
                for index,config in exadata_configs.iterrows():
                    if int(float(config["NumberOfDatabaseServers"])) <= NoDBServers:
                        final_config.append({"Configuration":config["Configuration"],"Number":1})
                        NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                        NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                        NoRacks-=1
                        break
            else:
                    final_config.append({"Configuration":"Quarter Rack","Number":1})
                    NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
                    NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
                    NoRacks-=1
            if NoDBServers<2:
                final_config.append({"Configuration":SmallestConfig,"Number":1})
                NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfStorageServers"]))
                NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfDatabaseServers"]))
                NoRacks-=1

    elif not use_StorageExpansions and use_DBServerExpansions: #You can use DB Server but not the storage
        NoRacks=math.ceil(NoDBServers/MaxNoDBServersInRack)
        while NoStorageServers>0 or NoRacks>0:
            if NoStorageServers>int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))*NoRacks:
                for index,config in exadata_configs.iterrows():
                    if int(float(config["NumberOfStorageServers"])) <= NoStorageServers:
                        final_config.append({"Configuration":config["Configuration"],"Number":1})
                        NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                        NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                        NoRacks-=1
                        break
            else:
                    final_config.append({"Configuration":"Quarter Rack","Number":1})
                    NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
                    NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
                    NoRacks-=1
            if NoStorageServers<3:
                final_config.append({"Configuration":SmallestConfig,"Number":1})
                NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfStorageServers"]))
                NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfDatabaseServers"]))
                NoRacks-=1

                    
    else:
        while NoStorageServers>0 or NoDBServers>0:
            if (NoStorageServers<3 and NoDBServers<=0) or (NoDBServers<2 and NoStorageServers<=0):
                final_config.append({"Configuration":SmallestConfig,"Number":1})
                NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfStorageServers"]))
                NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfDatabaseServers"]))
                continue
            for index,config in exadata_configs.iterrows():
                if int(float(config["NumberOfDatabaseServers"])) <= NoStorageServers or int(float(config["NumberOfDatabaseServers"])) <= NoDBServers:
                    final_config.append({"Configuration":config["Configuration"],"Number":1})
                    NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                    NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                    break
    if NoDBServers>0:
        final_config.append({"Configuration":"DB Server Expansion","Number":NoDBServers})
    if NoStorageServers>0:
        final_config.append({"Configuration":"Storage Expansion","Number":NoStorageServers})
    
    final_config=sorted(final_config, key=lambda val: val["Configuration"])
    for index in range(len(final_config)-1):
        while index<len(final_config)-1 and final_config[index]["Configuration"]==final_config[index+1]["Configuration"]:
            final_config[index]["Number"]+=final_config[index+1]["Number"]
            del final_config[index+1]
    
    def sortByConfigSize(e):
            if e["Configuration"] in exadata_configs["Configuration"].to_list():
                return 3-exadata_configs[exadata_configs["Configuration"]==e["Configuration"]].index.to_list()[0]
            else:
                return expansion_configs[expansion_configs["Configuration"]==e["Configuration"]].index.to_list()[0]
    final_config.sort(key=sortByConfigSize)
    return final_config

 
no_cores=650
storage_needed=650*1.5


Exadata_Configs=pd.read_csv("Exadata X9 Configurations.csv", sep=',').fillna(0)
exadata_configs=Exadata_Configs.head(4)
expansion_configs=Exadata_Configs.tail(2)
exadata_prices=pd.read_csv("ExaCC pricing.csv", sep=',').fillna(0)
MaxNoDBServersInRack=int(float(exadata_configs[exadata_configs["Configuration"]=="Full Rack"]["NumberOfDatabaseServers"]))


final_config=sizing(    no_cores,
                        storage_needed,
                        smallestNoRacks=True,
                        ignore_BaseSystem=True,
                        verbose=False,
                        use_DBServerExpansions=False,
                        use_StorageExpansions=True)

# print the final configuration grouped
print("{:<20}{:<5}{:<5}{:<5}".format("Configuration","Number","CPU","Storage"))
print("-"*50)
totalCPU=0
totalStorage=0
totalNumber=0
totalCost=0
freeStorageExpansion=freeDBServerExpansion=0
for config in final_config:
    if("Expansion" not in config["Configuration"]):
        CPUSize=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["MaximumNumberOfOCPUs"])*int(config["Number"]))
        StorageSize=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["TotalUsableDiskCapacity(TB)"])*int(config["Number"]))
        freeStorageExpansion+=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["AdditionalStorageCellPossibility"])*int(config["Number"]))
        freeDBServerExpansion+=int(float(MaxNoDBServersInRack-exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["NumberOfDatabaseServers"])*int(config["Number"]))
    else:
        CPUSize=int(float(expansion_configs[expansion_configs["Configuration"]==config["Configuration"]]["MaximumNumberOfOCPUs"])*int(config["Number"]))
        StorageSize=int(float(expansion_configs[expansion_configs["Configuration"]==config["Configuration"]]["TotalUsableDiskCapacity(TB)"])*int(config["Number"]))
        if "Storage" in config["Configuration"]:
            freeStorageExpansion-=config["Number"]
        else:
            freeDBServerExpansion=-config["Number"]

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
print("{} Storage and {} DB Server expansion possibilities are free".format(freeStorageExpansion,freeDBServerExpansion))


