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
except:
    print('<body>')
    print('<h1>Installed Base file has wrong format</h1>')
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
fig.update_layout(title="4 years cost comparison",width=df.index.size*220, height=500)
#fig.show()
#print(plotly.io.to_html(fig=fig,full_html=False, default_width='100%', default_height='60%',div_id='TCO_Comparison_chart'))
print(plotly.io.to_html(fig=fig,full_html=False, default_width='100%',div_id='TCO_Comparison_chart'))

#Other details display

print('<h2>Annual Support Paid for Oracle Database and Options:</h2>')
LA.printLicenseCosts(style='html')
insertDownloadLink('dataframe.licenses_table_style',LA.getMostSignificantCustomerName()+' support cost by license')

if LA.printULAInfo(style='html'):
    insertDownloadLink('dataframe.ULA_table_style',LA.getMostSignificantCustomerName()+' Licenses in ULA')

print('<h2>Number of Intel Cores Can Be Covered by DB Licenses</h2>')
LA.printLicenseQuantities(style='html')
insertDownloadLink('dataframe.Intel_coverage_table_style',LA.getMostSignificantCustomerName()+' cores covered by DB licenses')
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