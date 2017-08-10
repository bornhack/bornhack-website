const webSocketBridge = new channels.WebSocketBridge();
var modals = {};
var EVENT_INSTANCES = [], DAYS = [], CONFIG = {};

function toggleFavoriteButton(button) {
    if(button.getAttribute('data-state') == 'true') {
        favorite_button.classList.remove('btn-success');
        favorite_button.classList.add('btn-danger');
        favorite_button.innerHTML = '<i class="fa fa-minus"></i> Remove favorite';

        favorite_button.onclick = function(e) {
            button.setAttribute('data-state', 'false')
            webSocketBridge.send({action: 'unfavorite', event_instance_id: event_instance_id});
            toggleFavoriteButton(button)
        }
    } else {
        favorite_button.classList.remove('btn-danger');
        favorite_button.classList.add('btn-success');
        favorite_button.innerHTML = '<i class="fa fa-star"></i> Favorite';

        favorite_button.onclick = function(e) {
            button.setAttribute('data-state', 'true')
            webSocketBridge.send({action: 'favorite', event_instance_id: event_instance_id});
            toggleFavoriteButton(button)
        }

    }
}

function setup_websocket() {
  webSocketBridge.connect('/schedule/');
  webSocketBridge.listen(function(payload, stream) {
      if(payload['action'] == 'init') {
        EVENT_INSTANCES = payload['event_instances'];
        DAYS = payload['days'];
        render();
      }
  });
}

function init(config) {
    CONFIG = config;
    setup_websocket();
    render();
}

function findGetParameter(parameterName) {
    var result = null,
        tmp = [];
    location.search
      .substr(1)
      .split("&")
      .forEach(function (item) {
        tmp = item.split("=");
        if (tmp[0] === parameterName) {
           result = decodeURIComponent(tmp[1]);
        }
      });
    return result;
}

function get_parameters() {

    var day_parameter = findGetParameter('day');
    var filter_day = day_parameter != null ? day_parameter.split(',') : [];
    var type_parameter = findGetParameter('type');
    var filter_types = type_parameter != null ? type_parameter.split(',') : [];
    var location_parameter = findGetParameter('location')
    var filter_locations =  location_parameter != null ? location_parameter.split(',') : [];

    return {
      'day': filter_day[0],
      'types': filter_types,
      'locations': filter_locations
    }
}

function render() {
    parameters = get_parameters();
    toggleFilterBoxes(parameters['types'], parameters['locations']);
    render_day_menu(parameters['day']);
    setICSButtonHref(location.search);

    if(parameters['day'] != null) {
      render_day(parameters['types'], parameters['locations'], parameters['day']);
    } else {
      render_schedule(parameters['types'], parameters['locations']);
    }
}

function render_day_menu(active_iso) {
  var container = document.getElementById('schedule-days');
  container.innerHTML = '';

  var mobile_container = document.getElementById('schedule-days-mobile');
  mobile_container.innerHTML = '';

  function set_btn_type(classList, primary) {
    if(primary == true) {
      classList.add('btn-primary');
    } else {
      classList.add('btn-default');
    }
  }

  function dayEvent(e) {
    setHistoryState({
      'day': this.dataset.iso
    });
    render();
  }

  var all_days = document.createElement('a');
  all_days.classList.add('btn');
  set_btn_type(all_days.classList, active_iso == null);
  all_days.innerHTML = 'All days';
  all_days.dataset.iso = 'all-days';
  all_days.addEventListener('click', dayEvent);
  container.appendChild(all_days);

  all_days_mobile = all_days.cloneNode(true);
  all_days_mobile.addEventListener('click', dayEvent);
  mobile_container.appendChild(all_days_mobile);

  for(var day_id in DAYS) {
    var day_link = document.createElement('a');
    day_link.classList.add('btn');
    set_btn_type(day_link.classList, DAYS[day_id]['iso'] == active_iso);
    day_link.dataset.iso = DAYS[day_id]['iso'];
    day_link.innerHTML = DAYS[day_id]['day_name'];

    day_link.addEventListener('click', dayEvent);
    container.appendChild(day_link);

    day_link_mobile = day_link.cloneNode(true);
    day_link_mobile.addEventListener('click', dayEvent);
    mobile_container.appendChild(day_link_mobile);
  }
}

