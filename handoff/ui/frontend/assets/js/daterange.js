$(function() {
  $('input[name="datetimes"]').daterangepicker({
    timePicker: true,
    startDate: moment.utc().startOf('hour').add(-1, 'day'),
    endDate: moment.utc().startOf('hour'),
    locale: {
      format: 'YYYY/MM/DD hh:mm A UTC'
    }
  });
  $('input[name="datetimes"]').on('apply.daterangepicker', function(ev, picker) {
    setStartTimestamp(picker.startDate.unix());
    setEndTimestamp(picker.endDate.unix());
    fetchData();
  });
});

