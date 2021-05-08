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

function goToSection(h){
  var url = location.href;
  location.href = "#"+h;
  history.replaceState(null,null,url);
}

function request(url, method, params=[], data=[], headers=[], json=false) {
  // adopted from https://web.dev/promises/#promisifying-xmlhttprequest
  // Return a new promise.
  return new Promise(function(resolve, reject) {
    // Do the usual XHR stuff
    var req = new XMLHttpRequest();
    var urlParams = url;
    params.forEach(function(p, index) {
      if (index == 0) {
          urlParams += '?' + p[0] + '=' + p[1];
      } else {
          urlParams += '&' + p[0] + '=' + p[1];        
      }
    });
    req.open(method, urlParams);
    headers.forEach(function(h, index) {
      req.setRequestHeader(h[0], h[1]);
    });
    if (json) {
      req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    }

    req.onload = function() {
      // This is called even on 404 etc
      // so check the status
      if (req.status == 200) {
        // Resolve the promise with the response text
        resolve(req.response);
      }
      else {
        // Otherwise reject with the status text
        // which will hopefully be a meaningful error
        reject(Error(req.statusText));
      }
    };

    // Handle network errors
    req.onerror = function() {
      reject(Error("Network Error"));
    };

    var formData = null;
    if (json) {
      formData = data;  
    } else if (data.length > 0) {
      formData = new FormData();
      data.forEach(function(obj, index){
        formData.append(obj[0], obj[1]);
      });
    }
    // Make the request
    req.send(formData);
  });
}

function post(url, data=[], headers=[], json=false) {
  return request(url, 'POST', [], data, headers, json);
}

function get(url, params=[], headers=[]) {
  return request(url, 'GET', params, [], headers);
}

function put(url, data=[], headers=[]) {
  return request(url, 'PUT', [], data, headers);
}

function delete_(url, headers=[]) {
  return request(url, 'DELETE', [], [], headers);
}

/* get set
*/
var path = window.location.pathname.split('/')

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

function setOrganizationID(organizationID) {
  if (organizationID != getOrganizationID()){
    setRepositoryID(null);
  }
  document.getElementById('organization-id').textContent = organizationID;
  fetchRepositoryList();  
}
function getOrganizationID() {
  var organization = document.getElementById('organization-id').textContent;
  if (organization === '') organization = null;
  return organization;
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
}
function getProjectID() {
  var projectID = document.getElementById('project-id').textContent;
  if (projectID === '') projectID = null;
  return projectID
}
function goToProject(projectID) {
  setProjectID(projectID);
  window.location.href = '/p/' + getOrganizationID() + '/' + getRepositoryID() + '/' + getProjectID();
}

var projectFiles = null;
function getProjectFiles() {
    return projectFiles;
}
function setProjectFiles(files) {
    projectFiles = files;
}

/* login
*/
function login() {    
  var data = [
    ['username', $('#inputEmail').val()],
    ['password', $('#inputPassword').val()]
  ];
  post('/token', data).then(function(response) {
    response = JSON.parse(response);
    if (response['access_token'] != undefined) {
      token = response['access_token'];
      postLogin(token);
      sessionStorage.SessionName = 'handoff';
      sessionStorage.setItem("token", token);              
    }      
  });
}

function showLoginModal() {
  $("#login-modal").modal({
    backdrop: 'static',
    keyboard: false
  });
  $('#login-modal').modal('show');    
}

function postLogin(token) {
  var headers = [
      ['accept', 'application/json', false],
      ['Authorization', 'Bearer ' + token, false]
  ]
  get('/users/me/', [], headers).then(function(response) {
    response = JSON.parse(response);
    $('#profile-image')[0].src = response['profile_url']
    $('#login-modal').modal('hide');    
    document.getElementById('user-menu').innerHTML = 
      '<a class="dropdown-item" href="#"><i class="fas fa-user fa-sm fa-fw mr-2 text-gray-400"></i> Profile</a><a class="dropdown-item" href="#"><i class="fas fa-cogs fa-sm fa-fw mr-2 text-gray-400"></i> Settings</a><a class="dropdown-item" href="#"><i class="fas fa-list fa-sm fa-fw mr-2 text-gray-400"></i> Activity log</a><div class="dropdown-divider"></div><a class="dropdown-item" href="#" onclick="logout()"><i class="fas fa-sign-out-alt fa-sm fa-fw mr-2 text-gray-400"></i> Logout</a>';
      fetchData();
  }, function(error) {
        showLoginModal();    
  });
}

