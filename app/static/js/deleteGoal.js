document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', function() {
        if (confirm('Are you sure you want to delete this saving goal?')) {
            fetch(this.dataset.url, {
                method: 'DELETE',
            })
            .then(response => {
                if (response.ok) {
                    window.location.href = window.successRedirectUrl;
                }
            });
        }
    });
});
