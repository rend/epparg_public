function triggerFileInput() {
    document.getElementById('pdf-upload').click();
    document.getElementById('status-updates').innerHTML = '';
    document.getElementById('progress-bar').style.width= '0%';
    document.getElementById('results_area').style.display = 'none';
}


function filesSelected() {
    
    var fileInput = document.querySelector('input[type="file"]');
    var formData = new FormData();

    // Append each file to the form data
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('file', fileInput.files[i]);
    }

    showSpinner();

    fetch('/upload', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
      .then(data => {
          if(data.error) {
            //   alert('Error: ' + data.error);
          } else {
              // Output the text to your page, join texts if multiple
                // var textOutput = document.getElementById('textOutput');
                // if(textOutput) {
                //   textOutput.textContent = JSON.stringify(data.texts); 
                  //populateTable(data);
                  //hideSpinner();
                // }         
            }
      }).catch(error => {
          console.error('Error:', error);
        //   alert('An error occurred while uploading the files.');
      });
}

function showSpinner() {
    const button = document.getElementById('custom-button');
    button.innerHTML = '<div class="lds-ring"><div></div><div></div><div></div><div></div></div>'; // Replace with your spinner HTML or CSS
}

function hideSpinner() {
    const button = document.getElementById('custom-button');
    button.innerHTML = 'BROWSE FILES';
}

var socket = io.connect('http://127.0.0.1:5000');

socket.on('connect', function() {
    console.log('Connected to the server.');
});

socket.on('progress', function(data) {
    console.log('Progress: ' + data.progress);
    // Update progress bar or display progress
    updateProgressBar(data.progress);
    updateStatus(data.progressText);
});

socket.on('result', function(data) {
    populateTable(data);
});

function updateProgressBar(progress) {
    var progressBar = document.getElementById('progress-bar');
    progressBar.style.width = progress + '%';
    progressBar.innerText = progress + '%';
}

function updateStatus(message) {
    var statusUpdatesContainer = document.getElementById('status-updates');
    
    // Remove 'current' class from previous message
    var currentElements = statusUpdatesContainer.getElementsByClassName('current');
    if (currentElements.length > 0) {
        currentElements[0].classList.remove('current');
    }

    // Create new status message element
    var newStatusMessage = document.createElement('div');
    newStatusMessage.classList.add('status-message', 'current');
    newStatusMessage.textContent = message;
    
    // Add the new status message to the container
    statusUpdatesContainer.appendChild(newStatusMessage);
}

function createTableRow(standard, met, text) {
    let tr = document.createElement('tr');
    tr.className = met ? 'met-true' : 'met-false';

    let tdStandard = document.createElement('td');
    tdStandard.textContent = standard;

    let tdMet = document.createElement('td');
    tdMet.innerHTML = met ? "<img src='static/images/icons8-tick.svg' width='75'/>" : 'Not Met';

    let tdText = document.createElement('td');
    tdText.textContent = text || 'No evidence found';

    tr.appendChild(tdStandard);
    tr.appendChild(tdMet);
    tr.appendChild(tdText);

    return tr;
  }

  // A function to populate the table with the JSON data.
  function populateTable(data) {
    document.getElementById('results_area').style.display = 'flex'
    // let tableBody = document.getElementById('complianceTable').querySelector('tbody');
    // console.log(data);
    // data.forEach(item => {
    //   console.log(item);
    //   let tr = createTableRow(item.standard, item.met, item.relevant_text_from_offer);
    //   tableBody.appendChild(tr);
    // });

    document.getElementById('ecr_blurb').innerHTML = "";

    if (data.dutch){
        document.getElementById('epparg_report_title').textContent = "Uw Rapport"
        document.getElementById('epparg_standards_title').textContent = "EPPARG Normen"
        document.getElementById('epparg_standards_dutch').style.display = "block"
        document.getElementById('epparg_standards_english').style.display = "none"
    }
    else {
        document.getElementById('epparg_report_title').innerHTML = "<div class=\"report_link\"><div class=\"report_link_left\">Your Report</div><div class=\"report_link_right\"><a href=\"static/texts/EPPARG_Certificate.pdf\" download><button class=\"file-btn\">DOWNLOAD CERTIFICATE</button></a></div>"
        document.getElementById('epparg_standards_title').textContent = "EPPARG Standards"
        document.getElementById('epparg_standards_dutch').style.display = "none"
        document.getElementById('epparg_standards_english').style.display = "block"
    }

    console.log(data.texts)

    console.log(data.dutch)

    data.texts.forEach(item => {
        console.log(item)
        res = ""
        if(data.dutch){
            res += "<div class='ecr_result_line'><strong>Standaard " + item.standard_no + "</strong><br></div>"
            if (item.compliance == 'met'){
                res += "<div class='ecr_result_line'><strong>Voldaan: </strong>Voldaan<br>"
            }
            else {
                res += "<div class='ecr_result_line'><strong>Voldaan: </strong>Niet Voldaan<br>"
            }
            res += "<div class='ecr_result_line'><strong>Analyse: </strong><br/>" + item.analysis +"<br>"
            res += "<div class='ecr_result_line'><strong>Bewijs: </strong><br/>" 
        } else {
            res += "<div class='ecr_result_line'><strong>Standard " + item.standard_no + "</strong><br></div>"
            if (item.compliance == 'met'){
                res += "<div class='ecr_result_line'><strong>Met: </strong>Met<br>"
            }
            else {
                res += "<div class='ecr_result_line'><strong>Met: </strong>Not Met<br>"
            }
            res += "<div class='ecr_result_line'><strong>Analysis: </strong><br/>" + item.analysis +"<br>"
            res += "<div class='ecr_result_line'><strong>Evidence: </strong><br/>"
        }
         
        item.evidence.forEach((evidence, index) => {
            res += "<div class='ecr_result_line'><span style='font-style: italic;'>\"" + evidence + "\"</span> [<strong>" + item.source[index] + ", page " + item.page_no[index] + "</strong>]" +  "<br></div>"
        });
        res += "<div style='margin-top: 30px'></div>"
        document.getElementsByClassName('ecr_blurb')[0].innerHTML = document.getElementsByClassName('ecr_blurb')[0].innerHTML + res;
    })
    var element = document.getElementById("results_area");
    element.scrollIntoView({behavior: 'smooth'});
    hideSpinner();
  }