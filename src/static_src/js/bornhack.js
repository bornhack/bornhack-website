$(document).ready(function(){
    // remove the .noscript class from <body>
    // this allows us to add the class .hide-for-nojs-users to any element as needed
    $('body,html').removeClass("no-js");

    // enable all js tooltips on the page
    $('[data-bs-toggle="tooltip"]').tooltip();

    // define our datetime formats from settings.py
    // Thursday, Aug 27th, 2020, 12:00 (CEST)
    // doesn't work, dates still sort wrong :( halp!
    //DataTable.datetime( "dddd, MMM Do, YYYY, HH:mm" );

    // enable datatables for all tables on the page,
    $('.datatable').DataTable( {
        "stateSave": true,
        "pageLength": 100,
        "format": "dddd, MMM Do, YYYY, HH:mm",
        "lengthMenu": [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
        "responsive": true,
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

document.addEventListener('DOMContentLoaded', function () {
  //Pick tab based on url hash/fragment
  const urlHash = window.location.hash;
  //Test is there are tabs
  const triggerTabOnLoad = document.querySelector(`[data-bs-target="${urlHash}"]`);

  if (triggerTabOnLoad) {
    const tab = new bootstrap.Tab(triggerTabOnLoad);
    tab.show();
  }

  // Update URL hash on tab click
  const tabButtons = document.querySelectorAll('a[data-bs-toggle="tab"]');
  tabButtons.forEach(button => {
    button.addEventListener('show.bs.tab', event => {
      const targetId = event.target.getAttribute('data-bs-target');
      window.location.hash = targetId;
    });
  });
});
