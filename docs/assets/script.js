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
    headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        th.addEventListener('click', () => {
            sortTableByColumn(table, index);
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

    // Update header to show sort direction
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        header.textContent = header.textContent.replace(' ▲', '').replace(' ▼', '');
        if (index === columnIndex) {
            header.textContent += isAscending ? ' ▲' : ' ▼';
        }
    });
}

function filterTableByName(tableId, filterText) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const nameCell = row.children[0]; // Assuming the name is in the first column
        if (nameCell.textContent.toLowerCase().includes(filterText.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    fetch('all_player_metrics.json')
        .then(response => response.json())
        .then(data => populateTable('all-metrics-table', data));

    const filterInput = document.getElementById('filter-input');
    filterInput.addEventListener('input', () => {
        filterTableByName('all-metrics-table', filterInput.value);
    });
});