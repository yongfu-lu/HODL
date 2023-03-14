// ** show user dropdown when input stock names for each algorithm
// ** algo 1:
// Get the input field and dropdown content
var input1 = document.getElementById("stockInput1");
var dropdown1 = document.getElementById("stockDropdown1");

// Add event listener to the input field
input1.addEventListener("input", function () {
    // Hide the dropdown if the input field is empty
    if (this.value === "") {
        dropdown1.style.display = "none";
        var options = dropdown1.getElementsByTagName("a");
        for (var i = 0; i < options.length; i++) {
            options[i].style.display = 'none'
        }
        return;
    }

    // Get the prefix typed by the user
    var prefix = this.value.toLowerCase();

    if (prefix.length >= 2) {
        // Get all the options in the dropdown
        var n = prefix.charCodeAt(0) - 96
        var selector = ".index" + n.toString() + " a"
        var options = document.querySelectorAll(selector)

        // Loop through the options and show only the ones that match the prefix
        for (var i = 0; i < options.length; i++) {
            if (options[i].innerText.toLowerCase().startsWith(prefix)) {
                options[i].style.display = "block";
            } else {
                options[i].style.display = "none";
            }
        }
        // Show the dropdown
        dropdown1.style.display = "block";
    }
});
// Add event listener to the dropdown options
dropdown1.addEventListener("click", function (event) {
    // If the clicked element is an anchor tag, fill it into the input field and hide the dropdown
    if (event.target.tagName.toLowerCase() === "a") {
        input1.value = event.target.innerText;
        dropdown1.style.display = "none";
    }
});

//** algo 2
var input2 = document.getElementById("stockInput2");
var dropdown2 = document.getElementById("stockDropdown2");

// Add event listener to the input field
input2.addEventListener("input", function () {
    // Hide the dropdown if the input field is empty
    if (this.value === "") {
        dropdown2.style.display = "none";
        var options = dropdown2.getElementsByTagName("a");
        for (var i = 0; i < options.length; i++) {
            options[i].style.display = 'none'
        }
        return;
    }

    // Get the prefix typed by the user
    var prefix = this.value.toLowerCase();

    if (prefix.length >= 2) {
        // Get all the options in the dropdown
        var n = prefix.charCodeAt(0) - 96
        var selector = ".index" + n.toString() + " a"
        var options = document.querySelectorAll(selector)

        // Loop through the options and show only the ones that match the prefix
        for (var i = 0; i < options.length; i++) {
            if (options[i].innerText.toLowerCase().startsWith(prefix)) {
                options[i].style.display = "block";
            } else {
                options[i].style.display = "none";
            }
        }
        // Show the dropdown
        dropdown2.style.display = "block";
    }
});

// Add event listener to the dropdown options
dropdown2.addEventListener("click", function (event) {
    // If the clicked element is an anchor tag, fill it into the input field and hide the dropdown
    if (event.target.tagName.toLowerCase() === "a") {
        input2.value = event.target.innerText;
        dropdown2.style.display = "none";
    }
});


//** algo 3
var input3 = document.getElementById("stockInput3");
var dropdown3 = document.getElementById("stockDropdown3");

// Add event listener to the input field
input3.addEventListener("input", function () {
    // Hide the dropdown if the input field is empty
    if (this.value === "") {
        dropdown3.style.display = "none";
        var options = dropdown3.getElementsByTagName("a");
        for (var i = 0; i < options.length; i++) {
            options[i].style.display = 'none'
        }
        return;
    }

    // Get the prefix typed by the user
    var prefix = this.value.toLowerCase();

    if (prefix.length >= 2) {
        // Get all the options in the dropdown
        var n = prefix.charCodeAt(0) - 96
        var selector = ".index" + n.toString() + " a"
        var options = document.querySelectorAll(selector)

        // Loop through the options and show only the ones that match the prefix
        for (var i = 0; i < options.length; i++) {
            if (options[i].innerText.toLowerCase().startsWith(prefix)) {
                options[i].style.display = "block";
            } else {
                options[i].style.display = "none";
            }
        }
        // Show the dropdown
        dropdown3.style.display = "block";
    }
});

// Add event listener to the dropdown options
dropdown3.addEventListener("click", function (event) {
    // If the clicked element is an anchor tag, fill it into the input field and hide the dropdown
    if (event.target.tagName.toLowerCase() === "a") {
        input3.value = event.target.innerText;
        dropdown3.style.display = "none";
    }
});

//** algo 4
var input4 = document.getElementById("stockInput4");
var dropdown4 = document.getElementById("stockDropdown4");

// Add event listener to the input field
input4.addEventListener("input", function () {
    // Hide the dropdown if the input field is empty
    if (this.value === "") {
        dropdown4.style.display = "none";
        var options = dropdown4.getElementsByTagName("a");
        for (var i = 0; i < options.length; i++) {
            options[i].style.display = 'none'
        }
        return;
    }

    // Get the prefix typed by the user
    var prefix = this.value.toLowerCase();

    if (prefix.length >= 2) {
        // Get all the options in the dropdown
        var n = prefix.charCodeAt(0) - 96
        var selector = ".index" + n.toString() + " a"
        var options = document.querySelectorAll(selector)

        // Loop through the options and show only the ones that match the prefix
        for (var i = 0; i < options.length; i++) {
            if (options[i].innerText.toLowerCase().startsWith(prefix)) {
                options[i].style.display = "block";
            } else {
                options[i].style.display = "none";
            }
        }
        // Show the dropdown
        dropdown4.style.display = "block";
    }
});

// Add event listener to the dropdown options
dropdown4.addEventListener("click", function (event) {
    // If the clicked element is an anchor tag, fill it into the input field and hide the dropdown
    if (event.target.tagName.toLowerCase() === "a") {
        input4.value = event.target.innerText;
        dropdown4.style.display = "none";
    }
});


//** algo 5
var input5 = document.getElementById("stockInput5");
var dropdown5 = document.getElementById("stockDropdown5");

// Add event listener to the input field
input5.addEventListener("input", function () {
    // Hide the dropdown if the input field is empty
    if (this.value === "") {
        dropdown5.style.display = "none";
        var options = dropdown5.getElementsByTagName("a");
        for (var i = 0; i < options.length; i++) {
            options[i].style.display = 'none'
        }
        return;
    }

    // Get the prefix typed by the user
    var prefix = this.value.toLowerCase();

    if (prefix.length >= 2) {
        // Get all the options in the dropdown
        var n = prefix.charCodeAt(0) - 96
        var selector = ".index" + n.toString() + " a"
        var options = document.querySelectorAll(selector)

        // Loop through the options and show only the ones that match the prefix
        for (var i = 0; i < options.length; i++) {
            if (options[i].innerText.toLowerCase().startsWith(prefix)) {
                options[i].style.display = "block";
            } else {
                options[i].style.display = "none";
            }
        }
        // Show the dropdown
        dropdown5.style.display = "block";
    }
});

// Add event listener to the dropdown options
dropdown4.addEventListener("click", function (event) {
    // If the clicked element is an anchor tag, fill it into the input field and hide the dropdown
    if (event.target.tagName.toLowerCase() === "a") {
        input5.value = event.target.innerText;
        dropdown5.style.display = "none";
    }
});
