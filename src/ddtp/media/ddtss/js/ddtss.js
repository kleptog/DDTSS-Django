// Common javascript file for the DDTSS-Django project
function popup (url) {
    fenster = window.open(url, 'msgwindow', 'width=400,height=600,resizable=yes');
    fenster.focus();
    return true;
}

function setupMessagelinks() {
  $('a.messagelink').click(function () {
      popup(this.href)
      // suppress normal click event
      return false;
  })
}

function setMilestoneChart(title, url) {
    $.getJSON(url, function(data) {
        // Data is of the form (timestamp, packages, total, percent)
        var packages=[], total=[], percent=[];

        for (row in data) {
            packages.push( [data[row][0], data[row][1]] );
            total.push(    [data[row][0], data[row][2]] );
            percent.push(  [data[row][0], data[row][3]] );
        }
        $('#flot_chart').show();
        $('#flot_title').html(title);
        $.plot( $('#flot_graph'), [ {label: 'Percent'   , yaxis: 1, data: percent},
                                    {label: 'Total'     , yaxis: 2, data: total},
                                    {label: 'Translated', yaxis: 2, data: packages} ],
                                    {
                                        xaxis: { mode: 'time', timeformat: '%y-%m-%d' },
                                        yaxis: { show: 1, min: 0 },
                                        y2axis: { show: 1, min: 0 },
                                        legend: { show: 1, position: 'nw' }
                                    });
    });
}
function setUserChart(url) {
    $.getJSON(url, function(data) {
        // Data is of the form (timestamp, translated, reviewed)
        var translated=[], reviewed=[];

        for (row in data) {
            translated.push( [data[row][0], data[row][1]] );
            reviewed.push(   [data[row][0], data[row][2]] );
        }
        $('#flot_chart').show();
        $('#flot_title').html('User stats');
        $.plot( $('#flot_graph'), [ {label: 'Translated'   , yaxis: 1, data: translated},
                                    {label: 'Reviewed'     , yaxis: 1, data: reviewed} ],
                                    {
                                        xaxis: { mode: 'time', timeformat: '%y-%m-%d' },
                                        yaxis: { show: 1, min: 0 },
                                        legend: { show: 1, position: 'nw' }
                                    });
    });
}
