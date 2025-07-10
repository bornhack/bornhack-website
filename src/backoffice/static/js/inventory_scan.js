document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  const search_form = document.getElementById("search_form");
  const token_input = document.getElementById("token_input");

  search_form.onsubmit = submit;

  if (document.getElementById("opr_id") && document.getElementById("opr_id")) {
          new Audio('/static/audio/success.mp3').play()
  } else if (document.getElementById("opr_id")) {
    new Audio('/static/audio/tada.mp3').play();
  } else if (!document.getElementById("scan_again").hidden) {
    new Audio('/static/audio/error.mp3').play()
  }

  function submit(e) {
    var product_quantity = document.getElementById("product_quantity");
    e.preventDefault();
    if (token_input.value === "#clear") {
      window.location.replace(window.location.pathname);
    } else if (product_quantity && token_input.value.split("/").length == 4) {
      var quantity = Number(product_quantity.innerHTML)
      var opr = document.getElementById("opr_id").innerHTML
      var scanned_opr = token_input.value.split("/")[3]; 
      token_input.value = "";
      if (opr === scanned_opr) {
        if (quantity > 1) {
          product_quantity.innerHTML = quantity - 1;
          new Audio('/static/audio/success.mp3').play()
        } else {
          if (quantity === 1) {
            product_quantity.innerHTML = "0";
            document.getElementById("checkin_qr").removeAttribute("hidden");;
            new Audio('/static/audio/tada.mp3').play()
          } else {
            new Audio('/static/audio/error.mp3').play()
            token_input.value = "TO MANY ITEMS SCANNED!!!!!";
          }
        }
      } else {
        new Audio('/static/audio/error.mp3').play()
        token_input.value = "WRONG ITEM!!!!!";
      }
    } else {
      search_form.submit();
    }
  }

  document.addEventListener("keydown", event => {
    if (event.key === "#") {
      token_input.value = "";
      token_input.focus();
    }
  });
});
