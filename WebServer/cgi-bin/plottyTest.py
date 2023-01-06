import pandas as pd
import plotly.express as px
import pandas as pd
import plotly
import plotly.graph_objects as go
import TCOComparison as TCO

try:
    import LicenseAnalysis as LA
except Exception as e:
    print('<body>')
    print('<h1>Installed Base file has wrong format</h1>')
    print(e)
    print('</body></html>')
    exit()

def printSupportIDChart():
    import warnings
    fig=go.Figure()
    available_licenses=support_licenses.groupby(support_licenses["Product Name"])["Percent","IsDBEE"].max().sort_values(by=["IsDBEE","Percent"],ascending=[False,False])
    available_licenses.reset_index(inplace=True)

    print(available_licenses)
    colors=['#DE7f11','#A0c98b','#DB6fBF','#FBc26A','#9E7FCC','#5fb9b5','#E46476','#5fa2ba','#b4728b','#bd9057']

    support_ids=support_licenses["Support ID"].unique().tolist()
    i=0
    total_cores=available_licenses.copy()
    total_cores["Total Intel Cores Covered"]=total_cores.apply(
        lambda row: 0,
        axis=1
    )
   
    for s_id in support_ids:
        testseries=available_licenses.copy()
        s_idLicenses=support_licenses[support_licenses["Support ID"] == s_id]
        warnings.filterwarnings('ignore', category=UserWarning) 
        testseries["Total Intel Cores Covered"]=testseries.apply(
            lambda row:
                s_idLicenses[support_licenses["Product Name"] == row["Product Name"]]["Total Intel Cores Covered"].iloc[0] 
                    if len(s_idLicenses[support_licenses["Product Name"] == row["Product Name"]])>0 else 0,
                axis=1
        )
        total_cores["Total Intel Cores Covered"]=total_cores.apply(
            lambda row: row["Total Intel Cores Covered"]+testseries[testseries["Product Name"]==row["Product Name"]]["Total Intel Cores Covered"].iloc[0]
                if len(testseries[testseries["Product Name"]==row["Product Name"]])>0 else 0,
        axis=1
        )   
        warnings.filterwarnings('default')
        testseries=testseries[["Product Name","Total Intel Cores Covered"]]
        categories=testseries["Product Name"].copy()
        categories.at[0]="<b>"+categories.at[0]+"</b>"
        fig.add_trace(go.Bar(
            x=testseries["Total Intel Cores Covered"], y=categories,
            name=s_id,
            orientation='h',
            marker=dict(
                color=colors[i],
                line=dict(color='rgb(248, 248, 249)', width=1)
            ),
            text=testseries["Total Intel Cores Covered"],
            textposition="inside",
            insidetextanchor = 'middle',
            textfont=dict(
                color="white"
            ),
            hovertext=testseries.apply(lambda row, si_id=s_id: 'Support Id:'+str(si_id)+' cores:'+"{:.0f}".format(row["Total Intel Cores Covered"]), axis=1)
        ))

        del testseries
        if i<len(colors)-1:
            i+=1
        else:
            i=0

    fig.update_layout(
        barmode='stack',
        showlegend=True,
        yaxis={'categoryorder':'total ascending'}
    )
    total_cores["Total Intel Cores Covered"]=total_cores["Total Intel Cores Covered"].apply(
        lambda row: "{:.0f}".format(row)
    )
    categories=total_cores["Product Name"].copy()
    categories.at[0]="<b>"+categories.at[0]+"</b>"
    fig.add_trace(go.Scatter(
        x=list(total_cores["Total Intel Cores Covered"].map(lambda row: int(row)*1.01)),
        y=categories,
        text=list(total_cores["Total Intel Cores Covered"]),
        mode="text",
        textposition='middle right',
        textfont=dict(
            size=14,
        ),
        showlegend=False
    ))

    fig.update_layout(title="Supported cores by Support ID",width=1000, height=1000)
    fig.show()
    #print(plotly.io.to_html(fig=fig,full_html=False, default_width='100%',div_id='Support_ID_licenses_chart'))

support_licenses=LA.getLicencesBySupportId()
printSupportIDChart()
