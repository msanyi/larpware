// Initialize arrays to hold nodeTypes and files
    var nodeTypes = [];
    var files = [];

    // Function to fetch and store node types from server
    function populateNodeTypes() {
        return $.get("/admin/admin/get_node_types", function(data, status){
            nodeTypes = data;
        });
    }

    // Function to fetch and store files from server
    function populateFiles() {
        return $.get("/admin/admin/get_files", function(data, status){
            files = data;
        });
    }

    $(document).ready(function() {
        // When node types and files data are both fetched, generate the form for nodes dynamically
        $.when(populateNodeTypes(), populateFiles()).done(function() {
            $("#network-length").change(function() {
                var length = $(this).val();
                var nodesDiv = $("#nodes");
                nodesDiv.empty();
                for (var i = 0; i < length; i++) {
                    var nodeDiv = $('<div>');
                    nodeDiv.append(`<h2>Node ${i + 1}</h2>
                        <label for="node-name-${i}">Name:</label>
                        <input type="text" id="node-name-${i}" name="nodes[${i}][name]" required><br>
                        <label for="node-type-${i}">Type:</label>`);

                    var select = $(`<select id="node-type-${i}" name="nodes[${i}][node_type_id]" required></select>`);
                    nodeTypes.forEach(function(nodeType) {
                        select.append(new Option(nodeType.name, nodeType.id));
                    });
                    nodeDiv.append(select);

                    var fileSelect = $(`<select id="node-file-${i}" name="nodes[${i}][file_ids][]" multiple></select>`);

                    files.forEach(function(file) {
                        fileSelect.append(new Option(file.name, file.id));
                    });
                    nodeDiv.append(fileSelect);

                    nodeDiv.append(`<br>
                        <label for="node-users-${i}">Max Users:</label>
                        <input type="number" id="node-users-${i}" name="nodes[${i}][max_users]" min="0" value="2" required><br>`);

                    nodesDiv.append(nodeDiv);
                }
            });
        });

        // Handle form submission
        $('#network-form').submit(function(e) {
            e.preventDefault();

            // Extract form data
            var formData = {
                name: $('#network-name').val(),
                organization_id: $('#organization-id').val(),
                length: $('#network-length').val(),
                nodes: []
            };

            // Extract nodes data
            for (var i = 0; i < formData.length; i++) {
                var node = {
                    name: $(`#node-name-${i}`).val(),
                    node_type_id: $(`#node-type-${i}`).val(),
                    max_users: $(`#node-users-${i}`).val(),
                    file_ids: $(`#node-file-${i}`).val()
                };
                formData.nodes.push(node);
            }

            // Send POST request to create network
            $.ajax({
                url: '/admin/admin/create_network',
                method: 'POST',
                data: JSON.stringify(formData),
                contentType: 'application/json',
                success: function(response) {
                    // Display a success message and clear the form
					$('#message').text("Network created successfully!");
					$('#message').css("color", "green");

					// Feature added: form clear
					$('#network-form')[0].reset();
					$('#nodes').empty();
                    console.log(response);
                },
                error: function(error) {
                    // Handle error
                    console.log(error);
                }
            });
        });
    });