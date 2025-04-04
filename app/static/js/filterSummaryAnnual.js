document.getElementById("filter-form").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    let year = formData.get("year");
    if (!year) {
        year = new Date().getFullYear();
    }
    // on or null
    const splitByCategory = formData.get("split_by_category");
    const url_summary = splitByCategory === "on" ? `${window.getSummaryPrefix}/${year}?split_by_category=true` : `${window.getSummaryPrefix}/${year}`;
    const url_chart = splitByCategory === "on" ? `${window.getSummaryPrefix}/chart/${year}?split_by_category=true` : `${window.getSummaryPrefix}/chart/${year}`;

    fetch(url_summary)
        .then((response) => response.json())
        .then((data) => {
            const tableBody = document.getElementById("summary-table-body");
            tableBody.innerHTML = "";

            if (splitByCategory) {
                data.forEach((monthly_summary) => {
                    monthly_summary.summary.forEach((summary_record) => {
                        const row = document.createElement("tr");
                        row.innerHTML = `
                                <td>${monthly_summary.month_number}</td>
                                <td>${summary_record.category_name}</td>
                                <td>${summary_record.amount}</td>
                                <td>${monthly_summary.total_amount}</td>
                            `;
                        tableBody.appendChild(row);
                    });
                });
            } else {
                data.forEach((summary_record) => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                                <td>${summary_record.month_number}</td>
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
