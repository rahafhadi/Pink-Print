function showForm(formId) {
document.querySelectorAll(".form-box").forEach(form => form.classList.remove("active")); 
document.getElementById(formId).classList.add("active");
}

document.addEventListener("DOMContentLoaded", () => {

    const registerForm = document.querySelector(
        "#register-form form"
    );

    const message = document.getElementById(
        "register-message"
    );

    registerForm.addEventListener("submit", async (event) => {

        event.preventDefault();
        
        message.textContent = "Creating account...";

        try {
            const response = await fetch("/register", {
                method: "POST",
                body: new FormData(registerForm)
            });

            const result = await response.json();

            message.textContent = result.message;

            if (result.success) {
                registerForm.reset();
            }

        } catch (error) {
            message.textContent =
                "Connection error. Please try again.";
        }
    });

});

// Login form
document.addEventListener("DOMContentLoaded", () => {

    const loginForm = document.querySelector(
        "#login-form form"
    );

    const message = document.getElementById(
        "login-message"
    );

    loginForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        message.textContent = "Logging in...";

        try {
            const response = await fetch("/login", {
                method: "POST",
                body: new FormData(loginForm)
            });

            const result = await response.json();

        if (result.success) {
            message.textContent = result.message;

            window.location.href = "/main";
        } else {
            message.textContent = result.message;
        }
        
        } catch (error) {
            message.textContent =
                "Connection error. Please try again.";
        }
    });

});