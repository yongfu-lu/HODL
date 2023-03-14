
// ** show user dropdown when input stock names
// Get the input field and dropdown content
var input = document.getElementById("myInput");
var dropdown = document.getElementById("myDropdown");

// Add event listener to the input field
input.addEventListener("input", function () {
    // Hide the dropdown if the input field is empty
    if (this.value === "") {
        dropdown.style.display = "none";
        var options = dropdown.getElementsByTagName("a");
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
        dropdown.style.display = "block";
    }
});

// Add event listener to the dropdown options
dropdown.addEventListener("click", function (event) {
    // If the clicked element is an anchor tag, fill it into the input field and hide the dropdown
    if (event.target.tagName.toLowerCase() === "a") {
        input.value = event.target.innerText;
        dropdown.style.display = "none";
    }
});


