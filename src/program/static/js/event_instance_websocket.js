const webSocketBridge = new channels.WebSocketBridge();
var modals = {};
var EVENT_INSTANCES, DAYS;

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

webSocketBridge.connect('/schedule/');
webSocketBridge.listen(function(payload, stream) {
    if(payload['action'] == 'event_instance') {
        event_instance_id = payload['event_instance']['id'];
        modal = modals[event_instance_id];
        modal_title = modal.getElementsByClassName('modal-title')[0];
        modal_title.innerHTML = payload['event_instance']['title']
        modal_body_content = modal.getElementsByClassName('modal-body-content')[0];
        modal_body_content.innerHTML = payload['event_instance']['abstract'];
        more_button = modal.getElementsByClassName('more-button')[0];
        more_button.setAttribute('href', payload['event_instance']['url']);
        favorite_button = modal.getElementsByClassName('favorite-button')[0];
        if(payload['event_instance']['is_favorited'] !== undefined) {
            favorite_button.setAttribute('data-state', payload['event_instance']['is_favorited'])
            toggleFavoriteButton(favorite_button);
        } else {
            favorite_button.remove();
        }

        speakers_div = modal.getElementsByClassName('speakers')[0];
        speakers = payload['event_instance']['speakers'];
        for(speaker_id in speakers) {
            var speaker = speakers[speaker_id];
            var speaker_li = document.createElement('li');
            var speaker_a = document.createElement('a');
            speaker_a.setAttribute('href', speaker['url']);
            speaker_a.appendChild(document.createTextNode(speaker['name']));
            speaker_li.appendChild(speaker_a);
            speakers_div.appendChild(speaker_li);
        }
    }
    if(payload['action'] == 'init') {
      EVENT_INSTANCES = payload['event_instances'];
      DAYS = payload['days'];

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

      var type_parameter = findGetParameter('type');
      var types = type_parameter != null ? type_parameter.split(',') : [];
      var location_parameter = findGetParameter('location')
      var locations =  location_parameter != null ? location_parameter.split(',') : [];

      render_schedule(types, locations);
    }
});

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
    return render_day(day, day_event_instances);
  });

  for(day_id in rendered_days) {
    schedule_container.appendChild(rendered_days[day_id]['label']);
    schedule_container.appendChild(rendered_days[day_id]['element']);
  }
}

function render_day(day, event_instances) {
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
    element.dataset.eventInstanceId = event_instance['id'];

    time_element = document.createElement('small');
    time_element.innerHTML = event_instance.from.slice(11, 16) + " - " + event_instance.to.slice(11, 16);

    title_element = document.createElement('p');
    title_element.innerHTML = event_instance['title'];

    element.appendChild(time_element);
    element.appendChild(title_element);
    element.onclick = openModal

    return element
}

function get_instances(types, locations) {
  var event_instances = EVENT_INSTANCES.slice(0);
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

    modal = modals[event_instance_id];

    if(modal == undefined) {
        template = document.getElementById('event-template');
        modal = template.cloneNode(true);
        body = document.getElementsByTagName('body')[0];
        body.appendChild(modal);
        modal.setAttribute('id', 'event-modal-' + event_instance_id)
        modals[event_instance_id] = modal;
    }

    $('#event-modal-' + event_instance_id).modal();
    webSocketBridge.send({action: 'get_event_instance', event_instance_id: event_instance_id})
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
  var event_locations = location_input.map(function(box) {
    return box.value
  })

  var type_part = (types.length == 0) ? [] : ['type='] + types.join(',');
  var location_part = (event_locations.length == 0) ? [] : ['location='] + event_locations.join(',');

  history.pushState({}, '', "?" + type_part + "&" + location_part);

  render_schedule(types, event_locations);
});

