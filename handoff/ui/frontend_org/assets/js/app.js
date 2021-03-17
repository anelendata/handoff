var path = window.location.pathname.split('/')

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
    {"name": getProjectID(),
     "type":"column",
     "data":[
       [Date.now(),0.0]
     ]
    },
  ]
});

function setRepositoryID(repositoryID) {
  if (repositoryID != getRepositoryID()){
    setProjectID(null);
  }
  document.getElementById('repository-id').textContent = repositoryID;
  fetchProjectList();
}

function getRepositoryID() {
  var repository = document.getElementById('repository-id').textContent;
  if (repository === '') repository = null;
  return repository;
}

function setProjectID(projectID) {
  document.getElementById('project-id').textContent = projectID;
  fetchData();
}

function getProjectID() {
  var projectID = document.getElementById('project-id').textContent;
  if (projectID === '') projectID = null;
  return projectID
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchRepositoryList() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/repositories');
  xhr.onload = function(e) {
    var output = document.getElementById('repositories');
    records = JSON.parse(xhr.responseText);
    htmlOut = '';
    records.forEach(function(obj, index) {
       htmlOut += '<a class="dropdown-item" href="#" onclick="setRepositoryID(\'' + obj + '\')">' + obj + '</a>'
    });
    output.innerHTML = htmlOut;
  }
  xhr.send();
}

async function fetchProjectList() {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/projects');
  xhr.onload = function(e) {
    var output = document.getElementById('projects');
    xhr.responseText;
    records = JSON.parse(xhr.responseText);
    htmlOut = '';
    records.forEach(function(obj, index) {
       htmlOut += '<a class="dropdown-item" href="#" onclick="setProjectID(\'' + obj + '\')">' + obj + '</a>'
    });
    output.innerHTML = htmlOut;
  }
  xhr.send();
}

var log_text = '';
function updateLogArea(text) {
  log_text = text;
  var output = document.getElementById('log-area');
  filter_term = document.getElementById('filter-term').value;
  logs = text.split('\n').sort();
  filtered_text = '';  
  if (filter_term != undefined & filter_term.length > 0) {
    last = 0;
    for (i = 0; i < logs.length; i++) {
        if (logs[i].toLowerCase().includes(filter_term.toLowerCase())) {
            end_chunk = Math.min(logs.length - 1, i + 10);
            for (j = Math.max(last, i - 10); j <= end_chunk; j++) {
                filtered_text += logs[j] + '\n';
            }
            if (end_chunk < logs.length - 1) {
                filtered_text += '...\n...\n...\n';
            }
            i = end_chunk;
            last = end_chunk;
        }
    }  
  } else {
    for (i = 0; i < logs.length; i++) {
        filtered_text += logs[i] + '\n'
    }      
  }
  output.textContent = filtered_text;
  output.parentElement.parentElement.scrollTop = output.parentElement.parentElement.scrollHeight;  
  // output.textContent = xhr.responseText.replace(/\d{12}/g, '******');    
}

async function pollLog(startTimestamp, endTimestamp) {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/log?start_time=' + startTimestamp + '&end_time=' + endTimestamp);
  xhr.onload = function(e) {
    updateLogArea(xhr.responseText);
  }
  xhr.send();
}

async function pollStats(startTimestamp, endTimestamp) {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/stats?start_time=' + startTimestamp + '&end_time=' + endTimestamp);
  xhr.onload = function(e) {
    data = new Array();
    records = JSON.parse(xhr.responseText);
    records.forEach(function(obj, index) {
      if (obj['message'] && obj['message']['metric'] == 'record_count') {
        data.push([new Date(obj['datetime']).getTime() /* - 8 * 60 * 60 * 1000 */,
          obj['message']['value']]);
      }
    });
    console.info(data);
    chart.series[0].update({name: project, data: data}, true);
  }
  xhr.send();
}

async function runNow(target_id) {
  var confirm = window.confirm('Run ' + project + ' project target ' + target_id + '?');
  if (!confirm) {
    return;
  }    
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + repository + '/' + project + '/run?target_id=' + target_id);
  xhr.onload = function(e) {
    res = JSON.parse(xhr.responseText);
    console.info(res);
  }
  xhr.send();
}

async function getSchedule() {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project +'/schedules');
  xhr.onload = function(e) {
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
  xhr.send();
}

async function getStatus() {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID()
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project +'/status');
  xhr.onload = function(e) {
    res = JSON.parse(xhr.responseText);
    var htmlOut = '';
    if (res === null) return;
    res.forEach(function(s) {
    var h = '<tr><td>' + s['taskArn'] + '</td><td>' +
    // var h = '<tr><td>' + s['taskArn'].replace(/\d{12}/, '******') + '</td><td>' +        
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
  xhr.send();
}

function fetchData(startTimestamp, endTimestamp) {
  if (startTimestamp === undefined) startTimestamp = moment().add(-3, 'day').unix();
  if (endTimestamp === undefined) endTimestamp = moment().unix();
  fetchRepositoryList();
  fetchProjectList();
  getStatus();    
  getSchedule();
  pollLog(startTimestamp, endTimestamp);
  pollStats(startTimestamp, endTimestamp);
}

fetchData();