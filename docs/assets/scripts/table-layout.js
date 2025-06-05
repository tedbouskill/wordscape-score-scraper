// Add this helper function at the top of the file
function formatNumber(value) {
    if (typeof value === 'number') {
        return new Intl.NumberFormat().format(value);
    }
    return value;
}

function isNumeric(value) {
    return !isNaN(value) && !isNaN(parseFloat(value));
}

// Define table configurations
const TABLE_CONFIGS = {
    'player-metrics-dashboard-table': {
        columnGroups: {
            'Stars': ['Min Stars', 'Avg Stars', 'Max Stars'],
            'Ranks': ['Min Rank', 'Avg Rank', 'Max Rank', '1st Rank', 'Top 3 Rank'],
            'Weekends': ['Weekends Total', 'Weekends Missed','Weekends Played', 'Weekends %']
        },
        groupBorders: true
    },
    'recent-tournaments-table': {
        columnGroups: {
            'Stars': ['Min Stars', 'Avg Stars', 'Max Stars', 'Recent Stars'],
            'Ranks': ['Min Rank', 'Avg Rank', 'Max Rank', 'Recent Rank'],
            'Weekends': ['Weekends Skipped','Weekends Played']
        },
        groupBorders: true
    }
};

function populateTable(tableId, data) {
    const table = document.getElementById(tableId);
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    const config = TABLE_CONFIGS[tableId] || { columnGroups: {}, groupBorders: false };

    // Clear existing table content
    thead.innerHTML = '';
    tbody.innerHTML = '';

    // Get all headers and organize them
    const headers = Object.keys(data[0]);
    const groupedHeaders = Object.values(config.columnGroups).flat();
    const regularHeaders = headers.filter(header => !groupedHeaders.includes(header));

    if (Object.keys(config.columnGroups).length > 0) {
        // Create grouped table structure
        createGroupedTable(table, thead, tbody, data, regularHeaders, config);
    } else {
        // Create simple table structure
        createSimpleTable(table, thead, tbody, data, headers);
    }
}

function createGroupedTable(table, thead, tbody, data, regularHeaders, config) {
    const columnGroups = config.columnGroups

    // Create group header row
    const groupHeaderRow = document.createElement('tr');
    groupHeaderRow.className = 'group-header';

    // Create column header row
    const columnHeaderRow = document.createElement('tr');
    columnHeaderRow.className = 'column-header';

    let columnIndex = 0;

    // Add regular headers first
    regularHeaders.forEach(header => {
        const groupTh = document.createElement('th');
        groupTh.setAttribute('rowspan', '2');
        groupTh.textContent = header;
        // Set a data attribute for the column index
        groupTh.setAttribute('data-col-index', columnIndex);
        groupTh.classList.add('sortable');
        groupTh.addEventListener('click', (e) => {
            sortTableByColumn(table, parseInt(e.target.getAttribute('data-col-index')));
        });
        groupHeaderRow.appendChild(groupTh);
        columnIndex++;
    });

    // Add grouped columns
    Object.entries(columnGroups).forEach(([groupName, columns]) => {
        // Add group header
        const groupTh = document.createElement('th');
        groupTh.setAttribute('colspan', columns.length);
        groupTh.textContent = groupName;
        groupTh.className = 'border-x-2 border-black';
        groupHeaderRow.appendChild(groupTh);

        // Add individual column headers
        columns.forEach((header, i) => {
            const th = document.createElement('th');

            // Only add left border to first column in group
            th.className = i === 0 ? 'border-l-2 border-black' : '';
            // Add right border to last column in group
            if (i === columns.length - 1) {
                th.className += ' border-r-2 border-black';
            }

            if (header.includes(' Rank')) {
                th.textContent = header.replace(' Rank', '');
            } else if (header.includes(' Stars')) {
                th.textContent = header.replace(' Stars', '');
                th.className += ' text-right pr-4';
            } else if (header.includes(' Score')) {
                th.textContent = header.replace(' Score', '');
            } else if (header.includes('Weekends ')) {
                th.textContent = header.replace('Weekends ', '');
            }

            // Set a data attribute for the column index
            th.setAttribute('data-col-index', columnIndex);
            th.classList.add('sortable');
            th.addEventListener('click', (e) => {
                // Use the data attribute value for sorting
                sortTableByColumn(table, parseInt(e.target.getAttribute('data-col-index')));
            });
            columnHeaderRow.appendChild(th);
            columnIndex++;
        });
    });

    thead.appendChild(groupHeaderRow);
    thead.appendChild(columnHeaderRow);

    // Modify the data rows section:
    data.forEach(row => {
        const tr = document.createElement('tr');

        // Add regular columns first
        regularHeaders.forEach(header => {
            const td = document.createElement('td');
            td.className = isNumeric(row[header]) ? 'text-center' : 'text-left pl-4';
            td.textContent = formatNumber(row[header]);
            tr.appendChild(td);
        });

        // Add grouped columns
        Object.entries(columnGroups).forEach(([groupName, columns], groupIndex) => {
            columns.forEach((header, i) => {
                const td = document.createElement('td');
                td.className = 'text-left pl-4';

                if (header.includes('Stars')) {
                    td.className = 'text-right pr-4';
                } else if (isNumeric(row[header])) {
                    td.className = 'text-center';
                }

                // Add borders for group separation
                if (i === 0) {
                    td.className += ' border-l-2 border-black';
                } else if (i === columns.length - 1) {
                    td.className += ' border-r-2 border-black';
                }

                td.textContent = formatNumber(row[header]);
                tr.appendChild(td);
            });
        });

        tbody.appendChild(tr);
    });
}

