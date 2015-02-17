/*!
 * DDTSS-Django - A Django implementation of the DDTP/DDTSS website.
 * Copyright (C) 2014-2015 Fabio Pirola <fabio@pirola.org>
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
    language: undefined,
    // Flag used to identify coordinator, set in wordlist_page.html.
    flagCoordinator: undefined,
    // This field set in wordlist_page.html.
    wordlistUrl: undefined,
    // This field set in wordlist_page.html.
    wordlistPageAddEditDeleteUrl: undefined,
    // Wordlist DataTable.
    wordlistTable: undefined,
    // All Wordlist.
    allWordlist: undefined,
    // Mapping: from an incremental id to wordlist
    // Used to identify object to edit/delete
    mappingIdToWordlist: undefined,
    // Mapping: from an incremental id to wordlist
    // Used to check input data
    mappingWordlistToId: undefined,
    // Used to store current action
    currentAction: undefined,

    init: function() {
        // Language variable is defined in wordlist_page.html.
        DDTSS.retrieveWordlist(WORDLIST_PAGE.wordlistUrl, WORDLIST_PAGE.populateTable);
        $('.inline').colorbox({inline:true, width:'50%'});
        $('#input-pop-up-word').keyup(function(){
            WORDLIST_PAGE.checkPopUpData();
        });
        $('#textarea-pop-up-translation').keyup(function(){
            WORDLIST_PAGE.checkPopUpData();
        });
    },
    populateTable : function(wordlist) {
        var rows = [], i=0;
        if (WORDLIST_PAGE.wordlistTable === undefined) {
            WORDLIST_PAGE.buildTable();
        }
        WORDLIST_PAGE.wordlistTable.fnClearTable();
        WORDLIST_PAGE.mappingIdToWordlist=[];
        WORDLIST_PAGE.mappingWordlistToId=[];
        for (keyCycle in wordlist) {
            if (wordlist.hasOwnProperty(keyCycle)) {
                rows.push([['<a href="#" onclick="WORDLIST_PAGE.openPopUp(\'edit\',',
                i,');return false;">Edit</a> / ',
                '<a href="#" onclick="WORDLIST_PAGE.openPopUp(\'delete\',',
                i,');return false;">Delete</a>'].join(''),keyCycle,
                    wordlist[keyCycle]]);
                WORDLIST_PAGE.mappingIdToWordlist[i]=keyCycle;
                WORDLIST_PAGE.mappingWordlistToId[keyCycle]=i;
                i+=1;
            }
        }

        if (rows.length > 0) {
            WORDLIST_PAGE.wordlistTable.fnAddData(rows, true);
        }
        //WORDLIST_PAGE.wordlistTable.fnAdjustColumnSizing();
        WORDLIST_PAGE.wordlistTable.fnDraw();
        WORDLIST_PAGE.wordlistTable.fnSort([ [ 1, 'asc' ] ]);
        WORDLIST_PAGE.allWordlist = wordlist;
        if (WORDLIST_PAGE.flagCoordinator === undefined
               || WORDLIST_PAGE.flagCoordinator === false
               || WORDLIST_PAGE.flagCoordinator === 'False') {
            // Hide column in datatable
            WORDLIST_PAGE.wordlistTable.fnSetColumnVis( 0, false );
            // Hide button
            $('#button-add-word').hide();
        }
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
                         {'bSortable': false, 'sWidth': '15%' },
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
    },
    // Open pop-up for new wordlist
    openPopUp: function(action, id) {
        var currentWord, currentTranslation;

        //$('#cboxClose').click();
        WORDLIST_PAGE.currentAction=action;

        if (action === 'add') {
            $('#insert-or-update-record #head-content').text('Add word');
            $('#input-pop-up-word').val('');
            $('#input-pop-up-word').attr( 'readonly', false );
            $('#check-input-value-word').hide();
            $('#textarea-pop-up-translation').val('');
            $('#textarea-pop-up-translation').prop( 'readonly', false );
            $('#check-input-value-translation').hide();
            $('#button-pop-up-save').show();
            $('#button-pop-up-delete').hide();
            WORDLIST_PAGE.checkPopUpData();
        } else if(action === 'edit') {
            currentWord=WORDLIST_PAGE.mappingIdToWordlist[id];
            currentTranslation=WORDLIST_PAGE.allWordlist[currentWord];
            $('#insert-or-update-record #head-content').text('Edit word');
            $('#input-pop-up-word').val(currentWord);
            $('#input-pop-up-word').attr( 'readonly', true );
            $('#check-input-value-word').hide();
            $('#textarea-pop-up-translation').val(currentTranslation);
            $('#textarea-pop-up-translation').prop( 'readonly', false );
            $('#check-input-value-translation').hide();
            $('#button-pop-up-save').show();
            $('#button-pop-up-save').prop( 'disabled', false );
            $('#button-pop-up-delete').hide();
            WORDLIST_PAGE.checkPopUpData();
        } else {
            // Delete
            currentWord=WORDLIST_PAGE.mappingIdToWordlist[id];
            currentTranslation=WORDLIST_PAGE.allWordlist[currentWord];
            $('#insert-or-update-record #head-content').text('Delete word');
            $('#input-pop-up-word').val(currentWord);
            $('#input-pop-up-word').attr( 'readonly', true );
            $('#check-input-value-word').hide();
            $('#textarea-pop-up-translation').val(currentTranslation);
            $('#textarea-pop-up-translation').prop( 'readonly', true );
            $('#check-input-value-translation').hide();
            $('#button-pop-up-save').hide();
            $('#button-pop-up-delete').show();
        }
        
        $('#open-pop-up').click();
        
    },
    checkPopUpData: function() {
        var currentWord=$('#input-pop-up-word').val(),
            currentTranslation=$('#textarea-pop-up-translation').val();
        // Check word input field
        if (currentWord === undefined
                || currentWord.length < 1) {
            $('#check-input-value-word').html('<br/>Word must contain at least one character');
            $('#check-input-value-word').show();
            $('#button-pop-up-save').prop( 'disabled', true );
        } else if(WORDLIST_PAGE.currentAction !== 'edit'
                      && WORDLIST_PAGE.mappingWordlistToId.hasOwnProperty(currentWord)) {
            $('#check-input-value-word').html(['<br/>This word already exist in',
                ' wordlist. Click <a id="a-recall-wordlist" href="#"',
                ' onclick="WORDLIST_PAGE.openPopUp(\'edit\',',
                WORDLIST_PAGE.mappingWordlistToId[currentWord]
                ,');return false;">HERE</a> to recall.'].join(''));
            $('#check-input-value-word').show();
            $('#button-pop-up-save').prop( 'disabled', true );
        } else {
            $('#check-input-value-word').hide();
            $('#button-pop-up-save').prop( 'disabled', false );
        }
        // Check translation input field
        if (currentTranslation === undefined
                || currentTranslation.length < 3) {
            $('#check-input-value-translation').html('<br/>Translation must contain at least three characters');
            $('#check-input-value-translation').show();
            $('#button-pop-up-save').prop( 'disabled', true );
        } else {
            $('#check-input-value-translation').hide();
            $('#button-pop-up-save').prop( 'disabled', false );
        }
        $('#insert-or-update-record').colorbox.resize();
    },
    saveWordlist: function() {
        var data = {
        action: WORDLIST_PAGE.currentAction,
        word: $('#input-pop-up-word').val(),
        translation: $('#textarea-pop-up-translation').val()};
        $.ajax({
            type : 'POST',
            url : WORDLIST_PAGE.wordlistPageAddEditDeleteUrl,
            processData : false,
            timeout : DDTSS.ajaxTimeout,
            data : JSON.stringify(data),
            dataType : 'json',
            complete: function(xhr) {
                if ((WORDLIST_PAGE.currentAction === 'add' && xhr.status === 201)
                       ||(WORDLIST_PAGE.currentAction === 'edit' && xhr.status === 200)
                       ||(WORDLIST_PAGE.currentAction === 'delete' && xhr.status === 204)) {
                        $('#open-pop-up').hide();
                        $('#open-pop-up-ok-status').click();
                        DDTSS.retrieveWordlist(WORDLIST_PAGE.wordlistUrl, WORDLIST_PAGE.populateTable);
                } else {
                    alert('An error occurred in retrieving wordlist - Please contact webmaster');
                }
            }
        });
    }
};




// Document ready!
$(document).ready(function() {
    WORDLIST_PAGE.init();
});
