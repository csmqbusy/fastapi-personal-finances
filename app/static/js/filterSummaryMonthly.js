document.getElementById("filter-form").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    let year = formData.get("year");
    if (!year) {
        year = new Date().getFullYear();
    }

    let month = formData.get("month");
    if (!month) {
        month = new Date().getMonth() + 1;
    } else {
        month = parseInt(month, 10);
        if (month < 1 || month > 12) {
            alert("The month number must be between 1 and 12.");
            return;
        }
    }
    // on or null
    const splitByCategory = formData.get("split_by_category");
    const url_summary = splitByCategory === "on" ? `${window.getSummaryPrefix}/${year}/${month}?split_by_category=true` : `${window.getSummaryPrefix}/${year}/${month}`;
    const url_chart = splitByCategory === "on" ? `${window.getSummaryPrefix}/chart/${year}/${month}?split_by_category=true` : `${window.getSummaryPrefix}/chart/${year}/${month}`;

    fetch(url_summary)
        .then((response) => response.json())
        .then((data) => {
            const tableBody = document.getElementById("summary-table-body");
            tableBody.innerHTML = "";

            if (splitByCategory) {
                data.forEach((daily_summary) => {
                    daily_summary.summary.forEach((summary_record) => {
                        const row = document.createElement("tr");
                        row.innerHTML = `
                                <td>${daily_summary.day_number}</td>
                                <td>${summary_record.category_name}</td>
                                <td>${summary_record.amount}</td>
                                <td>${daily_summary.total_amount}</td>
                            `;
                        tableBody.appendChild(row);
                    });
                });
            } else {
                data.forEach((summary_record) => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                                <td>${summary_record.day_number}</td>
                                <td>All categories</td>
                                <td>${summary_record.total_amount}</td>
                                <td>${summary_record.total_amount}</td>
                            `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch((error) => console.error("Error:", error));

    fetch(url_chart)
        .then((response) => response.arrayBuffer())
        .then((arrayBuffer) => {
            const base64String = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

            const imgElement = document.getElementById("summary-chart");
            imgElement.src = `data:image/png;base64,${base64String}`;
        })
        .catch((error) => console.error("Error:", error));
});