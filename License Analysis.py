import threading
import math
import pandas as pd
import warnings
import ExaSizing as sizer


# Read the available database options into a dataframe
db_options=pd.read_csv("Database Options.csv", sep=',')
# Read the installed base into a dataframe with a ',' separator
df = pd.read_csv("Install Base.csv", sep=',')
if "Install Status" in df.columns:
    df=df[df["Install Status"]=="ACTIVE"]

# Describe Show the number of customers in this analysis
no_customers=df["Customer Name"].unique().__len__()
print("This analysis contains information about {} customers".format(no_customers))
print(df["Customer Name"].unique() if no_customers<10 else "") # Only lists if the number of customers are less than 10

#Calculate the license type based on the Product description 
df["License type"] = df.apply(
    lambda row:
        "Processor" if row["Product Description"].find("Processor") > 0
        else "NUP" if row["Product Description"].find("Named") > 0
        else "Unknown", axis=1)

# Sum up the amount of licenses and the ARR which has the same name and license type

licenses=df[["Product Name", "Quantity", "Contract ARR","License type"]][df["License type"] != "Unknown"].groupby(
    ["Product Name","License type"], as_index=False)[["Quantity", "Contract ARR"]].sum()

#Select the licenses which are database options, meaning that the keywords listed in the db_options
#is part of the license name. The DB Option field will also indicate which license it is in the db_option
#dataframe by index of the license entry

licenses["DB_Option"]=licenses.apply(
    lambda row: pd.Series(list(map(
        lambda option,no:
            no if option in row["Product Name"] else -1, db_options["Keyword"], range(db_options.__len__())
        ))).max(),
    axis=1)

#If the license is a DB option, we can extract the list price of CPU and NUP license from the db_option dataframe
#Based on the license type we can fill up the List price column with the proper type of list price.

licenses["List Price CPU"]=licenses.apply(
    lambda row:
        db_options["List Price CPU"][row["DB_Option"]] if row["DB_Option"]>0 else 0,
    axis=1)

licenses["List Price NUP"]=licenses.apply(
    lambda row:
        db_options["List Price NUP"][row["DB_Option"]] if row["DB_Option"]>0 
        else 0,
    axis=1)

licenses["License Name"]=licenses.apply(
    lambda row:
        db_options["License name"][row["DB_Option"]] if row["DB_Option"]>0
        else "Not a DB License",
    axis=1)

licenses["List Price"]=licenses.apply(
    lambda row:
        row["List Price CPU"] if row["License type"] == "Processor" else
        row["List Price NUP"] if row["License type"] == "NUP" else
        1,
    axis=1)

#The average discount can be calculated based on the ratio of the ARR/Quantity and the list price of the license type

licenses["Average Discount"]=licenses.apply(
    lambda row:
        (row["Contract ARR"]/row["Quantity"])/row["List Price"]-1 if row["List Price"]>1 else 0,
    axis=1)
licenses["Total Intel Cores Covered"]=licenses.apply(
    lambda row:
        row["Quantity"]/0.5 if row["License type"] == "Processor" else
        math.floor(row["Quantity"]/0.5/25) if row["License type"] == "NUP" and row["DB_Option"]!=0 else
        math.floor(row["Quantity"]/0.5/10) if row["License type"] ==" NUP" and row["DB_Option"]==0 else
        0
    ,axis=1)

# We create a new dataframe called license_printable from licenses, just to do the right ouptut formatting.

licenses_printable=licenses[licenses["DB_Option"]>0]
warnings.filterwarnings('ignore')
licenses_printable["Contract ARR"]=licenses_printable["Contract ARR"].map('${:,.0f}'.format)
licenses_printable["Average Discount"]=licenses_printable["Average Discount"].map('{:+.0%}'.format)
warnings.filterwarnings('default')

