async function handleLogin(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const response = await fetch(window.loginUrl, {
        method: "POST",
        body: new URLSearchParams(formData),
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
    });

    const result = await response.json();

    if (result.sign_in === "Success!") {
        window.location.href = "/pages/";
    } else {
        alert("Invalid username or password.");
    }
}
