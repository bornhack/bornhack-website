$(document).ready(function(){
    // remove the .noscript class from <body>
    // this allows us to add the class .hide-for-nojs-users to any element as needed
    $('body,html').removeClass("no-js");

    // enable all js tooltips on the page
    $('[data-toggle="tooltip"]').tooltip();

    // define our datetime formats from settings.py
    // Thursday, Aug 27th, 2020, 12:00 (CEST)
    // doesn't work, dates still sort wrong :( halp!
    $.fn.dataTable.moment( "dddd, MMM Do, YYYY, HH:mm" );

    // enable datatables for all tables on the page,
    $('.datatable').DataTable( {
        "stateSave": true,
        "pageLength": 100,
        "lengthMenu": [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
    } );
} );

// function used in speakeravailability form tables to toggle background color
function toggle_sa_form_class(checkboxid) {
    checkbox = $("#" + checkboxid);
    if (checkbox.prop("checked")) {
        checkbox.parent().parent().removeClass("danger warning active").addClass("success");
    } else {
        checkbox.parent().parent().removeClass("success warning active").addClass("danger");
    };
};
