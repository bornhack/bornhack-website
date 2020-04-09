$(document).ready(function(){
    // enable all js tooltips on the page
    $('[data-toggle="tooltip"]').tooltip();

    // define our datetime formats from settings.py
    // Thursday, Aug 27th, 2020, 12:00 (CEST)
    // doesn't work, dates still sort wrong :( halp!
    $.fn.dataTable.moment( "dddd, MMM Do, YYYY, HH:mm" );
    // enable datatables for all tables on the page,
    $('.datatable').DataTable();
} );