function logout() {
    sessionStorage.removeItem("token");
    document.getElementById('user-menu').innerHTML = '<a class="dropdown-item" id="login" href="#" onclick="showLoginModal()"><i class="fas fa-sign-in-alt fa-sm fa-fw mr-2 text-gray-400"></i> Login</a>';
    $('#profile-image')[0].src = 'https://gravatar.com/avatar/0';
    window.location = '/';
}

/* Fetch
*/
async function fetchRepositoryList() {
  get('/api/repositories').then(function(response) {
    var output = document.getElementById('repositories');
    records = JSON.parse(response);
    htmlOut = '';
    records.forEach(function(obj, index) {
       htmlOut += '<a class="dropdown-item" href="#" onclick="setRepositoryID(\'' + obj + '\')">' + obj + '</a>'
    });
    output.innerHTML = htmlOut;
  }, function(error) {
    console.error("Failed!", error);
  });
}

async function fetchProjectList() {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  get('/api/' + repository + '/projects').then(function(response) {
    var output = document.getElementById('projects');
    records = JSON.parse(response);
    htmlOut = '';
    records.forEach(function(obj, index) {
       htmlOut += '<a class="dropdown-item" href="#" onclick="goToProject(\'' + obj + '\')">' + obj + '</a>'
    });
    output.innerHTML = htmlOut;
  }, function(error) {
    console.error("Failed!", error);
  });
}

async function fetchProjectFiles() {
  var repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  var project = getProjectID();
  if (project === null) return [];
    
  get('/api/' + repository + '/' + project + '/files').then(function(response) {
    setProjectFiles(JSON.parse(response));
  }, function(error) {
    console.error("Failed!", error);
  });
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
  params = [
    ['start_time', startTimestamp],
    ['end_time', endTimestamp]
  ]
  get('/api/' + repository + '/' + project + '/' + stage + '/log', params).then(function(response) {
    updateLogArea(response);
  }, function(error) {
    console.error("Failed!", error);
  });
}

async function pollStats(startTimestamp, endTimestamp) {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  stage = getStage();
  if (project === null) return;
  params = [
    ['start_time', startTimestamp],
    ['end_time', endTimestamp]
  ]    
  get('/api/' + repository + '/' + project + '/' + stage + '/stats', params).then(function(response) {
    data = new Array();
    records = JSON.parse(response);
    records.forEach(function(obj, index) {
      if (obj['message'] && obj['message']['metric'] == 'record_count') {
        data.push([new Date(obj['datetime']).getTime() /* - 8 * 60 * 60 * 1000 */,
          obj['message']['value']]);
      }
    });
    console.info(data);
    chart.series[0].update({name: project, data: data}, true);
  }, function(error) {
    console.error("Failed!", error);
  });
}

async function runNow(target_id) {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  stage = getStage();
  if (project === null) return;   
  var confirm = window.confirm('Run ' + project + ' project stage:' + stage + ', target:' + target_id + '?');
  if (!confirm) {
    return;
  }    
  post('/api/' + repository + '/' + project + '/' + stage + '/schedules/' + target_id + '/run').then(function(response){
    res = JSON.parse(response);
    console.info(res);
    setTimeout(getStatus, 5000);      
  });
}

async function updateSchedule(targetId, cron){
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  stage = getStage();
  if (project === null) return; 
  var confirm = window.confirm('Schedule ' + project + ' project stage:' + stage + ', target:' + targetId + ' at ' + cron + '?');
  if (!confirm) {
    return;
  }
  post('/api/' + repository + '/' + project + '/' + stage + '/schedules/' + targetId).then(function(response) {
    res = JSON.parse(response);
    console.info(res);
    setTimeout(getSchedule, 1000);       
  });
}

async function deleteSchedule(targetId, cron){
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  stage = getStage();
  if (project === null) return;
  var confirm = window.confirm('Delete schedule ' + project + ' project stage:' + stage + ', target:' + targetId + ' at ' + cron + '?');
  if (!confirm) {
    return;
  }

  delete_('/api/' + repository + '/' + project + '/' + stage + '/schedules/' + targetId).then(function(response){
    res = JSON.parse(response);
    console.info(res);
    setTimeout(getSchedule, 1000);      
  });
}

