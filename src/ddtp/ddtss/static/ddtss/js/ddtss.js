/*!
 * DDTSS-Django - A Django implementation of the DDTP/DDTSS website.
 * Copyright (C) 2011-2014 Martijn van Oosterhout <kleptog@svana.org>
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

var DDTSS = {
    // Begin define usefull constant
    // timeout = 5 minutes
    ajaxTimeout : 400000,
    // End define usefull constant

    // Common javascript file for the DDTSS-Django project
    popup : function(url) {
        fenster = window.open(url, 'msgwindow', 'width=400,height=600,resizable=yes');
        fenster.focus();
        return true;
    },

    setupMessagelinks : function() {
        $('a.messagelink').click(function () {
            DDTSS.popup(this.href)
            // suppress normal click event
            return false;
        });
    },

    setMilestoneChart : function(title, url) {
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
    },

    setUserChart : function(url) {
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
    },

    /**
     * Retrieve wordlist entries and call handler function.
     * @param {string} wordlistUrl - Wordlist URL.
     * @param {string} handler - Function to call on wordlist entries retrieved.
     */
    retrieveWordlist : function(wordlistUrl, handler) {
        $.ajax({
            type : 'GET',
            url : wordlistUrl,
            processData : false,
            timeout : DDTSS.ajaxTimeout,
            data : undefined,
            dataType : 'json',
            success : function(responseMsg) {
                // Check if handler is a function.
                if (typeof handler === 'function') {
                    handler(responseMsg);
                }
            },
            error : function(jqXHR, textStatus, errorThrown) {
                alert('An error occurred in retrieving wordlist - Please contact webmaster');
            }
        });
    }
};