// Quick and simple export target #table_id into a csv
function download_table_as_csv(table_class, filename, separator = ',') {
    // Select rows from table_class
    var rows = document.querySelectorAll('table.' + table_class + ' tr');
    // Construct csv
    var csv = [];
    for (var i = 0; i < rows.length; i++) {
        var row = [], cols = rows[i].querySelectorAll('td, th');
        for (var j = 0; j < cols.length; j++) {
            // Clean innertext to remove multiple spaces and jumpline (break csv)
            var data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ')
            // Escape double-quote with double-double-quote (see https://stackoverflow.com/questions/17808511/properly-escape-a-double-quote-in-csv)
            data = data.replace(/"/g, '""');
            // Push escaped string
            row.push('"' + data + '"');
        }
        csv.push(row.join(separator));
    }
    var csv_string = csv.join('\n');
    // Download it
    var filename = filename + '_' + new Date().toLocaleDateString() + '.csv';
    var link = document.createElement('a');
    link.style.display = 'none';
    link.setAttribute('target', '_blank');
    link.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv_string));
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function DisplayPercentageOfCoverage(){

    if(window.matchMedia('print').matches){
        return
    }
    var col1="#FBc26A",
    col2="white";
    var els=document.querySelectorAll('.dataframe.Intel_coverage_table_style tr td:last-child');
    for (var i=0; i<els.length; i++) {
        var content=els[i].firstChild.nodeValue;
        var percentage = Number(content.substring(0,content.length-1));
        els[i].style.background = "-webkit-gradient(linear, left top,right top, color-stop("+percentage+"%,"+col1+"), color-stop("+percentage+"%,"+col2+"))";
        els[i].style.background = "-moz-linear-gradient(left center,"+col1+" "+percentage+"%, "+col2+" "+percentage+"%)" ;
        els[i].style.background = "-o-linear-gradient(left,"+col1+" "+percentage+"%, "+col2+" "+percentage+"%)";
        els[i].style.background = "linear-gradient(to right,"+col1+" "+percentage+"%, "+col2+" "+percentage+"%)" ;
    }
}