print("\n","-"*30," Summary of License Costs ","-"*30) 
print(licenses_printable[["Product Name","License type","Quantity","Contract ARR","Average Discount"]].to_string(index=False))
print('-'*100)
print("Total:{:>64,.0f}{:>13,.0f}{:+17.0%}".format(
    licenses[licenses["DB_Option"]>0]["Quantity"].max(),
    licenses[licenses["DB_Option"]>0]["Contract ARR"].sum(),
    licenses[licenses["DB_Option"]>0].apply(        # this calculates the weighted average. Weight is based on the ARR value
         lambda row:
             row["Contract ARR"]*row["Average Discount"]
          ,axis=1).sum()/licenses["Contract ARR"][licenses["DB_Option"]>0].sum()    
    )   
)


del licenses_printable

# And we will calculate the total cores covered and what is the coverage of the different DB options 
# compared to the Enterprise edition

cores_chart=licenses[licenses["DB_Option"]>0].pivot("Product Name","License type","Total Intel Cores Covered").fillna(0)
if "NUP" not in cores_chart.columns:
    cores_chart["NUP"]=0
if "Processor" not in cores_chart.columns:
    cores_chart["Processor"]=0
cores_chart["Total Intel cores"]=cores_chart.apply(
    lambda row:
        row["Processor"]+row["NUP"]
        ,axis=1
)
max_cores_supported=cores_chart["Total Intel cores"].max()
cores_chart["Percent"]=cores_chart.apply(
    lambda row:
        row["Total Intel cores"]/max_cores_supported,
        axis=1
)



warnings.filterwarnings('ignore')
cores_chart_printable=cores_chart.sort_values(by=["Percent"], ascending=False)
cores_chart_printable["NUP"]=cores_chart_printable["NUP"].map('{:,.0f}'.format)
cores_chart_printable["Processor"]=cores_chart_printable["Processor"].map('{:,.0f}'.format)
cores_chart_printable["Total Intel cores"]=cores_chart_printable["Total Intel cores"].map('{:,.0f}'.format)
cores_chart_printable["Percent"]=cores_chart_printable["Percent"].map('{:.0%}'.format)
warnings.filterwarnings('default')

print("\n","-"*30," Summary of Licenses ","-"*30) 
print(cores_chart_printable)

#Check if the customer has ULA

df["DB_Option"]=df.apply(
    lambda row: pd.Series(list(map(
        lambda option,no:
            no if option in row["Product Name"] else -1, db_options["Keyword"], range(db_options.__len__())
        ))).max(),
    axis=1)

df["Discount"]=df.apply(
    lambda row:
        (row["Contract ARR"]/row["Quantity"])/
            ( db_options["List Price CPU"][row["DB_Option"]])-1
        if (row["DB_Option"]>0 and row["License type"]=="Processor") else
        (row["Contract ARR"]/row["Quantity"])/
            ( db_options["List Price NUP"][row["DB_Option"]])-1
        if (row["DB_Option"]>0 and row["License type"]=="NUP") else
        0       
,axis=1)

ula_licenses=df[["Customer Name","Product Name"]][(df["Discount"]>0) & (df["Quantity"]==1)]
if ula_licenses.__len__()>0:
    print("\n","-"*30," ULA Information ","-"*30) 
    print("These customers has probably a ULA on these Licenses:")
    print(ula_licenses.to_string(index=False))

#Sizing the environment
print("\n","-"*30," Possible Exa target For The complete workload ","-"*30) 
print("\nTarget Sizing for this installation:")
result=sizer.sizing(
    no_cores=max_cores_supported,
    storage_needed=max_cores_supported*2,
    use_DBServerExpansions=False)
print("{:<20}{:<10}{:<9}{:<5}\t{}".format("Configuration","Number","CPU","Storage","Monthly Cost"))
print(*list(map(lambda config: "{:<20}{:>5}{:>10,.0f}{:>10,.0f}\t${:,.0f}".format(
    config["Configuration"],
    config["Number"],
    config["CPUSize"],
    config["StorageSize"],
    config["Cost"]
    ),result)),sep='\n')
print("-"*60)
print("{:<20}{:>5}{:>10,.0f}{:>10,.0f}\t${:,.0f}".format(
    "Total:",
    sum(config["Number"] for config in result),
    sum(config["CPUSize"] for config in result),
    sum(config["StorageSize"] for config in result),
    sum(config["Cost"] for config in result)
    ))

print("Total Annual Infrastructure cost: ${:,.0f}".format(sum(config["Cost"] for config in result)*12))