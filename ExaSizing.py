#from asyncio.windows_events import NULL
from queue import Empty
import math
import pandas as pd

# This function sizes the environment
# Returns a list of dictionaries which shows the number of the configurations needed to cover the requirements

def sizing( no_cores,
            storage_needed,
            Exa_Core_Ratio=1,
            verbose=False,
            ignore_BaseSystem=True,
            use_DBServerExpansions=True,
            use_StorageExpansions=True): 

    no_cores=math.ceil(no_cores/Exa_Core_Ratio)
    Requirements={
            "MaximumNumberOfOCPUs":no_cores,
            "TotalUsableDiskCapacity(TB)": storage_needed
        }

    Exadata_Configs=pd.read_csv("Exadata X9 Configurations.csv", sep=',').fillna(0)
    exadata_configs_origin=Exadata_Configs.head(4)
    exadata_configs=exadata_configs_origin.sort_values(by=["NumberOfDatabaseServers"],ascending=False) #Sort Largest configuration first
    del exadata_configs_origin
    # Expansion configs are the last two lines
    expansion_configs=Exadata_Configs.tail(2)

    exadata_prices=pd.read_csv("ExaCC pricing.csv", sep=',').fillna(0)

    # Set some constants
    StorageOCPURatio=float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["TotalUsableDiskCapacity(TB)"]/exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["MaximumNumberOfOCPUs"])
    DBServerCPUSize=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["MaximumNumberOfOCPUs"]/exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
    StorageServerSize=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["TotalUsableDiskCapacity(TB)"]/exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
    MaxNoStorageServersInRack=int(float(exadata_configs[exadata_configs["Configuration"]=="Full Rack"]["NumberOfStorageServers"]))
    MaxNoDBServersInRack=int(float(exadata_configs[exadata_configs["Configuration"]=="Full Rack"]["NumberOfDatabaseServers"]))

    #Adjust the smallest configuration based on preference (not every environment supports Base Racks)
    if ignore_BaseSystem:
        exadata_configs=exadata_configs[exadata_configs["Configuration"]!="Base system"]
        SmallestConfig="Quarter Rack"
    else:
        SmallestConfig="Base system"

    #Makes a copy of the original requirements to enable later reduction of requirements
    requirements=Requirements.copy()

    if verbose:
        print(requirements)
    
    #Calculating how many Servers are needed and which kind this sizing only takes CPU and Storage requirements into consideration
    # This is the place to enhance this further to support other parameters as well
    NoDBServers=math.ceil(requirements["MaximumNumberOfOCPUs"]/DBServerCPUSize)
    NoStorageServers=math.ceil(requirements["TotalUsableDiskCapacity(TB)"]/StorageServerSize)

    #initiate the final configuration with an emty list 
    final_config=[]

    # Different sizing methods based on differnent paramaters 
    if use_DBServerExpansions and use_StorageExpansions: # If both Storage and Database extensions are allowed
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
        else: #The configuration is CPU heavy
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
        NoRacks=math.ceil(NoStorageServers/MaxNoStorageServersInRack) # Need to calculate how many QRs are needed at least to host all the storage servers
        while NoDBServers>0 or NoRacks>0: 
            if NoDBServers>int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))*NoRacks: #Some of those QRs can be converted to larger configs if we need DB Servers, but only if the required DB servers are more than the Sum of QRs which are needed for Storage expansion anyway
                for index,config in exadata_configs.iterrows():
                    if int(float(config["NumberOfDatabaseServers"])) <= NoDBServers:
                        final_config.append({"Configuration":config["Configuration"],"Number":1})
                        NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                        NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                        NoRacks-=1
                        break
            else: #If we do not need more DB Servers, but we do not have enough expansion capacities we add QRs
                    final_config.append({"Configuration":"Quarter Rack","Number":1})
                    NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
                    NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
                    NoRacks-=1
            if NoDBServers<2: # if we need less than the smallest configuration we add the smallest configuration, since we cannot use DB Server Expansion
                final_config.append({"Configuration":SmallestConfig,"Number":1})
                NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfStorageServers"]))
                NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfDatabaseServers"]))
                NoRacks-=1

    elif not use_StorageExpansions and use_DBServerExpansions: #You can use DB Server expansion but not the storage server expansion
        NoRacks=math.ceil(NoDBServers/MaxNoDBServersInRack) # Calculate how many QRs are needed to host the DB Servers
        while NoStorageServers>0 or NoRacks>0:
            if NoStorageServers>int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))*NoRacks: # If we need more storage than what we would have because of the DB Servers
                for index,config in exadata_configs.iterrows(): # We can upgrade the QRs to larger configurations if we need them because of storage
                    if int(float(config["NumberOfStorageServers"])) <= NoStorageServers:
                        final_config.append({"Configuration":config["Configuration"],"Number":1})
                        NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                        NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                        NoRacks-=1
                        break
            else: # If we do not need more storage then we'll add just QRs to be able to host the DB Server Expansions
                    final_config.append({"Configuration":"Quarter Rack","Number":1})
                    NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfStorageServers"]))
                    NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]=="Quarter Rack"]["NumberOfDatabaseServers"]))
                    NoRacks-=1
            if NoStorageServers<3: # If we need less storage than the minimum configuration we add the minimum configuration
                final_config.append({"Configuration":SmallestConfig,"Number":1})
                NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfStorageServers"]))
                NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfDatabaseServers"]))
                NoRacks-=1

                    
    else: # If we cannot use neighter Storage nor DB Server expansion
        while NoStorageServers>0 or NoDBServers>0:
            if (NoStorageServers<3 and NoDBServers<=0) or (NoDBServers<2 and NoStorageServers<=0): # If we need less than the minimum config we add the minimum config
                final_config.append({"Configuration":SmallestConfig,"Number":1})
                NoStorageServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfStorageServers"]))
                NoDBServers-=int(float(exadata_configs[exadata_configs["Configuration"]==SmallestConfig]["NumberOfDatabaseServers"]))
                continue
            for index,config in exadata_configs.iterrows(): # find the best fit for the requirement
                if int(float(config["NumberOfDatabaseServers"])) <= NoStorageServers or int(float(config["NumberOfDatabaseServers"])) <= NoDBServers:
                    final_config.append({"Configuration":config["Configuration"],"Number":1})
                    NoStorageServers-=int(float(config["NumberOfStorageServers"]))
                    NoDBServers-=int(float(config["NumberOfDatabaseServers"]))
                    break
    if NoDBServers>0: # add the remaining DB Server Expansions 
        final_config.append({"Configuration":"DB Server Expansion","Number":NoDBServers})
    if NoStorageServers>0: # add the remaining Storage Server Expansions 
        final_config.append({"Configuration":"Storage Expansion","Number":NoStorageServers})
    
    # Let's consolidate the result and group the same configurations together

    final_config=sorted(final_config, key=lambda val: val["Configuration"])
    for index in range(len(final_config)-1):
        while index<len(final_config)-1 and final_config[index]["Configuration"]==final_config[index+1]["Configuration"]:
            final_config[index]["Number"]+=final_config[index+1]["Number"]
            del final_config[index+1]
    
    # Now we have the sizing. Let's sort it and add some useful parameters to the list
    def sortByConfigSize(e):
            if e["Configuration"] in exadata_configs["Configuration"].to_list():
                return 3-exadata_configs[exadata_configs["Configuration"]==e["Configuration"]].index.to_list()[0]
            else:
                return expansion_configs[expansion_configs["Configuration"]==e["Configuration"]].index.to_list()[0]

    final_config.sort(key=sortByConfigSize)
    for config in final_config:
        if("Expansion" not in config["Configuration"]):
            config["CPUSize"]=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["MaximumNumberOfOCPUs"])*int(config["Number"]))
            config["StorageSize"]=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["TotalUsableDiskCapacity(TB)"])*int(config["Number"]))
            config["freeStorageExpansion"]=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["AdditionalStorageCellPossibility"])*int(config["Number"]))
            config["freeDBServerExpansion"]=int(float(MaxNoDBServersInRack-exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["NumberOfDatabaseServers"])*int(config["Number"]))
        else:
            config["CPUSize"]=int(float(expansion_configs[expansion_configs["Configuration"]==config["Configuration"]]["MaximumNumberOfOCPUs"])*int(config["Number"]))
            config["StorageSize"]=int(float(expansion_configs[expansion_configs["Configuration"]==config["Configuration"]]["TotalUsableDiskCapacity(TB)"])*int(config["Number"]))
        config["Cost"]=int(exadata_prices[exadata_prices["Configuration"]== config["Configuration"]]["Price"])*int(config["Number"])
    return final_config #return the result 

 
