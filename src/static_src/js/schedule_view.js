window.addEventListener('DOMContentLoaded', () => {
  // If the user already scrolled down before DOMContentLoaded we dont mess with the scroll
  const scrollIntoView = (document.scrollingElement && document.scrollingElement.scrollTop === 0)
  findCurrentTimeSlot(new Date(), scrollIntoView)

  // update the time indicator every minute
  setInterval(() => findCurrentTimeSlot(new Date()), 1 * 60 * 1000)

  function findCurrentTimeSlot(now, scrollIntoView) {
    [ ...document.querySelectorAll(`[data-event-date-lower^="${now.toJSON().substr(0,10)}"]`) ]
      .filter(el => {
        const lower = new Date(el.getAttribute('data-event-date-lower'))
        const upper = new Date(el.getAttribute('data-event-date-upper'))
        return lower < now && upper > now
      })
      .forEach(el => {
        if (scrollIntoView) {
          el.scrollIntoView({behavior:"smooth", block:"center"})
        }
        el.querySelector('td').style.background = "#8f8"
      })
  }
});
