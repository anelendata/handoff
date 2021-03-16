$(function() {
  $('input[name="datetimes"]').daterangepicker({
    timePicker: true,
    startDate: moment().startOf('hour').add(-3, 'day'),
    endDate: moment().startOf('hour'),
    locale: {
      format: 'M/DD hh:mm A'
    }
  });
  $('input[name="datetimes"]').on('apply.daterangepicker', function(ev, picker) {
    fetchData(picker.startDate.unix(), picker.endDate.unix());
  });
});

