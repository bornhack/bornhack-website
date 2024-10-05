$( document ).ready(function() {
  const fields = document.querySelectorAll('.markdown-widget');
  fields.forEach((range) => {
    const entity = '#'+range.id;
    const valueEntity = entity + "-value";
    const html = marked.parse($(entity).val())
    $(valueEntity).html(html);
    $(entity).on('input', function(){
      const valueEntity = '#' + $( this )[0].id + "-value";
      const html = marked.parse($( this ).val())
      $(valueEntity).html(html);
    });
  });
});
