async function createGoal(event) {
    event.preventDefault();
    const form = document.getElementById("goal-form");
    const formData = new FormData(form);

    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value !== "" && value !== null && value !== undefined) {
            data[key] = value;
        }
    }

    try {
        const response = await fetch(window.apiCreateUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Server error:", errorData);

            let errorMessage = "Form submission error";
            if (Array.isArray(errorData.detail)) {
                errorMessage = errorData.detail.map((err) => `${err.loc?.join(".")}: ${err.msg}`).join("\n");
            } else if (errorData.detail) {
                errorMessage = errorData.detail;
            }

            alert(errorMessage);
            return;
        }

        window.location.href = window.successRedirectUrl;
    } catch (error) {
        console.error("Network error:", error);
        alert("Network error: " + error.message);
    }
}