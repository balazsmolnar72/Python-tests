import csv,string 

def is_csv(infile):
    try:
        with open(infile, newline='', encoding="utf-8") as csvfile:
            start = csvfile.read(4096)

            # isprintable does not allow newlines, printable does not allow umlauts...
            if not all([c in string.printable or c.isprintable() for c in start]):
                return False
            dialect = csv.Sniffer().sniff(start)
            return True
    except csv.Error:
        # Could not get a csv dialect -> probably not a csv.
        return False


def insertDownloadLink(table_class, filename):  #This command will insert a 'Downloadd as CSV' link into the page
                                                #table_class should contain the class of the table to be downloaded
                                                # filename should contain the default filename where csv should be exported (extended with the current date) 
    if 'insertDownloadLinkScript' not in globals(): # if the insertDownloadLinkScript is not defined (Include <script> only at the first time when this is involved)
        print('<script src="../Scripts.js" type="text/javascript"></script>')
        global insertDownloadLinkScript
        insertDownloadLinkScript=True
    print('<a class="download_links" href="#" onclick="download_table_as_csv(\''+table_class+'\',\''+filename+'\');">Download as CSV</a><br>')

def printTCOChart():
    data={'Scenarios':Scenarios,'Infra':Infrastructure,'License_support':License_support,'UC':Universal_credits}
    df=pd.DataFrame(data)
    df.set_index('Scenarios', inplace=True)
    fig=go.Figure(
        data=[
            go.Bar(
                name="Infra",
                x=df.index,
                y=df.Infra,
                offsetgroup=0,
                marker=go.bar.Marker(color='#245d63'),
                text=list(map(lambda val: 'Infra \n${:,.0f}K'.format(val/1000) if(val>0) else "",df.Infra)),
                textposition="inside"
            ),
            go.Bar(
                name="License_Support",
                x=df.index,
                y=df.License_support,
                offsetgroup=0,
                marker=go.bar.Marker(color='#83401E'),
                text=list(map(lambda val: 'Lic. Support \n${:,.0f}K'.format(val/1000) if(val>0) else "",df.License_support)),
                textposition="inside",
                textfont=dict(
                    color="white"
                )
            ),       
            go.Bar(
                name="UC",
                x=df.index,
                y=df.UC,
                marker=go.bar.Marker(color='#DE7F11'),
                offsetgroup=0,
                text=list(map(lambda val: 'UC \n${:,.0f}K'.format(val/1000) if(val>0) else "",df.UC)),
                textposition="inside",
                textfont=dict(
                    color="white"
                )
            )
        ]
    )
    fig.update_layout(barmode="stack",bargap=0.1)

    totalSum=df.sum(axis="columns")
    totalSumText=list(map(lambda val: '{:+.0%} Total \n${:,.0f}K'.format(val/totalSum[Reference]-1,val/1000) if(val>0) else "",totalSum))
    fig.add_trace(go.Scatter(
    #    x=df.Scenarios, 
        x=df.index,
        y=totalSum,
        text=totalSumText,
        mode="text",
        textposition='top center',
        textfont=dict(
            size=14,
        ),
        showlegend=False
    ))
    fig.update_yaxes(range=[0,totalSum.max()*1.2])
    fig.update_layout(title="Annual cost comparison",width=df.index.size*220, height=500)
    #fig.show()
    #print(plotly.io.to_html(fig=fig,full_html=False, default_width='100%', default_height='60%',div_id='TCO_Comparison_chart'))
    print(plotly.io.to_html(fig=fig,full_html=False, default_width='100%',div_id='TCO_Comparison_chart'))


def printSupportIDChart():
    import warnings
    fig=go.Figure()
    available_licenses=support_licenses.groupby(support_licenses["Product Name"])["Percent","IsDBEE"].max().sort_values(by=["IsDBEE","Percent"],ascending=[False,False])
    available_licenses.reset_index(inplace=True)

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

    # fig.update_layout(title="Supported cores by Support ID",width=1000)
    fig.update_layout(title="Supported Intel Cores by Support ID",width=650, height=len(available_licenses)*50)
    #fig.show()
    print(plotly.io.to_html(fig=fig,full_html=False,div_id='Support_ID_licenses_chart'))

import os, cgi, time

form = cgi.FieldStorage() 
fi = form['filename']
#fn = fi.filename
fn ='Install Base.csv'
if fi.filename:
    # This code will strip the leading absolute path from your file-name
    fil = os.path.basename(fi.filename)
    # open for reading & writing the file into the server
    fo=open(fn, 'wb')
    fo.write(fi.file.read())
    fo.close()
    while not os.path.exists(fn): # Wait until the file appear in File system (probably not needed)
        print("file does not exists")
        time.sleep(1)
    


