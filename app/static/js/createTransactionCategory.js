async function txCategoryCreate(event) {
    event.preventDefault();
    const form = document.getElementById("transaction-category-form");
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

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
