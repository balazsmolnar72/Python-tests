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

import os, cgi, time

form = cgi.FieldStorage() 

print("Content-type:text/html\r\n\r\n")
print('<html>')
print('<head>')
print('<title>TCO Analysis</title>')
print('</head>')
print('<body>')

fi = form['filename']
fn = fi.filename
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
    

import LicenseAnalysis as LA


""" if is_csv(fn):
    print("You've uploaded a csv file")
else:
    print("The file you've uploded is not a csv.") """

print('<h2>This is a TCO analysis</h2>')

LA.printNoCustomers()

print('<h2>These customers or this customer pays annually this amount of Support to Oracle for Oracle Database:</h2>')
LA.printLicenseCosts(style='html')

print('</body>')
print('</html>')