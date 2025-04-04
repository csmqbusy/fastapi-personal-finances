document.getElementById("filter-form").addEventListener("submit", function (event) {
    event.preventDefault();

    const formData = new FormData(this);

    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value !== "" && value !== null && value !== undefined) {
            data[key] = value;
        }
    }
    const params = new URLSearchParams(data).toString();

    fetch(`${window.goalsGetUrl}?${params}`)
        .then((response) => response.json())
        .then((data) => {
            const tableBody = document.getElementById("goals-table-body");
            tableBody.innerHTML = "";

            data.forEach((goal) => {
                const row = document.createElement("tr");
                row.className = "clickable-row";
                row.onclick = function () {
                    window.location.href = `${window.goalGetDetailsUrlPrefix}${goal.id}`;
                };
                row.innerHTML = `
                            <th scope="row">${goal.id}</th>
                            <td>${goal.name}</td>
                            <td>${goal.description}</td>
                            <td>${goal.current_amount}</td>
                            <td>${goal.target_amount}</td>
                            <td>${goal.start_date}</td>
                            <td>${goal.target_date}</td>
                            <td>${goal.end_date}</td>
                            <td>${goal.status}</td>
                        `;
                tableBody.appendChild(row);
            });
        })
        .catch((error) => console.error("Error:", error));
});
