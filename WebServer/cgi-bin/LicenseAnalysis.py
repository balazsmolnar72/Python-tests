import math
import pandas as pd
import warnings
import ExaSizing as sizer

warnings.filterwarnings('ignore')
global max_cores_supported
global totalSupportPaid


# Read the available database options into a dataframe
db_options=pd.read_csv("Database Options.csv", sep=',',encoding='utf8', engine='python')
# Read the installed base into a dataframe with a ',' separator chech if all fields/Information is present
possible_fields=['Customer Name', 'Product Name','Product Description','Quantity','Contract ARR', 'Contract ARR (CD)','Metric', 'Install Status']

try:
    df = pd.read_csv("Install Base.csv", sep=',', usecols=lambda x: x in possible_fields)
except Exception as e:
    print(e)
    print('Csv format is not valid.')
    exit()

current_columns=list(df.columns)

if 'Contract ARR (CD)' in current_columns:
    df=df.rename(columns={"Contract ARR (CD)": "Contract ARR", "B": "c"})
if 'Product Description' not in current_columns and 'Metric' not in current_columns:
    exit('Missing mandatory field')
if 'Product Description' not in current_columns and 'Metric' in current_columns:
    df['Product Description']=df['Product Name']+" - "+df['Metric']
if 'Product Name' not in current_columns and 'Product Description' in current_columns:
    df['Product Name']=df['Product Description'].map(lambda s: s[:s.find(' -')] if s.find(' -')>-1 else "")
    current_columns=list(df.columns)

if 'Customer Name' not in current_columns or 'Product Name' not in current_columns:
    exit('Missing mandatory field')

if "Install Status" in df.columns: # Check if there is an install status field in the file, if yes, only the active status is valid
    df=df[df["Install Status"]=="ACTIVE"]

def printNoCustomers(style='txt'):# Describe Show the number of customers in this analysis
    no_customers=df["Customer Name"].unique().__len__()
    print("This analysis contains information about {} customers:".format(no_customers))
    if style=='txt':
        print(df["Customer Name"].unique() if no_customers<10 else "") # Only lists if the number of customers are less than 10
    if style=='html':
        print("<br>")
        if no_customers==1:
            print("<b>")
        print("<br>".join((df["Customer Name"].unique() if no_customers<10 else ""))) # Only lists if the number of customers are less than 10
        if no_customers==1:
            print("</b>")       
    return no_customers

def getMostSignificantCustomerName(): #Returns the customer name where most of the lines belong to 
    listOfCustomers=df[["Customer Name", "Contract ARR"]].groupby(["Customer Name"], as_index=False)["Contract ARR"].sum()
    return (listOfCustomers.sort_values('Contract ARR', ascending=False).iloc[:1]['Customer Name'].to_string(index=False))

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



def printLicenseCosts(style='txt'):    # We create a new dataframe called license_printable from licenses, just to do the right ouptut formatting.

    licenses_printable=licenses[licenses["DB_Option"]>0]
    warnings.filterwarnings('ignore')
    if style=='html':
        licenses_printable=licenses_printable.append(
                {
                    "Product Name":"Total",
                    "License type":"",
                    "Quantity":"",
                    "Contract ARR":totalSupportPaid,
                    "Average Discount":licenses[licenses["DB_Option"]>0].apply(        # this calculates the weighted average. Weight is based on the ARR value
                        lambda row:
                            row["Contract ARR"]*row["Average Discount"]
                        ,axis=1).sum()/licenses["Contract ARR"][licenses["DB_Option"]>0].sum() 
                }
            ,ignore_index="true")

    licenses_printable["Contract ARR"]=licenses_printable["Contract ARR"].map('${:,.0f}'.format)
    licenses_printable["Average Discount"]=licenses_printable["Average Discount"].map('{:+.0%}'.format)

    if style=='html':
        print(
            licenses_printable[["Product Name","License type","Quantity","Contract ARR","Average Discount"]].to_html(index=False,classes="licenses_table_style")
            .replace('<tr>\n      <td>Total','<tr style="font-weight:bold">\n      <td>Total'))
    else:
        print("\n","-"*30," Summary of License Costs ","-"*30) 
        print(licenses_printable[["Product Name","License type","Quantity","Contract ARR","Average Discount"]].to_string(index=False))
        print('-'*100)
        print("Total:{:>64,.0f}{:>13,.0f}{:+17.0%}".format(
            licenses[licenses["DB_Option"]>0]["Quantity"].max(),
    #        licenses[licenses["DB_Option"]>0]["Contract ARR"].sum(),
            totalSupportPaid,
            licenses[licenses["DB_Option"]>0].apply(        # this calculates the weighted average. Weight is based on the ARR value
                lambda row:
                    row["Contract ARR"]*row["Average Discount"]
                ,axis=1).sum()/licenses["Contract ARR"][licenses["DB_Option"]>0].sum()    
                )   
            )
    del licenses_printable
  

# And we will calculate the total cores covered and what is the coverage of the different DB options 
# compared to the Enterprise editionmax_cores_supported

cores_chart=licenses[licenses["DB_Option"]>0].pivot("Product Name","License type","Total Intel Cores Covered").fillna(0)
cores_chart.reset_index(inplace=True)

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
totalSupportPaid=licenses[licenses["DB_Option"]>0]["Contract ARR"].sum()
cores_chart["Percent"]=cores_chart.apply(
    lambda row:
        row["Total Intel cores"]/max_cores_supported,
        axis=1
)

