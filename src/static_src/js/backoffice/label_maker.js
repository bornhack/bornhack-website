function printZpl(zpl) {
  var printWindow = window.open();
  printWindow.document.open('text/plain')
  printWindow.document.write(zpl);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
  window.location.reload();
}
$('#datatable-form').on('submit', function (e) {
  e.preventDefault(); // prevent normal form submit

  var form = $(this);
  var formData = form.serializeArray(); // serialize form including CSRF + all inputs

  // Send AJAX POST to same URL
  $.ajax({
    type: 'POST',
    url: window.location.href,
    data: formData,
    success: function (response) {
      printZpl(response);
    },
    error: function (xhr) {
      alert('Error: ' + xhr.statusText);
    }
  });
});
