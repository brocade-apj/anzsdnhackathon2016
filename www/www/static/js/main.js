jQuery(document).ready(function($) {
  $('#waypoints').select2();

  stopSorting();

  $('#sr-wizard').on('finished.fu.wizard', function (e, data) {
    createService();
  });
});

function getFormData() {
  var data = {}
  inputs = $(':input').filter(':not("button") [name]');
  $.each(inputs, function(index, input) {
    var $input = $(input);
    if($input.attr('name') == 'waypoints'){
      val = $input.val();
    }
    else if($input.is('select')) {
      val = $input.find('option:selected').val()
    } else {
      val = $input.val();
    }
    data[$input.attr('name')] = val
  });
  console.log(data)
  return data
}

function createService() {
  payload = getFormData();
  $.ajax({
    url: '/api/v1/services',
    type: 'POST',
    contentType: "application/json; charset=utf-8",
    data: JSON.stringify(payload),
  })
  .done(function(data) {
    console.log(data);
  });
  
  // $.post('/api/v1/services', payload, function(data, textStatus, xhr) {
  //   console.log(data);
  // }, 'json');
}

function stopSorting() {
  $("#waypoints").on("select2:select", function (evt) {
    var element = evt.params.data.element;
    var $element = $(element);
    
    $element.detach();
    $(this).append($element);
    $(this).trigger("change");
  });
}