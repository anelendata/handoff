var logStart = Math.floor(Date.now() / 1000) - 24 * 60 * 60
var statsStart = Math.floor(Date.now() / 1000) - 14 * 24 * 60 * 60
var path = window.location.pathname.split('/')
var project = path[path.length - 1]
var projectID = document.getElementById('project-id');
projectID.textContent = project;

var chart = new Highcharts.Chart({
  chart: {
     renderTo: 'chart-area',
     zoomType: 'x',
     defaultSeriesType: 'column'
  },
  credits: {
     enabled: false
  },
  title: {
     text: 'Extraction volume'
  },
  subtitle: {
      text: 'Click and drag in the plot area to zoom in'
  },
  xAxis: {
    type: 'datetime'
  },
  yAxis: {
     min: 0,
     title: {
        text: 'Rows'
     }
  },
  plotOptions: {
    series: {
        pointWidth: 10,
        groupPadding: 0.5
    }
  },
  tooltip: {
    formatter: function() {
      var rows = this.y;
      return '<strong>'+ this.series.name +'</strong><br>'+ Highcharts.dateFormat('%A %e %B, %l:%M%P', this.x) +'<br>Rows: '+ Math.floor(rows);
    }
  },

  series: [
    {"name": project,
     "type":"column",
     "data":[
       [Date.now(),0.0]
     ]
    },
  ]
});

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function pollLog() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + project + '/log?start_time=' + logStart);
  xhr.send();
  await sleep(2000);
  var output = document.getElementById('log-area');
  output.textContent = xhr.responseText;
}

async function pollStats() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + project + '/stats?start_time=' + statsStart);
  xhr.send();
  data = new Array();
  await sleep(2000);
  var lines = xhr.responseText.split(/\n/);
  lines.forEach(function(item, index) {
    try {
      obj = JSON.parse(item);
    } catch (error) {
      console.log(error);
    };
    if (obj['message']['metric'] == 'record_count') {
      data.push([new Date(obj['datetime']).getTime() - 8 * 60 * 60 * 1000, obj['message']['value']]);
    }
  });
  console.info(data)
  chart.series[0].update({data: data}, true);
}

async function runNow(target_id) {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + project + '/run?target_id=' + target_id);
  xhr.send();
  await sleep(2000);
  res = JSON.parse(xhr.responseText);
  console.info(res);
  setInterval(pollLog, 5000);
  setInterval(pollStats, 5000);
};

async function getSchedule() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + project +'/schedules');
  xhr.send();
  await sleep(2000);
  res = JSON.parse(xhr.responseText);
  var htmlOut = '';
  res['schedules'].forEach(function(s) {
    var h = '<tr><td><a class="btn btn-primary btn-sm d-none d-sm-inline-block" role="button" id="run-now" href="#" onclick="runNow(' +
        s['target_id'] +
        ');" style="background: #00599C;"><i class="fas fa-play fa-sm text-white-50"></i>&nbsp;Run Now</a> </td><td>' +
        s['target_id'] + '</td><td>' + s['cron'] + '</td><td>';
    s['envs'].forEach(function(e) {
      h = h + e['key'] + ": '" + e['value'] + "', ";
    });
    h = h + '</td></tr>';
    htmlOut += h;
  });
  var output = document.getElementById('schedule');
  output.innerHTML = htmlOut;
}

async function getStatus() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + project +'/status');
  xhr.send();
  await sleep(2000);
  res = JSON.parse(xhr.responseText);
  var htmlOut = '';
  if (res === null) return;
  res.forEach(function(s) {
  var h = '<tr><td>' + s['taskArn'] + '</td><td>' +
      s['lastStatus'] + '</td><td>' +
      s['createdAt'] + '</td><td>' +
      s['startedAt'] + '</td><td>' +
      s['duration'] + '</td><td>' +
      s['cpu'] + '</td><td>' +
      s['memory'] + '</td></tr>'
    ;
    htmlOut += h;
  });

  var output = document.getElementById('status');
  // output.textContent = JSON.stringify(res, undefined, 4);
  output.innerHTML= htmlOut;
}

getSchedule();
setInterval(pollLog, 5000);
setInterval(pollStats, 10000);
setInterval(getStatus, 5000);
