document.getElementById("filter-form").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value !== "" && value !== null && value !== undefined) {
            data[key] = value;
        }
    }
    const params = new URLSearchParams(data);

    fetch(`${window.transactionsGetUrl}?${params}`)
        .then((response) => response.json())
        .then((data) => {
            const tableBody = document.getElementById("transactions-table-body");
            tableBody.innerHTML = "";

            data.forEach((tx) => {
                const row = document.createElement("tr");
                row.className = "clickable-row";
                row.onclick = function () {
                    window.location.href = `${window.txGetDetailsUrlPrefix}${tx.id}`;
                };
                row.innerHTML = `
                            <th scope="row">${tx.id}</th>
                            <td>${tx.amount}</td>
                            <td>${tx.category_name}</td>
                            <td>${tx.date}</td>
                            <td>${tx.description}</td>
                        `;
                tableBody.appendChild(row);
            });
        })
        .catch((error) => console.error("Error:", error));
});