def printLicenseQuantities(style='txt'):
#    warnings.filterwarnings('ignore')
    cores_chart_printable=cores_chart.sort_values(by=["Percent"], ascending=False)
#    print(cores_chart_printable)

    # Make sure that the DB EE is the first in the row even if that is not the greatest
    cores_chart_printable.reset_index(inplace=True)
    DBEE_location=cores_chart_printable[cores_chart_printable['Product Name']=='Oracle Database Enterprise Edition'].index[0]
    if DBEE_location>0:
        temp=cores_chart_printable.iloc[DBEE_location].copy()
        cores_chart_printable.drop(index=DBEE_location, inplace=True)
        cores_chart_printable.loc[-1]=temp
        cores_chart_printable.index=cores_chart_printable.index+1
        cores_chart_printable.sort_index(inplace=True)
    else:
        cores_chart_printable=cores_chart.sort_values(by=["Percent"], ascending=False)

    cores_chart_printable["NUP"]=cores_chart_printable["NUP"].map('{:,.0f}'.format)
    cores_chart_printable["Processor"]=cores_chart_printable["Processor"].map('{:,.0f}'.format)
    cores_chart_printable["Total Intel cores"]=cores_chart_printable["Total Intel cores"].map('{:,.0f}'.format)
    cores_chart_printable["Percent"]=cores_chart_printable["Percent"].map('{:.0%}'.format)
#   warnings.filterwarnings('default')


    if style=='txt':
        print("\n","-"*30," Summary of Licenses ","-"*30) 
        print(cores_chart_printable.to_string(index=False))
#        print(cores_chart_printable[['Product Name','NUP','Processor','Total Intel cores','Percent']])
    if style=='html':
        print(cores_chart_printable[['Product Name','NUP','Processor','Total Intel cores','Percent']].to_html(classes="Intel_coverage_table_style", index=False,index_names=False)
            .replace('<tr>\n      <th>','<tr>\n      <th style="text-align: left;">')
            .replace('<tbody>\n    <tr>','<tbody>\n    <tr style="font-weight:bold">'))


#These activities are needed to calculate the cores coverage by CSI or Order number

if 'CSI#' in current_columns or 'Order Number' in licenses.columns:
    if 'CSI#'in current_columns:
        support_id='CSI#'
    else:
        support_id='Order Number'
    
    support_licenses=df[[support_id,"Product Name", "Quantity", "Contract ARR","License type"]][df["License type"] != "Unknown"].groupby(
    [support_id,"Product Name","License type"], as_index=False)[["Quantity", "Contract ARR"]].sum()





def printULAInfo(style='txt'): #Check if the customer has ULA
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
        if style=='txt':
            print("\n","-"*30," ULA Information ","-"*30) 
            print("These customers has probably a ULA on these Licenses:")
            print(ula_licenses.to_string(index=False))
        if style=='html':
            print("<br>These customers has probably a ULA on these Licenses:<br>")
            print(ula_licenses.to_html(classes="ULA_table_style",index=False))           
        return True
    else:
        print("Probably there are no ULA licenses in this scope")
        return False

def printTargetSizing(style='txt'):    #Sizing the environment
    if style=='txt':
        print("\n","-"*30," Possible Exa target For The complete workload ","-"*30) 
        print("\nTarget Sizing for this installation:","No. cores:",max_cores_supported,"Storage needed:",max_cores_supported*2)
    result=sizer.sizing(
        no_cores=max_cores_supported,
        storage_needed=max_cores_supported*2,
        use_DBServerExpansions=False)
    if style=='txt':
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
        print("Total Target Annual Infrastructure cost: ${:,.0f}".format(sum(config["Cost"] for config in result)*12))
    
    if style=='html':
        print("No. cores: <b>{:,.0f} </b>Storage needed: <b>{:,.0f} TB</b><br>".format(max_cores_supported,max_cores_supported*2))
        print('<table border="1" class="target_sizing_table_style">')
        print("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format("Configuration","Number","CPU","Storage","Monthly Cost"))
        print(*list(map(lambda config: "<tr><td>{}</td><td>{}</td><td>{:,.0f}</td><td>{:,.0f}</td><td>${:,.0f}</td></tr>".format(
            config["Configuration"],
            config["Number"],
            config["CPUSize"],
            config["StorageSize"],
            config["Cost"]
            ),result)),sep='\n')
        print('<tr style="font-weight:bold"><td>{}</td><td>{}</td><td>{:,.0f}</td><td>{:,.0f}</td><td>${:,.0f}</td></tr>'.format(
            "Total:",
            sum(config["Number"] for config in result),
            sum(config["CPUSize"] for config in result),
            sum(config["StorageSize"] for config in result),
            sum(config["Cost"] for config in result)
            ))
        print("</table><br>Total Target Annual Infrastructure cost: <b>${:,.0f}</b>".format(sum(config["Cost"] for config in result)*12))


def getMaxCoresSupported():
    return max_cores_supported

def getTotalSupportPaid():
    return totalSupportPaid

warnings.filterwarnings('default')
#printNoCustomers()
#printLicenseCosts(style='html')
#printLicenseQuantities(style='txt')
# printULAInfo()
# printTargetSizing()
# getMostSignificantCustomerName()