function render_day(types, locations, day) {

  function hoursTohhmm(hours){
    var hour = Math.floor(Math.abs(hours));
    var minutes = Math.floor((Math.abs(hours) * 60) % 60);
    if(hour > 24) {
      hour = hour - 24;
    }
    return (hour < 10 ? "0" : "") + hour + ":" + (minutes < 10 ? "0" : "") + minutes;
  }

  var event_instances = get_instances(types, locations, day);
  var schedule_container = document.getElementById('schedule-container');
  schedule_container.innerHTML = '';

  var day_table = document.createElement('table');
  schedule_container.appendChild(day_table);
  day_table.classList.add('table');
  day_table.classList.add('day-table');
  day_table_body = document.createElement('tbody');
  day_table.appendChild(day_table_body);

  var array_length = (24*60)/CONFIG['schedule_timeslot_length_minutes'];
  var timeslots_ = Array(array_length);
  var timeslots = [];
  for(var i=0; i<timeslots_.length; i++) {
    timeslots.push(
        { 'offset': i * CONFIG['schedule_timeslot_length_minutes']
        , 'minutes_since_midnight': (CONFIG['schedule_midnight_offset_hours'] * 60) + (i * CONFIG['schedule_timeslot_length_minutes'])
        }
    );
  }

  var timeslot_trs = {};
  for(var timeslots_index in timeslots) {
    var timeslot_tr = document.createElement('tr');
    day_table_body.appendChild(timeslot_tr);
    var timeslot_td = document.createElement('td');
    timeslot_tr.appendChild(timeslot_td);

    var minutes_since_midnight = timeslots[timeslots_index]['minutes_since_midnight'];
    if(minutes_since_midnight / 60 % 1 == 0) {
      timeslot_td.innerHTML = hoursTohhmm(minutes_since_midnight / 60);
    }
    timeslot_trs[hoursTohhmm(minutes_since_midnight / 60)] = timeslot_tr;
  }
  for(var event_instances_index in event_instances) {
    var event_instance = event_instances[event_instances_index];
    var event_instance_td = document.createElement('td');
    event_instance_td.innerHTML = event_instance['title'];
    event_instance_td.setAttribute('rowspan', event_instance['timeslots']);
    event_instance_td.classList.add('event-td');
    event_instance_td.setAttribute(
        'style',
        'background-color: ' + event_instance['bg-color'] +
        '; color: ' + event_instance['fg-color']);
    event_instance_td.onclick = openModal
    event_instance_td.dataset.eventInstanceId = event_instance['id'];

    var timeslot_tr = timeslot_trs[event_instance.from.slice(11, 16)];

    timeslot_tr.appendChild(event_instance_td);
  }
}

function render_schedule(types, locations) {
  var event_instances = get_instances(types, locations);
  var schedule_container = document.getElementById('schedule-container');
  schedule_container.innerHTML = "";

  var cloned_days = DAYS.slice(0);

  var rendered_days = cloned_days.map(function(day) {
    day_event_instances = event_instances.slice(0).filter(
      function(event_instance) {
        var event_day = event_instance['from'].slice(0, 10);
        return event_day == day['iso'];
      }
    );
    return render_schedule_day(day, day_event_instances);
  });

  for(day_id in rendered_days) {
    schedule_container.appendChild(rendered_days[day_id]['label']);
    schedule_container.appendChild(rendered_days[day_id]['element']);
  }
}

function render_schedule_day(day, event_instances) {
    var element = document.createElement('div');
    element.classList.add('schedule-day-row');
    var day_label = document.createElement('h4');
    day_label.innerHTML = day['repr'];
    element.appendChild(day_label);
    for(event_instance_id in event_instances) {
      var event_instance = event_instances[event_instance_id];
      var rendered_event_instance = render_event_instance(event_instance);
      element.appendChild(rendered_event_instance);
    }
    return {"label": day_label, "element": element};
}

function render_event_instance(event_instance) {
    var element = document.createElement('a');
    element.setAttribute(
        'style',
        'background-color: ' + event_instance['bg-color'] +
        '; color: ' + event_instance['fg-color']);
    element.classList.add('event');
    element.setAttribute('href', event_instance['url']);
    element.dataset.eventInstanceId = event_instance['id'];

    time_element = document.createElement('small');
    time_element.innerHTML = event_instance.from.slice(11, 16) + " - " + event_instance.to.slice(11, 16);

    title_element = document.createElement('p');
    title_element.innerHTML = event_instance['title'];

    icon_element = document.createElement('i');
    icon_element.classList.add('fa-' + event_instance['location_icon']);
    icon_element.classList.add('fa');
    icon_element.classList.add('pull-right');

    if(event_instance['video_url'] != undefined) {
      video_url_element = document.createElement('i');
      video_url_element.classList.add('fa-film');
      video_url_element.classList.add('fa');
      video_url_element.classList.add('pull-right');
      element.appendChild(video_url_element);
    } else if(event_instance['video_recording'] == true) {
      video_recording_element = document.createElement('i');
      video_recording_element.classList.add('fa-video-camera');
      video_recording_element.classList.add('fa');
      video_recording_element.classList.add('pull-right');
      element.appendChild(video_recording_element);
    }

    element.appendChild(time_element);
    element.appendChild(icon_element);
    element.appendChild(title_element);

    element.onclick = openModal

    return element
}

