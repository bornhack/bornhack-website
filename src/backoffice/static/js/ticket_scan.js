document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  const search_form = document.getElementById("search_form");
  const ticket_token_input = document.getElementById("ticket_token_input");
  const scan_again = document.getElementById("scan_again");

  const check_in_input = document.getElementById("check_in_input");
  const hand_out_badge_input = document.getElementById("hand_out_badge_input");
  const check_in_form = document.getElementById("check_in_form");

  search_form.onsubmit = submit;

  function submit(e) {
    e.preventDefault();

    if (ticket_token_input.value === "#clear") {
      window.location.replace(window.location.pathname);
    } else if (ticket_token_input.value === "#checkin") {
      check_in_input.checked = true;
      check_in_form.submit();
    } else if (ticket_token_input.value === "#handoutbadge") {
      hand_out_badge_input.checked = true;
      check_in_form.submit();
    } else if (ticket_token_input.value.length === 65) {
      search_form.submit();
    } else if (ticket_token_input.value.startsWith("#bornhack://opr/")) {
      var oprelement = document.getElementById("opr");
      if (oprelement) {
        var opr = oprelement.innerHTML
        var quantity = document.getElementById("product_quantity");
        var opr_scanned = ticket_token_input.value.split("/")[3]
        if (opr == opr_scanned) {
          if (quantity && quantity.innerHTML=="1") {
            quantity.innerHTML = Number(quantity.innerHTML) - 1;
          } else {
            document.getElementById("checkin_qr").removeAttribute("hidden");
          }
          ticket_token_input.value = "";
        } else {
          ticket_token_input.value = "WRONG ITEM";
        }
      } else {
        scan_again.removeAttribute("hidden");
        ticket_token_input.value = ""
      }
    } else {
      scan_again.removeAttribute("hidden");
    }
  }

  document.addEventListener("keydown", event => {
    if (event.key === "#") {
      ticket_token_input.value = "";
      ticket_token_input.focus();
    }
  });

});
