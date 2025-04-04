async function deleteTxCategory(event, category_name) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);

    const params = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
        if (value !== "" && value !== null && value !== undefined) {
            params.append(key, value);
        }
    }

    try {
        let url = window.apiDeleteTxCategoryUrl + encodeURIComponent(category_name);

        const queryString = params.toString();
        if (queryString) {
            url += "?" + queryString;
        }
        const response = await fetch(url, {
            method: "DELETE",
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

        window.location.reload();
    } catch (error) {
        console.error("Network error:", error);
        alert("Network error: " + error.message);
    }
}
