import pandas as pd
import plotly.express as px
Scenarios = ['On Premise', 'Exadata', 'ExaCC', 'ExaCC BYOL', 'OCI DBCS']
Infrastructure = [80000, 100000, 90000, 90000, 40000]
License_support = [340000, 280000, 0, 200000, 0]
Universal_credits=[0,0,89000,25000,45000]
width = 0.9       # the width of the bars: can also be len(x) sequence

Totals=list(map(lambda a,b,c: a+b+c, Infrastructure, License_support,Universal_credits))

data={'Scenarios':Scenarios,'Infra':Infrastructure,'License_support':License_support,'UC':Universal_credits}
print(data)
df=pd.DataFrame(data)
df=df.transpose()
print(df)
fig=px.bar(df)
fig.show()
