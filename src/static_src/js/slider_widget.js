$( document ).ready(function() {
  const fields = document.querySelectorAll('input[type="range"]');
  fields.forEach((range) => {
    $('#'+range.id).on('input', function(){
      console.log($( this )[0].id)
      $('#' + $( this )[0].id + "-value").text($( this ).val());
    });
  });
});
