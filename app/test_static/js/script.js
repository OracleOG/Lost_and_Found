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
});

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



