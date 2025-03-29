document.addEventListener('DOMContentLoaded', function () {
    const claimLinks = document.querySelectorAll('.claim-link');

    claimLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            const claimId = this.getAttribute('data-claim-id');
            showClaimModal(claimId);
        });
    });

    function showClaimModal(claimId) {
        //calling the claim api
         fetch(`/claims/${claimId}`)
            .then(response => response.json())
            .then(data => {
                const modal = document.createElement('div');
                modal.classList.add('modal', 'fade');
                modal.setAttribute('tabindex', '-1');
                modal.setAttribute('role', 'dialog');
                                 
                // Determine if there is an item image
                const hasItemImage = data.item_image_url && data.item_image_url.trim() !== '';

                // Modal content based on image availability
                modal.innerHTML = `
                <div class="modal fade" id="claimModal" tabindex="-1" role="dialog" aria-labelledby="claimModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                                <h5 class="modal-title">Claim ${data.claim_id} Details</h5>
                                <button type="button" class="close" data-bs-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">

                                ${hasItemImage ? `
                                    <p><strong>ITEM IMAGE :</strong></p>
                                    <img src="${data.item_image_url}" class="img-fluid" alt="Item Image">
                                ` : `
                                    <p><strong>CLAIM IMAGE :</strong></p>

                                    <img src="${data.image_url}" class="img-fluid" alt="Claim Image">
                                `}
                            <p><strong>Claim status :</strong> ${data.status || 'Not Available'}</p>
                            <p><strong>Claim additional information:</strong> ${data.additional_information ? data.additional_information : 'Not Available'}</p>

                            <p><strong>Item Name:</strong> ${data.item_name || 'Not Available'}</p>
                            <p><strong>Description:</strong> ${data.item_description || 'Not Available'}</p>
                            <p><strong>Category:</strong> ${data.item_category || 'Not Available'}</p>
                            <p><strong>Status:</strong> ${data.item_status || 'Not Available'}</p>
                            <p><strong>Date Reported:</strong> ${data.date_reported || 'Not Available'}</p>
                            <p><strong>User Name:</strong> ${data.user_name || 'Not Available'}</p>
                            <p><strong>User Email:</strong> ${data.user_email || 'Not Available'}</p>
                            <p><strong>User Phone:</strong> ${data.user_phone || 'Not Available'}</p>
                            <p><strong>Color:</strong> ${data.item_color || 'Not Available'}</p>
                            <p><strong>Brand:</strong> ${data.item_brand || 'Not Available'}</p>
                            <p><strong>Date Lost/Found:</strong> ${data.date_lost_found || 'Not Available'}</p>
                            <p><strong>Location Lost/Found:</strong> ${data.location_lost_found || 'Not Available'}</p>
                              </div>
                            </div>
 
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();
                modal.addEventListener('hidden.bs.modal', function () {
                    document.body.removeChild(modal);
                });
            })
            .catch(error => {
                console.error('Error fetching claim details:', error);
            });
    }
});

// keeps the navbar fixed at the top when scrolling up, but disappear when scrolling down.
document.addEventListener('DOMContentLoaded', function () {
    const header = document.querySelector('.fixed-header');
    let lastScrollTop = 0;

    window.addEventListener('scroll', function () {
        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > lastScrollTop) {
            header.style.top = '-80px';
        } else {
            header.style.top = '0';
        }

        lastScrollTop = scrollTop;
    });
});

// logic to populate the newsfeed, and search/filter algorithm
$(document).ready(function() {
    function loadItems(searchQuery = '', filters = {}) {
        $.ajax({
            url: 'http://127.0.0.1:5000/api/items',
            method: 'GET',
            success: function(response) {
                const items = response.items;
                let filteredItems = items;

                // Filter items based on search query (in name and description)
                if (searchQuery) {
                    filteredItems = filteredItems.filter(item => 
                        item.item_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        item.description.toLowerCase().includes(searchQuery.toLowerCase())
                    );
                }

                // Filter items based on selected category
                if (filters.category) {
                    filteredItems = filteredItems.filter(item => item.item_category === filters.category);
                }

                // Filter items based on location
                if (filters.location) {
                    filteredItems = filteredItems.filter(item => item.location_lost_found.toLowerCase().includes(filters.location.toLowerCase()));
                }

                // Filter items based on start date
                if (filters.dateStart) {
                    filteredItems = filteredItems.filter(item => new Date(item.date_reported) >= new Date(filters.dateStart));
                }

                // Filter items based on end date
                if (filters.dateEnd) {
                    filteredItems = filteredItems.filter(item => new Date(item.date_reported) <= new Date(filters.dateEnd));
                }

                // Sort items by date reported (newest first)
                filteredItems.sort((a, b) => new Date(b.date_reported) - new Date(a.date_reported));

                // Clear the current items in the newsfeed container
                $('#newsfeed-container').empty();

                // Append each filtered item to the newsfeed container
                filteredItems.forEach(item => {
                    // Calculate the number of days since the item was reported
                    const daysAgo = Math.ceil((new Date() - new Date(item.date_reported)) / (1000 * 60 * 60 * 24));
                    // Shorten the description if it is too long
                    const description = item.description.length > 100 ? item.description.substring(0, 97) + '...' : item.description;
                    // Generate the HTML for the item
                    const itemHtml = `
                        <div class="col-md-4">
                            <div class="newsfeed-item" data-id="${item.id}">
 
                                <img src="${item.image_url}" alt="Item Image">
                                <div class="report-date">Reported: ${daysAgo} days ago</div>
                                <div class="location">${item.location_lost_found}</div>
                                <p>${description}</p>
                                <div class="claims-count">Claims: ${item.claims_count}</div>
                            </div>
                        </div>
                    `;
                    // Append the generated HTML to the newsfeed container
                    $('#newsfeed-container').append(itemHtml);
                });

                // Add click event listener to each newsfeed item to redirect to the item's detail page
                $('.newsfeed-item').click(function() {
                    const itemId = $(this).data('id');
                    window.location.href = `/item/${itemId}`;
                });
            }
        });
    }

    // Event handler for the search form submission
    $('#search-form').submit(function(event) {
        event.preventDefault();  // Prevent the default form submission
        const query = $('#search-input').val();  // Get the search query from the input
        // Get filter values
        const filters = {
            category: $('#filter-category').val(),
            location: $('#filter-location').val(),
            dateStart: $('#filter-date-start').val(),
            dateEnd: $('#filter-date-end').val()
        };
        // Load items with the search query and filters
        loadItems(query, filters);
    });

    // Event handler for the filter button click
    $('#filter-button').click(function() {
        // Get filter values
        const filters = {
            category: $('#filter-category').val(),
            location: $('#filter-location').val(),
            dateStart: $('#filter-date-start').val(),
            dateEnd: $('#filter-date-end').val()
        };
        // Load items with the filters
        loadItems('', filters);
    });

    // Initial load of items when the page is first loaded
    loadItems();
});

document.addEventListener('DOMContentLoaded', function () {
    const claimLinks = document.querySelectorAll('.claim-link');

    claimLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            const claimId = this.getAttribute('data-claim-id');
            showClaimModal(claimId);
        });
    });

    function showClaimModal(claimId) {
        const modal = document.createElement('div');
        modal.classList.add('modal', 'fade');
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('role', 'dialog');
        modal.innerHTML = `
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Claim ${claimId} Details</h5>
                        <button type="button" class="close" data-bs-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <img src="https://via.placeholder.com/600x400" class="img-fluid" alt="Claim ${claimId} Image">
                        <p>Details for claim ${claimId}...</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        modal.addEventListener('hidden.bs.modal', function () {
            document.body.removeChild(modal);
        });
    }

    window.confirmAction = function(action, claimId = null) {
        const message = action === 'merge' 
            ? 'Are you sure you want to merge successful claims?' 
            : `Are you sure you want to ${action} claim ${claimId}?`;
        if (confirm(message)) {
            // Perform the action here (e.g., send a request to the server)
            console.log(`${action} action confirmed for claim ${claimId}`);
        }
    };
});
