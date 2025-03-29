/**
 * Lost & Found App - Homepage JavaScript
 * Handles item loading, search functionality, navbar behavior, flash messages, and item details modal
 */

// Wait for DOM to be fully loaded before executing code
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all components
    initItemLoader();
    initNavbarBehavior();
    initFlashMessages();
});

/**
 * Item loading and search functionality
 */
function initItemLoader() {
    const container = document.getElementById('newsfeed-container');
    const searchForm = document.getElementById('search-form');
    const itemDetailsModal = new bootstrap.Modal(document.getElementById('itemDetailsModal'), { keyboard: true });
    const claimItemButton = document.getElementById('claimItemButton');
    let currentItemId = null; // Store the current item ID for claiming

    /**
     * Load items with optional filters
     * @param {Object} filters - Filter parameters for the API
     */
    const loadItems = (filters = {}) => {
        // Show loading state
        if (container) {
            container.innerHTML = '<div class="col-12 text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        }
        
        const params = new URLSearchParams(filters);
        
        fetch(`/api/v2/found_items?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!container) return;
                
                container.innerHTML = '';
                
                if (!data.items || data.items.length === 0) {
                    container.innerHTML = '<div class="col-12"><div class="alert alert-info">No items found matching your criteria.</div></div>';
                    return;
                }

                data.items.forEach(item => {
                    // Calculate days ago using time_created
                    const itemDate = new Date(item.time_created || item.date_lost_found);
                    const daysAgo = Math.ceil((new Date() - itemDate) / (1000 * 60 * 60 * 24));
                    
                    
                    // Create item HTML
                    const itemHtml = `
                        <div class="col-md-4 mb-4">
                            <div class="newsfeed-item card h-100" data-id="${item.id}">
                                <img src="${item.item_image || '/static/images/default-item-image.jpg'}" 
                                     class="card-img-top" alt="Item Image" style="height: 200px; object-fit: cover;">
                                <div class="card-body">
                                    <div class="report-date text-muted small">Reported: ${daysAgo} day${daysAgo !== 1 ? 's' : ''} ago</div>
                                    <div class="location"><i class="fas fa-map-marker-alt me-1"></i>${item.location_found || 'Unknown'}</div>
                                    <p class="mt-2">${item.item_name}</p>
                                    <div class="claims-count mt-auto text-end">
                                        <span class="badge bg-secondary">Claims: ${item.number_of_claims || 0}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    container.insertAdjacentHTML('beforeend', itemHtml);
                });

                // Add click event to show item details in modal
                document.querySelectorAll('.newsfeed-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const itemId = item.getAttribute('data-id');
                        currentItemId = itemId; // Store the item ID for claiming
                        fetchItemDetails(itemId);
                        itemDetailsModal.show();
                    });
                });
            })
            .catch(error => {
                console.error('Error loading items:', error);
                if (container) {
                    container.innerHTML = `<div class="col-12"><div class="alert alert-danger">Error loading items. Please try again.</div></div>`;
                }
            });
    };

    /**
     * Fetch item details and populate the modal
     * @param {string} itemId - The ID of the item to fetch
     */
    const fetchItemDetails = (itemId) => {
        fetch(`/api/v2/item/${itemId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Populate modal elements
                document.getElementById('itemModalName').textContent = data.item_name || 'Unknown Item';
                document.getElementById('itemModalImage').src = data.item_image || data.image_url || '/static/images/default-item-image.jpg';
                document.getElementById('itemModalDescription').textContent = data.description || 'No description available';
                document.getElementById('itemModalLocation').textContent = `Location: ${data.location_found || data.location_lost_found || 'Unknown'}`;

                // Handle extra details for admin/QC users
                const extraDetails = document.getElementById('itemModalExtraDetails');
                extraDetails.innerHTML = '';
                if (data.item_category) {
                    extraDetails.innerHTML += `<p><strong>Category:</strong> ${data.item_category}</p>`;
                }
                if (data.item_color) {
                    extraDetails.innerHTML += `<p><strong>Color:</strong> ${data.item_color}</p>`;
                }
                if (data.item_brand) {
                    extraDetails.innerHTML += `<p><strong>Brand:</strong> ${data.item_brand}</p>`;
                }
                if (data.date_lost_found) {
                    extraDetails.innerHTML += `<p><strong>Date Lost/Found:</strong> ${new Date(data.date_lost_found).toLocaleDateString()}</p>`;
                }
            })
            .catch(error => {
                console.error('Error fetching item details:', error);
                document.getElementById('itemModalDescription').textContent = 'Error loading item details.';
            });
    };

    /**
     * Handle item claim action
     */
    const claimItem = () => {
        if (!currentItemId) return;
        
        fetch(`/api/v2/make_claim/${currentItemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Show success message
                alert('Claim submitted successfully!');
                itemDetailsModal.hide();
                // Reload items to update claims count
                loadItems({ status: 'found' });
            })
            .catch(error => {
                console.error('Error claiming item:', error);
                alert('Failed to submit claim. Please try again.');
            });
    };

    // Attach claim button event listener
    if (claimItemButton) {
        claimItemButton.addEventListener('click', claimItem);
    }

    // Initial load of found items
    loadItems({ status: 'found' });

    // Set up search form functionality
    if (searchForm) {
        searchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const filters = {
                status: 'found',
                search: document.getElementById('search-input')?.value || '',
                category: document.getElementById('filter-category')?.value || '',
                date_start: document.getElementById('filter-date-start')?.value || '',
                date_end: document.getElementById('filter-date-end')?.value || '',
                location: document.getElementById('filter-location')?.value || ''
            };
            loadItems(filters);
        });
    }
}

/**
 * Navbar scroll behavior
 */
function initNavbarBehavior() {
    const header = document.querySelector('.fixed-header');
    if (!header) return;
    
    let lastScrollTop = 0;
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        header.style.transition = 'top 0.3s ease-in-out';
        header.style.top = scrollTop > lastScrollTop && scrollTop > header.offsetHeight ? '-80px' : '0';
        lastScrollTop = scrollTop;
    });
}

/**
 * Flash messages handling
 */
function initFlashMessages() {
    const flashContainer = document.querySelector('.flash-container');
    if (!flashContainer) return;
    
    const alerts = flashContainer.querySelectorAll('.alert');
    
    // Hide container if no messages
    if (!alerts || alerts.length === 0) {
        flashContainer.style.display = 'none';
        return;
    }
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        alerts.forEach(alert => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.classList.remove('show');
                alert.addEventListener('transitionend', () => {
                    alert.remove();
                });
            }
        });
        
        setTimeout(() => {
            flashContainer.style.display = 'none';
        }, 500);
    }, 5000);
}