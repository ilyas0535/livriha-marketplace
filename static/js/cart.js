// Cart management functions
function updateCartCount() {
    // Skip cart count update for now to avoid 404 errors
    return;
}

// Update cart count on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
});

// Update cart count after form submissions
document.addEventListener('submit', function(e) {
    if (e.target.action && (e.target.action.includes('add-to-cart') || e.target.action.includes('update-cart'))) {
        setTimeout(updateCartCount, 500);
    }
});

// Update cart count after adding items
function addToCartAndUpdate(productId) {
    fetch(`/products/add-to-cart/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (response.ok) {
            updateCartCount();
        }
    })
    .catch(error => console.error('Error adding to cart:', error));
}