document.getElementById("filter-form").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value !== "" && value !== null && value !== undefined) {
            data[key] = value;
        }
    }
    const params = new URLSearchParams(data).toString();

    fetch(`${window.getSummaryUrl}?${params}`)
        .then((response) => response.json())
        .then((data) => {
            const tableBody = document.getElementById("summary-table-body");
            tableBody.innerHTML = "";

            data.forEach((summary_record) => {
                const row = document.createElement("tr");
                row.innerHTML = `
                            <td>${summary_record.category_name}</td>
                            <td>${summary_record.amount}</td>
                        `;
                tableBody.appendChild(row);
            });
        })
        .catch((error) => console.error("Error:", error));

    fetch(`${window.getSummaryChartUrl}?${params}`)
        .then((response) => response.arrayBuffer())
        .then((arrayBuffer) => {
            const base64String = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

            const imgElement = document.getElementById("summary-chart");
            imgElement.src = `data:image/jpeg;base64,${base64String}`;
        })
        .catch((error) => console.error("Error:", error));
});