print("Content-type:text/html\r\n\r\n")
print('<html>')
try:
    import LicenseAnalysis as LA
except Exception as e:
    print('<body>')
    print('<h1>Installed Base file has wrong format</h1>')
    print(e)
    print('</body></html>')
    exit()
print('<head>')
print('<title>TCO Analysis for ',LA.getMostSignificantCustomerName(),'</title>')
print('<link rel="stylesheet" href="../reportStyle.css" type="text/css"/>')
print('</head>')
print('<body>')
print('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>')



# print("""<style>
#         @media print {
#             .pagebreak {
#                 clear: both;
#                 page-break-after: always;
#             }
#     }</style>""")


""" if is_csv(fn):
    print("You've uploaded a csv file")
else:
    print("The file you've uploded is not a csv.") """

print('<h2>TCO Analysis for Complete Oracle DB Migration to ExaCC')
from datetime import date
today = date.today()
print('<br><i style="font-size:small;">',today,'</i></h2>')
print('<a class="download_links" href="#" onclick="window.print();">Print this analyis</a><br>')

print('<div class="InfoPanel">')

no_customers=LA.printNoCustomers(style="html")
if no_customers>1:
    print('<br><br>The most significant customer is:<b>',LA.getMostSignificantCustomerName(),'</b><br>')

print('</div>')

print('<h2>TCO Comparison of Current and A Possible Exa Environment</h2>')

#The plotly chart of TCO Comparison

import pandas as pd
import plotly
import plotly.graph_objects as go
import TCOComparison as TCO

max_cores_supported=LA.getMaxCoresSupported()
totalSupportPaid=LA.getTotalSupportPaid()

#totalSupportPaid=licenses[licenses["DB_Option"]>0]["Contract ARR"].sum()
TCO_result=TCO.TCO_comparison(
    cores=max_cores_supported,
    storageTB=max_cores_supported*2,
    annualDBsupport=totalSupportPaid,
    utilization=0.4)
Scenarios = ['On Premise', 'ExaCC', 'ExaCS', 'ExaCC BYOL', 'ExaCS BYOL']
Infrastructure = TCO_result['Infrastructure']
License_support = TCO_result['DB Support']
Universal_credits=TCO_result['UC']
width = 0.9       # the width of the bars: can also be len(x) sequence

#Totals=list(map(lambda a,b,c: a+b+c, Infrastructure, License_support,Universal_credits))
Totals=TCO_result['Total']
Reference='On Premise' # On the chart the savings will be displayed based on this reference

printTCOChart()  # Draw the TCO Chart 

#Other details display

print('<h2>Annual Support Paid for Oracle Database and Options:</h2>')
LA.printLicenseCosts(style='html')
insertDownloadLink('dataframe.licenses_table_style',LA.getMostSignificantCustomerName()+' support cost by license')

if LA.printULAInfo(style='html'):
    insertDownloadLink('dataframe.ULA_table_style',LA.getMostSignificantCustomerName()+' Licenses in ULA')

print('<h2>Number of Intel Cores Can Be Covered by DB Licenses</h2>')
support_licenses=LA.getLicencesBySupportId()
if support_licenses is not None:  #If the data contains Order Number or CSI number fields draw a chart about CSI Numbers
    print('<table id="LicenseCoverageColumnTable"><td>')
LA.printLicenseQuantities(style='html')
print('<div class="download_links"><script> DisplayPercentageOfCoverage()</script></div>')
insertDownloadLink('dataframe.Intel_coverage_table_style',LA.getMostSignificantCustomerName()+' cores covered by DB licenses')
if support_licenses is not None:  #If the data contains Order Number or CSI number fields draw a chart about CSI Numbers
    print('<td>')
    printSupportIDChart()
    print('</td></table>')

#print('<div class="pagebreak"> </div>')  # Breaks the page before the target sizing

print('<h2>Possible Exa Target Sizing</h2>')
print('<br>To host the whole scope of this environment on Exa configurations, you would need this configuration:<br>')
LA.printTargetSizing(style='html')
print('<br>')
insertDownloadLink('target_sizing_table_style',LA.getMostSignificantCustomerName()+' Exa Target Sizing')
print('<br><br>')

# Close the page

print('<div class="ReportFootage"> ')
print('''
    This calculation is based on actual Customer Support data, but the TCO comparison is based on several assumptions.
    This calculation cannot be considered as a commercial offer, the purpose of this calculation is to give an orientation of the 
    expected costs and benefits of the solution.  
    Oracle does not take any responsiblility for the assumptions and calculations in case of a future commercial offer!
    <br><br>Calculation prepared by: <a href="mailto:balazs.molnar@oracle.com">Balazs Molnar</a> Oracle Corporation ''')
print('</div>')

print('</body>')
print('</html>')