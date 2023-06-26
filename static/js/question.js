
// Check if a radio button is selected and show and hide the warning appropriately
function radio_is_checked() {
    for (i = 1; i <= num_question_choices; i++) {
        let radioButton = $('#Q' + i);
        if (radioButton.is(':checked')) {
            $("#radio_selection_warning").hide()
            return true;
        }
    }
    $("#radio_selection_warning").show()
    return false
}


// Checks if the user answered correctly and visually displays the correct answer
function check_answer() {
    user_choice = '';
    for (i = 1; i <= num_question_choices; i++) {
        let radioButton = $('#Q' + i);
        if (radioButton.is(':checked')) {
            user_choice = radioButton.val();
            break;
        }
    }

    // Perform an AJAX request to check the answer for the current question number
    // The answers for other questions is not shown until the user submits their selection on that question
    var url = "/record_choice_get_answer";
    data = { worker_id: worker_id, user_choice: user_choice };
    $.ajax({
        url: url,
        type: 'POST',
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify(data, null, '\t'),
        success: function (data) {

            // data = {
            //     'answerNum': ...,
            //     'answerText': '...'
            // }

            correct_answer = data.answerNum;
            console.log("Correct choice is:", correct_answer, ", user chose:", user_choice);

            // HTML Colors for correct and wrong answers
            let correct_color = "#6C9A33"
            let wrong_color = "#672770"

            // Change the color of the choices to suggest (in)/correctness

            let correctAnswerLabel = $('#Q_label_' + correct_answer);

            if (user_choice == correct_answer) {
                console.log("Correct Answer!");
                correctAnswerLabel.after("<p id='feedback_id_correct' style='display:inline;margin-left:12px';><strong>Correct</strong></p>");
                $('#feedback_id_correct').css("color", correct_color);
            }
            else {
                console.log("Wrong Answer!");
                let userChoiceLabel = $('#Q_label_' + user_choice);
                userChoiceLabel.css("color", wrong_color);
                userChoiceLabel.after("<p id='feedback_id_wrong' style='display:inline;margin-left:12px';><strong>Wrong</strong></p>");
                $('#feedback_id_wrong').css("color", wrong_color);
            }
            correctAnswerLabel.css("color", correct_color);

            // Disable all the radio buttons
            $('input[type=radio').attr('disabled', true);

            // Change the text on the button
            $('#submit_answer').prop('value', 'Next');
        },
        error: function (xhr, testStatus, errorThrown) {
            console.log("AJAX to get_question_answer() route failed!");
        }
    });
}

// Loads the next question in the list and updates the image, schema and SQL 
function load_next_question() {
    worker_id = localStorage.getItem('worker_id');
    data = { worker_id: worker_id };
    let url = "/get_next_question";
    $.ajax({
        url: url,
        type: 'POST',
        data: JSON.stringify(data, null, '\t'),
        contentType: 'application/json;charset=UTF-8',
        success: function (data) {
            console.log("XXXX ", data)
            // data = {
            //     'image': '...',
            //     'answerStrings': ['...', '...', ...]
            let filename = 'img/question/' + data.image;
            $('.question_div_mid img').attr("src", static_folder + filename);

            for (i = 0; i < num_question_choices; i++) {
                let text_val = data.answerStrings[i];
                let html_val = text_val.replace(/\*\*(\**[\s\S]*?\**)\*\*/g, "<b>$1</b>");// make it bold

                $('#Q_label_' + (i + 1)).html(html_val);
            }

        },
        error: function (xhr, testStatus, errorThrown) {
            console.log("AJAX failed");
        }
    });


    // Enable all radio buttons
    $('input[type=radio').attr('disabled', false);

    // Change the color of all choices to black
    for (i = 0; i < 4; i++) {
        $('#Q_label_' + (i + 1)).css("color", "black");
    }

    $('#feedback_id_correct').remove();
    $('#feedback_id_wrong').remove();

    // Change the text on the button
    $('#submit_answer').prop('value', 'Submit');
}