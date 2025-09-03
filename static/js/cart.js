// Cart management functions
function updateCartCount() {
    fetch('/products/api/cart-count/')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = data.count;
                if (data.count > 0) {
                    cartCount.style.display = 'inline-block';
                } else {
                    cartCount.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
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