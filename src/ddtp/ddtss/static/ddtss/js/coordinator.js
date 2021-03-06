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

// Document ready!
$(document).ready(function($) {
    DDTSS.setupMessagelinks();
    $('#table-coordinators')
        .dataTable(
                {
                    'bSearchable' : false,
                    'bPaginate' : false,
                    'bFilter' : false,
                    'bInfo' : false,
                    'bScrollCollapse': true,
                    'language' : {
                        'emptyTable' : 'No coordinators for this language',
                        'infoEmpty' : 'No coordinators for this language'
                     },
                    'fnRowCallback' : function(nRow, aData,
                            iDisplayIndex, iDisplayIndexFull) {
                        return nRow;
                    }
                });
});