function get_instances(types, locations, day) {
  var event_instances = EVENT_INSTANCES.slice(0);
  if(day != undefined && day != null) {
    event_instances = event_instances.filter(
      function(event_instance) {
        return event_instance.from.slice(0, 10) == day;
      }
    );
  }
  if(locations.length != 0) {
    event_instances = event_instances.filter(
      function(event_instance) {
        return locations.includes(event_instance['location']);
      }
    );
  }
  if(types.length != 0) {
    event_instances = event_instances.filter(
      function(event_instance) {
        return types.includes(event_instance['event_type']);
      }
    );
  }
  return event_instances
}

function openModal(e) {
    e.preventDefault();

    // Avoid that clicking the text in the event will bring up an empty modal
    target = e.target;
    if (e.target !== this) {
        target = e.target.parentElement
    }

    event_instance_id = target.dataset.eventInstanceId;
    event_instance = EVENT_INSTANCES.filter(
        function(event_instance) {
            return event_instance.id == event_instance_id
        }
    )[0];

    modal = modals[event_instance_id];

    if(modal == undefined) {
        modal = document.createElement('div');
        modal.classList.add('modal');
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('role', 'dialog');

        modal_dialog = document.createElement('div');
        modal_dialog.classList.add('modal-dialog');
        modal.setAttribute('role', 'document');
        modal.appendChild(modal_dialog);

        modal_content = document.createElement('div');
        modal_content.classList.add('modal-content');
        modal_dialog.appendChild(modal_content);

        modal_header = document.createElement('div');
        modal_header.classList.add('modal-header');
        modal_content.appendChild(modal_header);

        modal_close_button = document.createElement('button');
        modal_close_button.setAttribute('type', 'button');
        modal_close_button.setAttribute('aria-label', 'Close');
        modal_close_button.dataset.dismiss = 'modal';
        modal_close_button.classList.add('close');
        modal_close_button.innerHTML = '<span aria-hidden="true">&times;</span></button>';

        modal_title = document.createElement('h4');
        modal_title.classList.add('modal-title')
        modal_title.innerHTML = event_instance['title'];

        modal_header.appendChild(modal_close_button);
        modal_header.appendChild(modal_title);

        modal_body_content = document.createElement('div');
        modal_body_content.classList.add('modal-body');
        modal_body_content.classList.add('modal-body-content');
        modal_body_content.innerHTML = event_instance['abstract'];
        modal_content.appendChild(modal_body_content);

        modal_body = document.createElement('div');
        modal_body.classList.add('modal-body');
        speakers_h4 = document.createElement('h4');
        speakers_h4.innerHTML = 'Speaker(s):';
        speakers_ul = document.createElement('ul');
        speakers_ul.classList.add('speakers');

        speakers = event_instance['speakers'];
        for(speaker_id in speakers) {
            var speaker = speakers[speaker_id];
            var speaker_li = document.createElement('li');
            var speaker_a = document.createElement('a');
            speaker_a.setAttribute('href', speaker['url']);
            speaker_a.appendChild(document.createTextNode(speaker['name']));
            speaker_li.appendChild(speaker_a);
            speakers_ul.appendChild(speaker_li);
        }

        video_recording_div = document.createElement('div');
        video_recording_div.classList.add('alert');
        video_recording_div.classList.add('alert-info');
        video_recording_div.classList.add('video-recording');

        if(event_instance['video_url'] != undefined) {
          // We have an URL to the video
          video_url_icon = document.createElement('i');
          video_url_icon.classList.add('fa');
          video_url_icon.classList.add('fa-film');
          video_url_link = document.createElement('a');
          video_url_link.setAttribute('href', event_instance['video_url']);
          video_url_link.setAttribute('target', '_blank');
          video_url_link.innerHTML = " Watch the video recording here!";

          video_recording_div.appendChild(video_url_icon);
          video_recording_div.appendChild(video_url_link);

        } else if(event_instance['video_recording'] == true) {
          // This instance will be recorded
          video_notice_icon = document.createElement('i');
          video_notice_icon.classList.add('fa');
          video_notice_icon.classList.add('fa-camera');
          video_notice_span = document.createElement('span');
          video_notice_span.innerHTML = " This event will be recorded!";

          video_recording_div.appendChild(video_notice_icon);
          video_recording_div.appendChild(video_notice_span);
        } else {
          // This instance will NOT be recorded!
          video_recording_element.remove();
        }

        modal_body.appendChild(speakers_h4);
        modal_body.appendChild(speakers_ul);
        modal_body.appendChild(video_recording_div);

        modal_content.appendChild(modal_body);

        modal_footer = document.createElement('div');
        modal_footer.classList.add('modal-footer');
        modal_content.appendChild(modal_footer);

        close_button = document.createElement('button');
        close_button.setAttribute('type', 'button');
        close_button.classList.add('btn');
        close_button.classList.add('btn-default');
        close_button.classList.add('pull-left');
        close_button.dataset.dismiss = "modal";
        close_button.innerHTML = "Close";
        modal_footer.appendChild(close_button);

        favorite_button = document.createElement('a');
        favorite_button.classList.add('btn');
        favorite_button.classList.add('btn-success');
        favorite_button.classList.add('favorite-button');
        favorite_button.innerHTML = '<i class="fa fa-star"></i> Favorite</a>';
        if(event_instance['is_favorited'] !== undefined) {
            favorite_button.setAttribute('data-state', event_instance['is_favorited'])
            toggleFavoriteButton(favorite_button);
        } else {
            favorite_button.remove();
        }

        modal_footer.appendChild(favorite_button);

        more_button = document.createElement('a');
        more_button.classList.add('btn');
        more_button.classList.add('btn-info');
        more_button.classList.add('more-button');
        more_button.setAttribute('href', event_instance['url']);
        more_button.innerHTML = '<i class="fa fa-info"></i> More</a>';
        modal_footer.appendChild(more_button);

        body = document.getElementsByTagName('body')[0];
        body.appendChild(modal);
        modal.setAttribute('id', 'event-modal-' + event_instance_id)
        modals[event_instance_id] = modal;
    }

    $('#event-modal-' + event_instance_id).modal();
}

