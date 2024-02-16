// Initialize arrays to hold network, nodeTypes and files
var networks = [];
var nodeTypes = [];
var files = [];

// Function to fetch and store networks from server
function populateNetworks() {
    return $.get("/admin/admin/get_networks").done(function(data, status){
        networks = data;
    }).catch(function(err){
        console.log("Error fetching networks", err);
    });
}

// Function to fetch and store node types from server
function populateNodeTypes() {
    return $.get("/admin/admin/get_node_types").done(function(data, status){
        nodeTypes = data;
    }).catch(function(err){
        console.log("Error fetching node types", err);
    });
}

// Function to fetch and store files from server
function populateFiles() {
    return $.get("/admin/admin/get_files").done(function(data, status){
        files = data;
    }).catch(function(err){
        console.log("Error fetching files", err);
    });
}


// Function to generate a new node div
function createNodeDiv(i, node = {}) {
    var nodeDiv = $('<div>');
    nodeDiv.append(`<h2>Node ${i + 1}</h2>
        <label for="node-name-${i}">Name:</label>
        <input type="text" id="node-name-${i}" name="nodes[${i}][name]" value="${node.name || ''}" required><br>
        <label for="node-type-${i}">Type:</label>`);

    var select = $(`<select id="node-type-${i}" name="nodes[${i}][node_type_id]" required></select>`);
    nodeTypes.forEach(function(nodeType) {
        var option = new Option(nodeType.name, nodeType.id);
        if(node.node_type_id && nodeType.id == node.node_type_id) option.selected = true;
        select.append(option);
    });
    nodeDiv.append(select);

    nodeDiv.append(`<label for="node-file-${i}">Files:</label>`);
    var fileSelect = $(`<select id="node-file-${i}" name="nodes[${i}][file_ids][]" multiple></select>`);

    files.forEach(function(file) {
        var option = new Option(file.name, file.id);
        if(node.file_ids && node.file_ids.includes(file.id)) option.selected = true;
        fileSelect.append(option);
    });
    nodeDiv.append(fileSelect);

    nodeDiv.append(`<br>
        <label for="node-users-${i}">Max Users:</label>
        <input type="number" id="node-users-${i}" name="nodes[${i}][max_users]" value="${node.max_users || 0}" min="0" required><br>`);

    return nodeDiv;
}


// Add event listener for network-length field
$('#network-length').change(function() {
    var length = $(this).val();
    var nodesDiv = $("#node-form-container");
    var nodeDivCount = nodesDiv.children('div').length;
    if(length < nodeDivCount) {
        nodesDiv.children('div').slice(length).remove();
    } else if(length > nodeDivCount) {
        for(var i = nodeDivCount; i < length; i++) {
            nodesDiv.append(createNodeDiv(i));
        }
    }
});

// Function to generate node form based on network length
function generateNodeForm(network) {
    var length = network.nodes.length;
    // Set values for network name, organization id and network length
    $("#network-name").val(network.name);
    $("#organization-id").val(network.organization_id);
    $("#network-length").val(length); // Populate node length field

    // Clear existing node form
    $("#node-form-container").html('');

    // Create form fields for each node
    for (var i = 0; i < length; i++) {
        var node = network.nodes[i];
        var nodeName = node.name;
        var nodeType = node.node_type_id;
        var nodeUsers = node.max_users;
        var nodeFileIds = node.file_ids || [];

        // Create node form fields
        var nodeForm = createNodeDiv(i);

        // Fill the form fields
        $(`#node-name-${i}`, nodeForm).val(nodeName);
        $(`#node-type-${i}`, nodeForm).val(nodeType);
        $(`#node-users-${i}`, nodeForm).val(nodeUsers);
        $(`#node-file-${i}`, nodeForm).val(nodeFileIds);


        // Append the node form to the node form container
        $("#node-form-container").append(nodeForm);
    }
}


$(document).ready(function() {
    // When network, node types and files data are all fetched, populate the network selector
    $.when(populateNetworks(), populateNodeTypes(), populateFiles()).then(function() {
        var networkSelect = $("#network-select");
        networks.forEach(function(network) {
            networkSelect.append(new Option(network.name, network.id));
        });

        // Trigger change event for the networkSelect after appending options
        networkSelect.trigger("change");

        // When a network is selected, generate the form for modifying nodes
        networkSelect.change(function() {
            var selectedNetwork = networks.find(network => network.id === parseInt(this.value));
            generateNodeForm(selectedNetwork);
        });
    }).catch(function(err) {
        console.log("Error when fetching initial data", err);
    });

    // Handle form submission
    $('#network-form').submit(function(e) {
        e.preventDefault();

        var networkId = $("#network-select").val(); // get the selected network ID
        var networkName = $("#network-name").val();
        var organizationId = $("#organization-id").val();
        var nodeLength = $("#network-length").val();
        var nodes = [];

        // Create or update nodes
        for (var i = 0; i < nodeLength; i++) {
            var nodeName = $(`#node-name-${i}`).val();
            var nodeType = $(`#node-type-${i}`).val();
            var nodeUsers = $(`#node-users-${i}`).val();

            // Get selected file IDs
            var nodeFileIds = $(`#node-file-${i}`).val() || [];

            var node = {
                name: nodeName,
                node_type_id: nodeType,
                max_users: nodeUsers,
                file_ids: nodeFileIds,
                order: i // assuming order is the same as the index
            };

            nodes.push(node);
        }

        var formData = {
            id: networkId,
            name: networkName,
            organization_id: organizationId,
            nodes: nodes
        };

        // Send POST request to update network
        $.ajax({
            url: '/admin/admin/update_network',
            method: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json'
        }).done(function(response) {
            // Handle successful response
            console.log(response);

            // Display a success message and clear the form
            $('#message').text("Network modified successfully!");
            $('#message').css("color", "green");

            // Feature added: form clear
            $('#network-form')[0].reset();
            $('#node-form-container').empty();
            populateNetworks().done(function() {
                var networkSelect = $("#network-select");
                networkSelect.empty();
                networks.forEach(function(network) {
                    networkSelect.append(new Option(network.name, network.id));
                });
                // Trigger change event for the networkSelect after appending options
                networkSelect.trigger("change");
            });
        }).catch(function(err) {
            // Handle error
            console.log(err);
        });
    });
});

