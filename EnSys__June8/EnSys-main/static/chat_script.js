$(document).ready(function() {
    // Function to enable or disable input elements
    function toggleInputElements(disabled) {
        $('input[name=message]').prop('disabled', disabled);
        $('.send-button').prop('disabled', disabled);
    }

    // Function to adjust input height based on content
    function adjustInputHeight() {
        var input = $('input[name=message]')[0];
        input.style.height = 'auto'; // Reset height to auto
        input.style.height = (Math.min(input.scrollHeight, 100)) + 'px'; // Set height up to 100px
    }

    // Function to send message when Enter key is pressed
    $('.chat-input').keypress(function(event) {
        if (event.which === 13) { // 13 is the ASCII code for Enter key
            sendMessage();
        }
    });

    // Function to send the user message to the server
    function sendMessage() {
        var userMessage = $('input[name=message]').val().trim();

        if (userMessage === '') {
            return;
        }

        // Disable input elements while processing
        toggleInputElements(true);

        // Add the user message to the messages container
        $('.chat-messages').append('<div class="message-container"><div class="user-message">' + userMessage + '</div></div>');

        // Clear the input box
        $('input[name=message]').val('');

        // Reset the input's height
        adjustInputHeight();

        // Scroll to the bottom of the container when a new message is added
        $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);

        // Send the user message and sentiment to the server
        var sentiment = $('input[name=sentiment]').val(); // Get the sentiment value
        $.post("/chat", {
            prompt: userMessage,
            sentiment: sentiment // Pass sentiment to the server
        }, function(response) {
            // Display the bot's response with profile and image
            $('.chat-messages').append('<div class="message-container"><div class="chatbot-profile"><img src="static/logo.png" alt="EnSys Profile Image"></div><div class="message">' + formatMenu(response) + '</div></div>');

            // Scroll to the bottom of the container after adding the response
            $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);

            // Re-enable input elements after processing
            toggleInputElements(false);
        }).fail(function() {
            // Handle AJAX request failure (e.g., server not responding)
            $('.chat-messages').append('<div class="message-container"><div class="message">Something went wrong</div></div>');
            $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);

            // Re-enable input elements after processing
            toggleInputElements(false);
        });
    }

    // Function to format the menu response
    function formatMenu(response) {
        var formattedResponse = '';
        var lines = response.split('\n');
        lines.forEach(function(line) {
            if (line.includes(':')) {
                formattedResponse += '<strong>' + line + '</strong><br>';
            } else {
                formattedResponse += line + '<br>';
            }
        });
        return formattedResponse;
    }

    // When the send button is clicked, send the message to the server
    $('.send-button').click(function() {
        sendMessage();
    });

    // Adjust input height initially
    adjustInputHeight();
});

// Automatically request menu when user types 'menu'
$('input[name=message]').on('input', function() {
    var userInput = $(this).val().trim().toLowerCase();
    if (userInput === 'menu') {
        $.post("/chat", {
            prompt: 'MENU'
        }, function(response) {
            // Display the menu response with each item listed separately
            var formattedMenu = formatMenu(response);
            $('.chat-messages').append('<div class="message-container"><div class="message">' + formattedMenu + '</div></div>');

            // Scroll to the bottom of the container after adding the menu
            $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);
        });
        // Clear the input box after sending the menu request
        $('input[name=message]').val('');
    }
});

// Function to end chat and redirect to rating page
function endChat() {
        $.post("/chat", {
            prompt: 'END CHAT'
        }, function(response) {
            if (response === 'END CHAT') {
                window.location.href = '/rate';
            }
        });
    }
