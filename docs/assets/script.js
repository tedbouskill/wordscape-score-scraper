function populateTable(tableId, data) {
    const table = document.getElementById(tableId);
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    // Clear existing table content
    thead.innerHTML = '';
    tbody.innerHTML = '';

    // Add header row
    const headers = Object.keys(data[0]);
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        th.addEventListener('click', () => {
            sortTableByColumn(table, headers.indexOf(header));
        });
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    // Add data rows
    data.forEach(row => {
        const tr = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            td.textContent = row[header];
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

function sortTableByColumn(table, columnIndex) {
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const isAscending = table.getAttribute('data-sort-asc') === 'true';
    const direction = isAscending ? 1 : -1;

    rows.sort((a, b) => {
        const aText = a.children[columnIndex].textContent.trim();
        const bText = b.children[columnIndex].textContent.trim();

        return aText > bText ? (1 * direction) : (-1 * direction);
    });

    table.querySelector('tbody').append(...rows);
    table.setAttribute('data-sort-asc', !isAscending);
}

document.addEventListener('DOMContentLoaded', () => {
    fetch('all_player_metrics.json')
        .then(response => response.json())
        .then(data => populateTable('all-metrics-table', data));
});