# no_cores=650
# storage_needed=650*1.5

# Exadata_Configs=pd.read_csv("Exadata X9 Configurations.csv", sep=',').fillna(0)
# exadata_configs=Exadata_Configs.head(4)
# expansion_configs=Exadata_Configs.tail(2)
# exadata_prices=pd.read_csv("ExaCC pricing.csv", sep=',').fillna(0)
# MaxNoDBServersInRack=int(float(exadata_configs[exadata_configs["Configuration"]=="Full Rack"]["NumberOfDatabaseServers"]))


# final_config=sizing(    no_cores,
#                         storage_needed,
#                         ignore_BaseSystem=True,
#                         verbose=False,
#                         use_DBServerExpansions=False,
#                         use_StorageExpansions=True)


# print("{:<20}{:<5}{:<5}{:<5}\t{}".format("Configuration","Number","CPU","Storage","Monthly Cost"))
# print("-"*50)
# totalCPU=totalStorage=totalNumber=totalCost=freeStorageExpansion=freeDBServerExpansion=0 #initalize counters
# for config in final_config:
#     if("Expansion" not in config["Configuration"]):
#         freeStorageExpansion+=int(float(exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["AdditionalStorageCellPossibility"])*int(config["Number"]))
#         freeDBServerExpansion+=int(float(MaxNoDBServersInRack-exadata_configs[exadata_configs["Configuration"]==config["Configuration"]]["NumberOfDatabaseServers"])*int(config["Number"]))
#     else:
#         if "Storage" in config["Configuration"]:
#             freeStorageExpansion-=config["Number"]
#         else:
#             freeDBServerExpansion=-config["Number"]

#     print("{:<20}{:>5}{:>5}{:>5}\t${:,.0f}".format(
#     config["Configuration"],
#     config["Number"],
#     config["CPUSize"],
#     config["StorageSize"],
#     config["Cost"]
#     ))
#     totalNumber+=int(config["Number"])
#     totalCPU+=int(config["CPUSize"])
#     totalStorage+=int(config["StorageSize"])
#     totalCost+=int(config["Cost"])

# print("-"*50)
# print("Total:{:>20}{:>5}{:>5}\t${:,.0f}".format(totalNumber,totalCPU,totalStorage,totalCost))
# print("Requirements:{:>18}{:>5.0f}".format(no_cores,storage_needed))
# print("{} Storage and {} DB Server expansion possibilities are free".format(freeStorageExpansion,freeDBServerExpansion))


