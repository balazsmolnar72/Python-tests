import json
import pandas as pd
import ExaSizing as sizer


def TCO_comparison(cores,storageTB,annualDBsupport,utilization, Exa_Core_Ratio=1):
    json_file=open("benchmarks.json")
    benchmarks=json.load(json_file)
    json_file.close()
    exadata_prices=pd.read_csv("ExaCC pricing.csv", sep=',').fillna(0)
    exaCSResult=sizer.sizing(no_cores=cores,storage_needed=storageTB,Exa_Core_Ratio=Exa_Core_Ratio)
    ExaCSInfraCost=sum(config["Cost"] for config in exaCSResult)*12
    ExaCCResult=sizer.sizing(no_cores=cores,storage_needed=storageTB,use_DBServerExpansions=False)
    ExaCCInfraCost=sum(config["Cost"] for config in ExaCCResult)*12
    OnPremInfraCost=cores*benchmarks["Cost of 1 core Intel Server Acquisition"]/benchmarks["Amortization Period in Years"]+storageTB*benchmarks["Cost of TB Storage CAPEX"]/benchmarks["Amortization Period in Years"]+cores*benchmarks["Support of 1 TB of Storage OPEX"]+storageTB*benchmarks["OS and Server support for 1 core"]
    UniversalCreditLI=0
    UniversalCreditLI=cores*24*31*12*utilization*float(exadata_prices[exadata_prices["Configuration"]=="DB Extreme Performance"]["Price"])
    UniversalCreditBYOL=cores*24*31*12*utilization*float(exadata_prices[exadata_prices["Configuration"]=="DB BYOL"]["Price"])
    output=pd.DataFrame([
        ("On Premise",OnPremInfraCost,annualDBsupport,0),
        ("ExaCC",ExaCCInfraCost,0,UniversalCreditLI),
        ("ExaCS",ExaCSInfraCost,0,UniversalCreditLI),
        ("ExaCC BYOL",ExaCCInfraCost,annualDBsupport,UniversalCreditBYOL),
        ("ExaCS BYOL",ExaCSInfraCost,annualDBsupport,UniversalCreditBYOL)
    ],columns=["Config","Infrastructure","DB Support","UC"])
    output.set_index("Config",inplace=True)
    output["Total"]=output.sum(axis="columns")
    output["Saving %"]=list(map(lambda sum: (sum/output.loc["On Premise"]["Total"])-1,output["Total"]))
    return output

#TCO_result=TCO_comparison(cores=1308,storageTB=1308*2,annualDBsupport=6812223,utilization=0.4)
#print(TCO_result)