function init_modals(event_class_name) {
  var event_elements = document.getElementsByClassName(event_class_name);

  for (var event_id in event_elements) {
      event_element = event_elements.item(event_id);
      if(event_element != null) {
        event_element.onclick = openModal
      }
  }
}

var filter = document.getElementById('filter')
filter.addEventListener('change', function(e) {
  var type_input = Array.prototype.slice.call(document.querySelectorAll('.event-type-checkbox:checked'));
  var types = type_input.map(function(box) {
    return box.value
  })
  var location_input = Array.prototype.slice.call(document.querySelectorAll('.location-checkbox:checked'));
  var locations = location_input.map(function(box) {
    return box.value
  })

  toggleFilterBoxes(types, locations);
  setHistoryState({
    'types': types,
    'locations': locations
  });
  render();
});


function setHistoryState(parts) {

  var day = parts['day'];
  var types = parts['types'];
  var locations = parts['locations'];

  var query = '?';

  day = day == undefined ? findGetParameter('day') : day;
  if(day != null && day != 'all-days') {
    query = query + "day=" + day + "&";
  }

  types = types == undefined ? findGetParameter('type') : types.join(',');
  if(types != null && types.length > 0) {
    var type_part = 'type=' + types;
    query = query + type_part + "&";
  }

  locations = locations == undefined ? findGetParameter('location') : locations.join(',');
  if(locations != null && locations.length > 0) {
    var location_part = 'location=' + locations;
    query = query + location_part;
  }

  history.replaceState({}, '', query);
  setICSButtonHref(query);
}

function setICSButtonHref(query) {
  // Update ICS button as well
  var ics_button = document.querySelector('#ics-button');
  ics_button.setAttribute('href', CONFIG['ics_button_href'] + query);
}

function toggleFilterBoxes(types, locations) {
  var type_input = Array.prototype.slice.call(document.querySelectorAll('.event-type-checkbox'));
  type_input.map(function(box) {
    if(types.includes(box.value)) {
      box.checked = true;
    }
    return box;
  });
  var location_input = Array.prototype.slice.call(document.querySelectorAll('.location-checkbox'));
  location_input.map(function(box) {
    if(locations.includes(box.value)) {
      box.checked = true;
    }
    return box;
  });
}
