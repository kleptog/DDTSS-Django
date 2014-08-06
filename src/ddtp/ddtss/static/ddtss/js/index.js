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

var INDEX = {
    // Wordlist DataTable.
    languagesTable : undefined,

    init : function() {
        this.languagesTable = $('#table-languages')
        .dataTable(
                {
                    'bSearchable' : false,
                    'bPaginate' : false,
                    'bFilter' : false,
                    'bInfo' : false,
                    'bScrollCollapse': true,
                    'language' : {
                        'emptyTable' : 'DDTSS without languages enabled!! This is very embarrassing :(',
                        'infoEmpty' : 'DDTSS without languages enabled!! This is very embarrassing :('
                     },
                    'fnRowCallback' : function(nRow, aData,
                            iDisplayIndex, iDisplayIndexFull) {
                        return nRow;
                    }
                });
        new $.fn.dataTable.FixedHeader( this.languagesTable );
        // Sort table by Translated column.
        this.languagesTable.fnSort([ [ 3, 'desc' ] ]);
    }
};

// Document ready!
$(document).ready(function() {
    INDEX.init();
});
