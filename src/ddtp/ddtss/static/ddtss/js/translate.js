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

var TRANSLATE = {
    // This field will evaluated in wordlist_page.html.
    wordlistUrl : undefined,
    showShortDiff : function(url) {
        var box,
            boxes = document.getElementsByName('shortboxes'),
            i;
        for(i = boxes.length - 1; i >= 0; i -= 1) {
            boxes[i].style.display = 'none';
        }
        /* Coded like this to avoid errors on 'None' */
        box = document.getElementById(url)
        if (box) {
            box.style.display = 'block';
        }
    },

    showLongDiff : function(url) {
        var boxes = document.getElementsByName('longboxes'),
            box,
            i;
        for (i = boxes.length - 1; i > 0; i -= 1) {
            boxes[i].style.display = 'none';
        }
        box = document.getElementById(url);
        if (box) {
            box.style.display='block';
        }
        return false;
    },

    toggleShowShortDescr : function() {
        var showDescrFields = document.getElementsByName('ShowShortDescr');
        for (i = showDescrFields.length; i > 0; i -= 1) {
            if(showDescrFields[i].style.display === 'block') {
                showDescrFields[i].style.display = 'none';
            } else {
                showDescrFields[i].style.display = 'block';
            }
        }
        return false;
    },

    toggleShowLongDescr : function() {
        var showDescrFields = document.getElementsByName('ShowLongDescr'),
            i;
        for (i = showDescrFields.length; i > 0; i -= 1) {
            if(showDescrFields[i].style.display === 'block') {
                showDescrFields[i].style.display = 'none';
            } else {
                showDescrFields[i].style.display = 'block';
            }
        }
        return false;
    },

    // Sort values by length.
    // name: member name used to sort
    // sortType used for desc or asc sorting.
    byLength : function(name, sortType) {
        return function(o, p) {
            var a, b;
            if (sortType !== 'asc'
                && sortType !== 'desc') {
                throw {
                    name: 'Error',
                    message: 'Unknown type of sorting[' + sortType +
                        ']. Allowed values are: desc or asc'
                };
            }
            if (o && p
                && typeof o === 'object'
                && typeof p === 'object') {
                a = o[name];
                b = p[name];
                if (typeof a === typeof b) {
                    if (sortType === 'asc') {
                        return a.length < b.length ? -1 : 1;
                    } else {
                        return a.length > b.length ? -1 : 1;
                    }
                }
                return typeof a < typeof b ? -1 : 1;
            } else {
                throw {
                    name: 'Error',
                    message: 'Expected an object when sorting by ' + name
                };
            }
        };
    },

    /** High light wordlist in package title and description.
     *
     * @param {object} wordlist Wordlist for selected language.
     */
    highlightWordlist : function(wordlist) {
        var tmpHtml, keyCycle,
            arrayWordlist = [];
        // Convert wordlist into array and sort it.
        for (keyCycle in wordlist) {
            if (wordlist.hasOwnProperty(keyCycle)) {
                arrayWordlist.push({word: keyCycle,
                                    translation: wordlist[keyCycle]});
            }
        }
        arrayWordlist.sort(TRANSLATE.byLength('word','desc'));
        tmpHtml = TRANSLATE.buildHtmlHighlight(arrayWordlist, $('#untranslated-short-description').text());
        $('#untranslated-short-description').html(tmpHtml);
        tmpHtml = TRANSLATE.buildHtmlHighlight(arrayWordlist, $('#untranslated-long-description').text());
        $('#untranslated-long-description').html(tmpHtml);
    },

    /** Build HTML string from original text adding
     * tag used to high light word.
     * High light wordlist is something tricky and it
     * is done with several steps:
     * 1) Cycle for all wordlist
     * 2) Search if there is at leat an occurence
     * 3) save result of split and match result
     * 4) Join all matching and return the html result.
     * 
     * @param {object} wordlist Wordlist for selected language.
     * @param {string} originalText Original (HTML) text.
     */
    buildHtmlHighlight : function(wordlist, originalText) {
        var splitResult = [],
            tmpSplitResult,
            tmpMatchResult,
            matchResult = [],
            posFirstOccurence,
            i, j,
            strPattern,
            regexp,
            finalHtml = '';
        // In order to understand better this function, let's make an example:
        //   wordlist = [{word: "lorem ipsum", translation: "FOUND lorem ipsum"},
        //                {word: "ipsum", translation: "FOUND ipsum"}]
        //   originalText = Lorem ipsum dolor sit amet... ipsum ... lorem

        // Convert original text into an array for next step(s)
        // Example - splitResult = ['Lorem ipsum dolor sit amet... ipsum ... lorem']
        splitResult = [originalText];
        for (i = 0; i < wordlist.length; i += 1) {
            // Example - First loop - wordlist[i] = {word: "lorem ipsum", translation: "FOUND lorem ipsum"}
            // Example - Second loop - wordlist[i] = {word: "ipsum", translation: "FOUND ipsum"}

            // Build pattern for regular expression.
            // Replace space character with a regular expression.
            // New line and carriage return is used for
            // wordlist splitted in different rows.
            // Add escape character to the special character.
            // Example - First loop - strPattern = 'lorem[ |\t|\n|\r\n]+ipsum'
            // Example - Second loop - strPattern = 'ipsum'
            strPattern = TRANSLATE.escapeSpecialChar(wordlist[i].word)
                                  .replace(/\t+/gim, ' ')
                                  .replace(/ +/gim, ' ')
                                  .replace(' ','[ |\\t|\\n|\\r\\n]+');

            // Build Regular expression
            regexp = new RegExp(strPattern, 'gim');

            for (j = 0; j < splitResult.length; j += 1) {
                posFirstOccurence = splitResult[j].search(regexp);
                if (posFirstOccurence < 0) {
                    // No occurence found - Skip to next split result
                    continue;
                }

                // Split text by regex pattern.
                // Example - First loop - tmpSplitResult = ['',' dolor sit amet... ipsum ... lorem']
                // Example - Second loop - tmpSplitResult = [" dolor sit amet... "," ... lorem"]
                tmpSplitResult = splitResult[j].split(regexp);

                // Example - First loop - tmpMatchResult = ['<span class="box-wordlist"><span class="tooltip-wordlist"></span><span class="wordlist" tooltip-text="FOUND lorem ipsum">lorem ipsum</span></span>']
                // Example - Second loop - tmpMatchResult = ['<span class="box-wordlist"><span class="tooltip-wordlist"></span><span class="wordlist" tooltip-text="FOUND ipsum">ipsum</span></span>']
                tmpMatchResult = TRANSLATE.buildTooltip(wordlist[i].translation,
                                                        splitResult[j].match(regexp));


                // Insert split result into "final" array.
                // Example - First loop - splitResult = ['',' dolor sit amet... ipsum ... lorem']
                // Example - Second loop - splitResult = ['',' dolor sit amet... ',' ... lorem']
                splitResult = TRANSLATE.spliceArrayWithDelete(splitResult,
                                                              tmpSplitResult,
                                                              j + 1);
                // Example - First loop - matchResult = ['<span class="box-wordlist"><span class="tooltip-wordlist"></span><span class="wordlist" tooltip-text="FOUND lorem ipsum">lorem ipsum</span></span>']
                // Example - First loop - matchResult = ['<span class="box-wordlist"><span class="tooltip-wordlist"></span><span class="wordlist" tooltip-text="FOUND lorem ipsum">lorem ipsum</span></span>',
                //                                       '<span class="box-wordlist"><span class="tooltip-wordlist"></span><span class="wordlist" tooltip-text="FOUND ipsum">ipsum</span></span>']
                matchResult = TRANSLATE.spliceArray(matchResult,
                                                    tmpMatchResult,
                                                    j);


                // Update j position to skip new items inserted.
                j += tmpSplitResult.length;
            }
        }

        // Merge final arrays with the folowing order
        //  1) splitResult
        //  2) matchResult
        // If a match has been found at the start of original statement then
        // add an empty string in the top of splitResult array.
        for (i = 0; i < splitResult.length; i += 1) {
            if (splitResult[i]) {
                finalHtml += splitResult[i];
            }
            if (matchResult[i]) {
                finalHtml += matchResult[i];
            }
        }
        return finalHtml;
    },

    /** Escape special character.
     * 
     * @param {string} inputString Input string.
     */
    escapeSpecialChar : function(inputString) {
        return inputString.replace(/[\\\/\[\]\(\)\{\}\?\+\*\|\.\^\$]/gm,
                   function (c) {
                       return ['\\', c].join('');
                   });
    },

    /** Build HTML tooltip for all array split element.
     * 
     * @param {string} translation Wordlist translation.
     * @param {array} arraySplit Split result array.
     */
    buildTooltip : function(translation, arraySplit) {
        var i;
        for (i = 0; i < arraySplit.length; i += 1) {
            arraySplit[i] = ['<span class="box-wordlist">',
                             '<span class="tooltip-wordlist"',
                             ' tooltip-text="',
                             translation.replace('"','\\"'),
                             '"></span><span class="wordlist">',
                             arraySplit[i],
                             '</span></span>'].join('');
        }
        return arraySplit;
    },

    /** Splice two array without delete item.
     * 
     * @param {array} startArray Start array.
     * @param {array} newItems Split result array.
     * @param {number} position Position to splice input arrays. Value must be greater than 1.
     */
    spliceArray : function(startArray, newItems, position) {
        return startArray.slice(0, position)
            .concat(newItems)
            .concat(startArray.slice(position));
    },

    /** Splice two array with delete item at position.
     * 
     * @param {array} startArray Start array.
     * @param {array} newItems Split result array.
     * @param {number} position Position to splice input arrays. Value must be greater than 1.
     */
    spliceArrayWithDelete : function(startArray, newItems, position) {
        return startArray.slice(0, position - 1)
            .concat(newItems)
            .concat(startArray.slice(position));
    }
};

$(document).ready(function($) {
    $('#submit').prop('disabled',true);
    DDTSS.setupMessagelinks();
    // Language variable is defined in wordlist_page.html.
    DDTSS.retrieveWordlist(TRANSLATE.wordlistUrl, TRANSLATE.highlightWordlist);
})