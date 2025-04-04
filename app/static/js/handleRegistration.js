async function handleRegistration(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        username: formData.get("username"),
        email: formData.get("email"),
        password: formData.get("password"),
    };

    const response = await fetch(window.signUpUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    if (response.ok) {
        window.location.href = "/pages/";
    } else {
        const errorData = await response.json();
        const errorMessage = errorData.detail || "An error occurred";
        alert(errorMessage);
    }
}
