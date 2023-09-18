// Define the number of items per page
const itemsPerPage = 10;

// Get the logs data from the server (assuming it's already fetched)

// Calculate the total number of pages
const totalPages = Math.ceil(logs.length / itemsPerPage);

// Initialize the current page to 1
let currentPage = 1;

// Function to render the logs based on the current page number
function renderLogs() {
  // Clear the existing logs
  const tbody = document.querySelector('tbody');
  tbody.innerHTML = '';

  // Calculate the start and end index of the logs to be displayed
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;

  // Iterate over the logs within the range and append them to the table
  for (let i = startIndex; i < endIndex && i < logs.length; i++) {
    const log = logs[i];

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${log.message}</td>
      <td>${log.actor}</td>
      <td>${log.action}</td>
      <td>${log.target}</td>
      <td>${log.status}</td>
    `;

    tbody.appendChild(row);
  }
}

// Function to update the current page and re-render the logs
function updatePage(page) {
  currentPage = page;
  renderLogs();
}

// Add event listeners to the pagination buttons
const paginationButtons = document.querySelectorAll('.pagination-button');
paginationButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const page = parseInt(button.dataset.page);
    updatePage(page);
  });
});

// Render the initial logs
renderLogs();
