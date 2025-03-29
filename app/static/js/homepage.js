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
                    
                    
                    // Updated newsfeed item HTML generation
                    const itemHtml = `
                        <div class="col-sm-6 col-lg-4 mb-4">
                            <div class="newsfeed-item card h-100 shadow-sm hover-effect" data-id="${item.id}">
                                <div class="card-img-wrapper">
                                    <img src="${item.item_image || '/static/images/default-item-image.jpg'}" 
                                         class="card-img-top" alt="${item.item_name || 'Lost Item'}" loading="lazy">
                                    <div class="item-category">
                                        <span class="badge bg-primary">${item.item_category || 'Misc'}</span>
                                    </div>
                                </div>
                                
                                <div class="card-body d-flex flex-column p-3">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span class="text-muted small">
                                            <i class="fas fa-clock me-1"></i> ${daysAgo} day${daysAgo !== 1 ? 's' : ''} ago
                                        </span>
                                        <span class="badge ${item.number_of_claims > 0 ? 'bg-warning text-dark' : 'bg-light text-secondary'} claims-badge">
                                            ${item.number_of_claims || 0} claim${item.number_of_claims !== 1 ? 's' : ''}
                                        </span>
                                    </div>
                                    
                                    <h5 class="card-title mb-2">${item.item_name || 'Unknown Item'}</h5>
                                    
                                    <div class="location-display mb-3">
                                        <i class="fas fa-map-marker-alt text-danger me-1"></i>
                                        <span class="text-muted">${item.location_found || 'Unknown location'}</span>
                                    </div>
                                    
                                    <div class="mt-auto text-end">
                                        <button class="btn btn-sm btn-outline-primary view-details-btn">View Details</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    container.insertAdjacentHTML('beforeend', itemHtml);
                });

                // Add click event to show item details in modal
                document.querySelectorAll('.newsfeed-item').forEach(item => {
                    const viewDetailsBtn = item.querySelector('.view-details-btn');
                    
                    // Make whole card clickable
                    item.addEventListener('click', (e) => {
                        // Only trigger if not clicking the button (button has its own handler)
                        if (!e.target.closest('.view-details-btn')) {
                            const itemId = item.getAttribute('data-id');
                            currentItemId = itemId;
                            fetchItemDetails(itemId);
                            itemDetailsModal.show();
                        }
                    });
                    
                    // Button click handler
                    if (viewDetailsBtn) {
                        viewDetailsBtn.addEventListener('click', (e) => {
                            e.stopPropagation(); // Prevent card click
                            const itemId = item.getAttribute('data-id');
                            currentItemId = itemId;
                            fetchItemDetails(itemId);
                            itemDetailsModal.show();
                        });
                    }
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
        
        // Redirect to the claim page instead of making an API call
        window.location.href = `/make_claim/${currentItemId}`;
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
                search_query: document.getElementById('search-input')?.value.toLowerCase() || '',
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