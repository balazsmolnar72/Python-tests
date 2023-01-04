import pandas as pd

possible_fields=['Customer Name', 'Product Name','Product Description','Quantity','Contract ARR', 'Contract ARR (CD)','Metric']

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

print(df)