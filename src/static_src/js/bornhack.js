$(document).ready(function(){
    // enable all js tooltips on the page
    $('[data-toggle="tooltip"]').tooltip();

    // define our datetime formats from settings.py
    // Thursday, Aug 27th, 2020, 12:00 (CEST)
    // doesn't work, dates still sort wrong :( halp!
    $.fn.dataTable.moment( "dddd, MMM Do, YYYY, HH:mm" );

    // enable datatables for all tables on the page,
    $('.datatable').DataTable();

    // remove the .noscript class from <body>
    // add the class .hide-for-nojs-users to any element as needed
    $('body,html').removeClass("no-js");
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
