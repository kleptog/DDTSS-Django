/*!
 * DDTSS-Django - A Django implementation of the DDTP/DDTSS website.
 * Copyright (C) 2014 Fabio Pirola <fabio@pirola.org>
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

var WORDLIST_PAGE = {
    // This field set in wordlist_page.html.
    language : undefined,
    // This field set in wordlist_page.html.
    wordlistUrl : undefined,
    // Wordlist DataTable.
    wordlistTable : undefined,
    // All Wordlist.
    allWordlist : undefined,

    populateTable : function(wordlist) {
        var rows = [];
        WORDLIST_PAGE.buildTable();
        WORDLIST_PAGE.wordlistTable.fnClearTable();
        for (keyCycle in wordlist) {
            if (wordlist.hasOwnProperty(keyCycle)) {
                rows.push([keyCycle,
                    wordlist[keyCycle]]);
            }
        }

        if (rows.length > 0) {
            WORDLIST_PAGE.wordlistTable.fnAddData(rows, true);
        }
        //WORDLIST_PAGE.wordlistTable.fnAdjustColumnSizing();
        WORDLIST_PAGE.wordlistTable.fnDraw();
        WORDLIST_PAGE.wordlistTable.fnSort([ [ 0, 'asc' ] ]);
        WORDLIST_PAGE.allWordlist = wordlist;
    },
    buildTable : function() {
        WORDLIST_PAGE.wordlistTable = $('#table-wordlist')
        .dataTable(
                {
                    'bSearchable' : true,
                    'bPaginate' : false,
                    'bFilter' : true,
                    'bInfo' : false,
                    'sDom' : '<"top-left"f>t<"clear">',
                    'bScrollCollapse': true,
                    'autoWidth': false,
                    'language' : {
                        'emptyTable' : 'No wordlist defined for this language.',
                        'infoEmpty' : 'No wordlist defined for this language.'
                     },
                     'columns': [
                         {'sWidth': '30%' },
                         {'sWidth': '70%' }
                      ],
                    'fnRowCallback' : function(nRow, aData,
                            iDisplayIndex, iDisplayIndexFull) {
                        return nRow;
                    }
                });
        new $.fn.dataTable.FixedHeader( WORDLIST_PAGE.wordlistTable );
    },

    // Save wordlist as CSV file via FileSaver (JavaScript).
    // File name has the following sintax:
    //  wordlist-[language]_[current date, format YYYYMMDD].csv
    // In order to be complaint with RFC 4180:
    //   - fields separated by the comma character and rows terminated by newlines;
    //   - field quoted;
    //   - each of the embedded double-quote characters must
    //       be represented by a pair of double-quote characters.
    saveAsCsv : function() {
        var currentDate = new Date(),
            blob = undefined,
            filename = ['wordlist-',
            WORDLIST_PAGE.language,
            '_',
            currentDate.getFullYear(),
            currentDate.getMonth() + 1,
            currentDate.getDate(),
            '.csv'
            ].join(''),
            wordlistData = [],
            translation;

        // Add header.
        wordlistData.push('"Word","Translation"\r\n');
        // Create a string with all values.
        for (keyCycle in WORDLIST_PAGE.allWordlist) {
            if (WORDLIST_PAGE.allWordlist.hasOwnProperty(keyCycle)) {
                translation = WORDLIST_PAGE.allWordlist[keyCycle].replace('"', '""');
                wordlistData.push(['"',
                keyCycle.replace('"', '""'),
                '","',
                translation,
                '"\r\n'].join(''));
                ;
            }
        }

        blob = new Blob(wordlistData, {type: "text/plain;charset=utf-8"}),
        saveAs(blob, filename);
    }
};

// Document ready!
$(document).ready(function() {
    // Language variable is defined in wordlist_page.html.
    DDTSS.retrieveWordlist(WORDLIST_PAGE.wordlistUrl, WORDLIST_PAGE.populateTable);
});