async function getSchedule() {
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  if (project === null) return;
  stage = getStage();
    
  get('/api/' + repository + '/' + project + '/' + stage + '/schedules').then(function(response) {
    res = JSON.parse(response);
    var htmlOut = '';
    res['schedules'].forEach(function(s) {
      var h = '<tr>';
      h = h + '<td>' + '<a class="btn btn-primary btn-sm d-none d-sm-inline-block" role="button" id="publish" href="#schedules"';
      if (s['status'] == 'scheduled') {
        button_label = 'Scheduled';
        button_color = 'gray';
      } else if (s['cron'] === undefined || s['cron'] == '') {
        button_label = 'Adhoc';
        button_color = 'gray';
      } else {
        h = h + 'onclick="updateSchedule(\'' + s['target_id'] + '\', \'' + s['cron'] +'\')" ';
        button_label = 'Schedule';
        button_color = 'green';
      }
      h = h + 'style="background: var(--' + button_color + ');">' + button_label + '</a>';
      if (s['status'] == 'scheduled') {
        h = h + ' <a onclick="deleteSchedule(\'' + s['target_id'] + '\', \'' + s['cron'] +'\')" class="btn btn-primary btn-sm d-none d-sm-inline-block" role="button" id="run-now-1" href="#schedules" style="background: var(--red);"><i class="fas fa-trash-alt fa-sm text-white"></i></a>';
      }
      h = h + '</td>';
      h = h + '<td><a class="btn btn-primary btn-sm d-none d-sm-inline-block" role="button" id="run-now" href="#schedules" onclick="runNow(\'' +
          s['target_id'] +
          '\');" style="background: #00599C;"><i class="fas fa-play fa-sm text-white-50"></i>&nbsp;Run Now</a> </td>';
      h = h + '<td>' + s['target_id'] + '</td><td>' + s['cron'] + '</td><td>';
      s['envs'].forEach(function(e) {
        h = h + e['key'] + ": '" + e['value'] + "', ";
      });
      h = h + '</td></tr>';
      htmlOut += h;
    });
    var output = document.getElementById('schedule');
    output.innerHTML = htmlOut;        
  }, function(error) {
    console.error("Failed!", error);
  });    
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
    
  get('/api/' + repository + '/' + project + '/' + stage + '/status').then(function(response) {
    res = JSON.parse(response);
    var htmlOut = '';
    if (res === null || res['status'] == 'error') return;
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
    output.innerHTML= htmlOut;  }, function(error) {
    console.error("Failed!", error);
  });
}

async function saveFile() {
  var path = document.getElementById('filename').innerText;
  if (path === undefined || path == '') {
      return;
  }
  var repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  var project = getProjectID();
  if (project === null) return; 
    
  // document.getElementById('filename').innerText = path;
  var data = JSON.stringify({'body': editor.getValue()});
    
  post('/api/' + repository + '/' + project + '/files/' + path, data, [], true).then(function(response){
    console.log('saved file:' + path);
    setTimeout(fetchData, 1000);            
  });
}

async function loadFile(path){
  repository = getRepositoryID();
  if (repository === null) {
    return;
  }
  project = getProjectID();
  if (project === null) return;

  get('/api/' + repository + '/' + project + '/files/' + path).then(function(response) {
    text = response.replace(/^"|"$/g, '').replaceAll('\\n', '\n').replaceAll('\\"', '\"');
    editor.setValue(text);
    document.getElementById('filename').innerText = path;  
    goToSection('develop');
  }, function(error) {
    console.error("Failed!", error);
  });
}

function fetchData() {
  path = window.location.pathname.split('/');
  organization = path[2];
  if (organization != undefined) setOrganizationID(organization);
  repository = path[3];
  if (repository != undefined) setRepositoryID(repository);
  project = path[4];
  if (project != undefined) setProjectID(project);
  startTimestamp = getStartTimestamp();
  endTimestamp = getEndTimestamp();
  fetchRepositoryList();
  fetchProjectList();
  fetchProjectFiles();
  project = getProjectID();
  if (project != null && editor != undefined && editor.getValue() === '') {
      loadFile(project + '/' + 'project.yml');
  }
  if (fileManager != undefined){
      fileManager.refresh();
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
  } else {
    showLoginModal();      
  }
}

$(document).ready(function(){
  init();
});