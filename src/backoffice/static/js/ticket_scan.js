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
    } else if (ticket_token_input.value === "#check-in") {
      check_in_input.checked = true;
      check_in_form.submit();
    } else if (ticket_token_input.value === "#hand-out-badge") {
      hand_out_badge_input.checked = true;
      check_in_form.submit();
    } else if (ticket_token_input.value.length === 65) {
      search_form.submit();
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
