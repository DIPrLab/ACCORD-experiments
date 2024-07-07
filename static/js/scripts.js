$(document).ready(function(){
    // Set max date for date field to today's date
    var today = new Date().toISOString().split('T')[0];
    $('#date-field').attr('max', today);

    // Function to handle fetch button click
    $('#fetch-button').on('click', async function() {
        // Show loader
        $('#loader').show();
        // Hide table, fetch message, and pagination
        $('#log-table').hide();
        $('#fetch-message').hide();
        $('#pagination').hide();
        // Disable detect conflicts button
        $('#detect-conflicts-button').prop('disabled', true);

        // Get selected date value from date field
        var selectedDate = $('#date-field').val();
        
        // Convert selected date to ISO string format
        var isoDate = new Date(selectedDate).toISOString();

        // Fetch drive log with selected date as parameter
        try {
            let logResponse = await fetch('/fetch_drive_log?time=' + isoDate);
            let logData = await logResponse.json();
            console.log('Log Data:', logData);

            // Clear existing table rows
            $('#log-table-body').empty();

            // Populate table with log data if available
            if (logData.length > 0) {
                $('#log-table').show();
                $('#fetch-message').show().text(`Fetched ${logData.length} rows from ${selectedDate}`);
                
                // Calculate pagination
                var pageSize = 20;
                var pageCount = Math.ceil(logData.length / pageSize);
                var currentPage = 1;

                // Display initial page
                displayLogData(logData, currentPage, pageSize);

                // Generate pagination links
                var paginationHtml = '';
                for (var i = 1; i <= pageCount; i++) {
                    paginationHtml += `<li class="page-item ${i === currentPage ? 'active' : ''}"><a class="page-link" href="#">${i}</a></li>`;
                }
                $('#pagination-list').html(paginationHtml);
                $('#pagination').show();

                // Enable detect conflicts button
                $('#detect-conflicts-button').prop('disabled', false);

                // Handle pagination click
                $('#pagination-list').on('click', '.page-link', function(e) {
                    e.preventDefault();
                    currentPage = parseInt($(this).text());
                    displayLogData(logData, currentPage, pageSize);
                    // Update active state
                    $('#pagination-list .page-item').removeClass('active');
                    $(this).parent().addClass('active');
                });

            } else {
                // Display message if no rows fetched
                $('#fetch-message').show().text(`No data found for ${selectedDate}`);
            }

        } catch (error) {
            console.error('Error fetching log:', error);
            // Handle error gracefully
            $('#fetch-message').show().text('Error fetching data. Please try again.');
        } finally {
            // Hide loader after fetch completes
            $('#loader').hide();

            // Send HTTP POST request to /refresh_logs
            fetch('/refresh_logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
                // Optionally, you can also send data in the request body if needed
                // body: JSON.stringify({key: 'value'})
            }).then(response => {
                // You can handle the response here if needed
                console.log(response);
            }).catch(error => {
                // Handling errors
                console.error('Error:', error);
            });        
            
        }
    });

    // Detect conflicts button click handler
    $('#detect-conflicts-button').on('click', function() {
        
        // Get selected date value from date field
        var selectedDate = $('#date-field').val();
        // Convert selected date to ISO string format
        var isoDate = new Date(selectedDate).toISOString();

        // Clear the table
        $("#logs-table tbody").empty();

        // Show loader
        $('#loader').show();

        // Call detect conflicts function with ISO date
        callDetectConflictsDemo(isoDate);
    });

    // Function to detect conflicts
    function callDetectConflictsDemo(currentDate) {
        // Send HTTP POST request to detect conflicts endpoint
        fetch('/detect_conflicts_demo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `current_date=${currentDate}`, // Sending current_date as a form parameter
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json(); // Expecting JSON response
        })
        .then(data => {
            // Hide loader after fetch completes
            $('#loader').hide();

            // Display detection time label
            $('#detectionTimeLabel').text(`Detection Time: ${data.detectTimeLabel}`);

            // Check if logs are available
            if (data.logs.length > 0) {
                // Update the table with the returned logs
                data.logs.forEach(function(log, index) {
                    const row = $("<tr>");
                    row.append($("<td>").text(data.conflictID[index])); // Add conflict ID
                    for (let i = 0; i < 4; i++) {
                        row.append($("<td>").text(log[i])); // Append first four columns from log data
                    }
                    $("#logs-table tbody").append(row); // Append the row to the table body
                });

                // Show the modal with logs
                $('#logsModal').modal('show');
            } else {
                // Display message if no logs found
                $('#no-logs-message').show();
            }
        })
        .catch(error => {
            console.error('Error detecting conflicts:', error);
            // Handle error gracefully
            alert('Error detecting conflicts. Please try again.');
            $('#loader').hide(); // Hide loader on error
        });
    }


    $('.nav-tabs a').on('click', function (e) {
        e.preventDefault();
        $(this).tab('show');
    });
});

// Function to display log data based on pagination
function displayLogData(logData, page, pageSize) {
    var startIndex = (page - 1) * pageSize;
    var endIndex = startIndex + pageSize;
    var displayedData = logData.slice(startIndex, endIndex);

    // Clear table rows
    $('#log-table-body').empty();

    // Populate table rows
    displayedData.forEach((logEntry, index) => {
        $('#log-table-body').append(`
            <tr>
                <td>${startIndex + index + 1}</td>
                <td>${logEntry.time}</td>
                <td>${logEntry.activity}</td>
                <td>${logEntry.resource}</td>
                <td>${logEntry.actor}</td>
            </tr>
        `);
    });
}

// Action Constraints
document.getElementById('showConstraints').addEventListener('click', async function() {
    const constraintsTable = document.getElementById('constraintsTable').getElementsByTagName('tbody')[0];
    const statusMessage = document.getElementById('statusMessage');
    const dateValue = document.getElementById('cdate-field').valueAsDate;  // Get selected date value

    // Convert selected date to ISO string format
    const isoDate = dateValue.toISOString();

    statusMessage.textContent = 'Fetching constraints...';
    constraintsTable.innerHTML = '';  // Clear the table

    try {
        const response = await fetch('/fetch_actionConstraints', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ date: isoDate })  // Pass ISO string date in the request body
        });

        const constraints = await response.json();

        // Check if constraints array is empty
        if (constraints.length > 0) {
            constraints.forEach((constraint, index) => {
                setTimeout(() => {
                    const row = constraintsTable.insertRow();
                    const cell1 = row.insertCell(0);
                    const cell2 = row.insertCell(1);
                    const cell3 = row.insertCell(2);
                    const cell4 = row.insertCell(3);
                    const cell5 = row.insertCell(4);
                    const cell6 = row.insertCell(5);

                    cell1.innerHTML = index + 1;
                    cell2.innerHTML = constraint.TimeStamp;
                    cell3.innerHTML = constraint.ConstraintTarget;
                    cell4.innerHTML = constraint.Constraint;
                    cell5.innerHTML = constraint.ConstraintOwner;
                    cell6.innerHTML = constraint.File;
                }, 10 * index);
            });

            statusMessage.textContent = `Fetched ${constraints.length} Action Constraints`;
        } else {
            statusMessage.textContent = 'No Action Constraints found';
        }
    } catch (error) {
        console.error('Error fetching constraints:', error);
        statusMessage.textContent = 'Failed to fetch Action Constraints';
    }
});