function createSimpleTable(table, thead, tbody, data, headers) {
    // Create simple header row
    const headerRow = document.createElement('tr');
    headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        th.setAttribute('data-col-index', index);
        th.classList.add('sortable');
        th.addEventListener('click', () => sortTableByColumn(table, index));
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    // Create data rows
    data.forEach(row => {
        const tr = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            td.textContent = formatNumber(row[header]);
            td.className = 'text-center';
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
        const aText = a.children[columnIndex].textContent.trim().replace(/,/g, '');
        const bText = b.children[columnIndex].textContent.trim().replace(/,/g, '');

        // Check if the column contains numeric values (after removing commas)
        const aValue = isNaN(aText) ? aText : parseFloat(aText);
        const bValue = isNaN(bText) ? bText : parseFloat(bText);

        if (typeof aValue === 'number' && typeof bValue === 'number') {
            return (aValue - bValue) * direction;
        }
        return aValue > bValue ? (1 * direction) : (-1 * direction);
    });

    // Update the table body with sorted rows
    table.querySelector('tbody').append(...rows);
    table.setAttribute('data-sort-asc', !isAscending);

    // Update header indicators
    updateSortIndicators(table, columnIndex, isAscending);
}

function updateSortIndicators(table, columnIndex, isAscending) {
    // Select only the headers with the sortable class
    const headers = table.querySelectorAll('th.sortable');
    headers.forEach(header => {
        header.textContent = header.textContent.replace(' ▲', '').replace(' ▼', '');
    });

    // Find the header by its data attribute value
    const targetHeader = Array.from(headers).find(header => {
        return parseInt(header.getAttribute('data-col-index')) === columnIndex;
    });

    if (targetHeader) {
        targetHeader.textContent += isAscending ? ' ▲' : ' ▼';
    }
}

function filterTableByName(tableId, filterText) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    const filterNames = filterText.toLowerCase().split(',').map(name => name.trim()).filter(name => name);

    rows.forEach(row => {
        const nameCell = row.children[0]; // Assuming the name is in the first column
        const rowText = nameCell.textContent.toLowerCase();
        const isVisible = filterNames.some(name => rowText.includes(name));
        row.style.display = isVisible ? '' : 'none';
    });
}

function initializeTable(tableId, jsonUrl) {
    fetch(jsonUrl)
        .then(response => response.json())
        .then(data => {
            populateTable(tableId, data);

            const filterInput = document.getElementById('filter-input');
            filterInput.addEventListener('input', () => {
                filterTableByName(tableId, filterInput.value);
            });
        });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize table if present
    const table = document.querySelector('table');
    if (table) {
        const tableId = table.id;
        const jsonUrl = table.dataset.jsonUrl;
        initializeTable(tableId, jsonUrl);
    }
});
