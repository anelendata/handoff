function login() {    
  username = $('#inputEmail').val();
  password = $('#inputPassword').val();
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/token', true);
  xhr.onload = function(e) {
    response = JSON.parse(xhr.responseText);
    if (response['access_token'] != undefined) {
      token = response['access_token'];
      postLogin(token);
      sessionStorage.SessionName = 'handoff';
      sessionStorage.setItem("token", token);              
    }
  }
  data = new FormData();
  data.append('username', username);
  data.append('password', password)
  xhr.send(data);
}

function showLoginModal() {
  $("#login-modal").modal({
    backdrop: 'static',
    keyboard: false
  });
  $('#login-modal').modal('show');    
}

function postLogin(token) {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/users/me/');
  xhr.setRequestHeader('accept', 'application/json', false);
  xhr.setRequestHeader('Authorization', 'Bearer ' + token, false);
  xhr.onload = function(e) {
    response = JSON.parse(xhr.responseText);
    $('#profile-image')[0].src = response['profile_url']
    $('#login-modal').modal('hide');    
    document.getElementById('user-menu').innerHTML = 
      '<a class="dropdown-item" href="#"><i class="fas fa-user fa-sm fa-fw mr-2 text-gray-400"></i> Profile</a><a class="dropdown-item" href="#"><i class="fas fa-cogs fa-sm fa-fw mr-2 text-gray-400"></i> Settings</a><a class="dropdown-item" href="#"><i class="fas fa-list fa-sm fa-fw mr-2 text-gray-400"></i> Activity log</a><div class="dropdown-divider"></div><a class="dropdown-item" href="#" onclick="logout()"><i class="fas fa-sign-out-alt fa-sm fa-fw mr-2 text-gray-400"></i> Logout</a>';      
  }
  xhr.send();
}

function logout() {
    sessionStorage.removeItem("token");
    document.getElementById('user-menu').innerHTML = '<a class="dropdown-item" id="login" href="#" onclick="showLoginModal()"><i class="fas fa-sign-in-alt fa-sm fa-fw mr-2 text-gray-400"></i> Login</a>';
    $('#profile-image')[0].src = 'https://gravatar.com/avatar/0';
    showLoginModal();
}

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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/* get set
*/
function getStage() {
    if (document.getElementById('stage').value == '0') return 'dev';
    return 'prod';
}

var startTimestamp = null;
function setStartTimestamp(ts) {
    startTimestamp = ts;
}
function setEndTimestamp(ts) {
    endTimestamp = ts;
}

var endTimestamp = null;
function getStartTimestamp() {
  if (startTimestamp === null) startTimestamp = moment().add(-3, 'day').unix();
  return startTimestamp;
}
function getEndTimestamp() {
  if (endTimestamp === null) endTimestamp = moment().unix();
  return endTimestamp;
}

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

var projectFiles = null;
function getProjectFiles() {
    return projectFiles;
}
function setProjectFiles(files) {
    projectFiles = files;
}

/* Fetch
*/
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

async function fetchProjectFiles() {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  if (project === null) return [];
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/files');
  xhr.onload = function(e) {
    setProjectFiles(JSON.parse(xhr.responseText));
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
        filtered_text += logs[i].replace(/[0-9]{8}/, '************') + '\n'
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
  stage = getStage();
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/' + stage + '/log?start_time=' + startTimestamp + '&end_time=' + endTimestamp);
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
  stage = getStage();
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/' + stage + '/stats?start_time=' + startTimestamp + '&end_time=' + endTimestamp);
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
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  stage = getStage();
    
  var confirm = window.confirm('Run ' + project + ' project stage:' + stage + ', target:' + target_id + '?');
  if (!confirm) {
    return;
  }

  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + repository + '/' + project + '/' + stage + '/run?target_id=' + target_id);
  xhr.onload = function(e) {
    res = JSON.parse(xhr.responseText);
    console.info(res);
    setTimeout(getStatus, 5000);      
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
  stage = getStage();
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/' + stage +'/schedules');
  xhr.onload = function(e) {
    res = JSON.parse(xhr.responseText);
    var htmlOut = '';
    res['schedules'].forEach(function(s) {
      var h = '<tr>';
      h = h + '<td>' + '<a class="btn btn-primary btn-sm d-none d-sm-inline-block" role="button" id="publish" href="#schedules"';
      if (s['status'] != 'scheduled') {
          h = h + 'onclick="updateSchedule(' + s['target_id'] + ')" ';
      }
      button_color = s['status'] != 'scheduled' ? 'green' : 'gray';
      button_label = s['status'] != 'scheduled' ? 'Schedule' : 'Scheduled';
      h = h + 'style="background: var(--' + button_color + ');">' + button_label + '</a>' + '</td>';
      h = h + '<td><a class="btn btn-primary btn-sm d-none d-sm-inline-block" role="button" id="run-now" href="#schedules" onclick="runNow(' +
          s['target_id'] +
          ');" style="background: #00599C;"><i class="fas fa-play fa-sm text-white-50"></i>&nbsp;Run Now</a> </td>';
      h = h + '<td>' + s['target_id'] + '</td><td>' + s['cron'] + '</td><td>';
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
    var output = document.getElementById('status');
    output.innerHTML = "";
    return;
  }
  project = getProjectID()
  if (project === null) return;
  stage = getStage();
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/' + stage +'/status');
  xhr.onload = function(e) {
    res = JSON.parse(xhr.responseText);
    var htmlOut = '';
    if (res === null) return;
    res.forEach(function(s) {
    var h = '<tr><td>' + s['taskArn'].slice(-8) + '</td><td>' +
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

async function loadFile(path){
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
    
  if (project === null) return;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/' + repository + '/' + project + '/files/' + path);
  xhr.onload = function(e) {
    text = xhr.responseText.replace(/^"|"$/g, '').replaceAll('\\n', '\n').replaceAll('\\"', '\"');
    editor.setValue(text);
  }
  xhr.send();
}

function fetchData() {
  startTimestamp = getStartTimestamp();
  endTimestamp = getEndTimestamp();
  fetchRepositoryList();
  fetchProjectList();
  fetchProjectFiles();
  project = getProjectID();
  if (project != null && editor.getValue() === '') {
      loadFile(project + '/' + 'project.yml');
  }
  getStatus();
  getSchedule();
  pollLog(startTimestamp, endTimestamp);
  pollStats(startTimestamp, endTimestamp);
}

function init() {
  sessionStorage.SessionName = 'handoff';
  token = sessionStorage.getItem("token");
  if (token != undefined) {
    postLogin(token);
    fetchData();  
  } else {
    showLoginModal();      
  }
}

$(document).ready(function(){
  init();
});