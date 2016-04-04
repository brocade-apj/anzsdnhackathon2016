jQuery(document).ready(function($) {
  $('#waypoints').select2();

  $('#sr-wizard').on('finished.fu.wizard', function (e, data) {
    createService();
  });
});

function getFormData() {
  var data = {}
  inputs = $(':input').filter(':not("button") [name]');
  $.each(inputs, function(index, input) {
    var $input = $(input);
    if($input.is('select')) {
      val = $input.find('option:selected').val()
    } else {
      val = $input.val();
    }
    data[$input.attr('name')] = val
  });
  console.log(data);
}

function createService() {
  payload = getFormData();
  $.post('/api/v1/services', payload, function(data, textStatus, xhr) {
    console.log(data);
  }, 'json');
}