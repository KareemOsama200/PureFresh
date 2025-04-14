document.addEventListener('DOMContentLoaded', function() {
    // Toggle between unit and carton price in product details
    const unitPriceOption = document.getElementById('unit-price-option');
    const cartonPriceOption = document.getElementById('carton-price-option');
    const isCartonInput = document.getElementById('is_carton');
    
    if (unitPriceOption && cartonPriceOption && isCartonInput) {
        unitPriceOption.addEventListener('click', function() {
            unitPriceOption.classList.add('active');
            cartonPriceOption.classList.remove('active');
            isCartonInput.checked = false;
        });
        
        cartonPriceOption.addEventListener('click', function() {
            cartonPriceOption.classList.add('active');
            unitPriceOption.classList.remove('active');
            isCartonInput.checked = true;
        });
    }
    
    // Initialize datepicker for admin forms
    const dateInputs = document.querySelectorAll('.datepicker');
    if (dateInputs.length > 0) {
        dateInputs.forEach(input => {
            flatpickr(input, {
                dateFormat: "Y-m-d",
                locale: {
                    firstDayOfWeek: 6 // Saturday
                }
            });
        });
    }
    
    // Quantity increment/decrement buttons
    const decrementBtns = document.querySelectorAll('.quantity-decrement');
    const incrementBtns = document.querySelectorAll('.quantity-increment');
    
    decrementBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.nextElementSibling;
            const value = parseInt(input.value);
            if (value > 1) {
                input.value = value - 1;
                // Trigger change event to update any dependent calculations
                input.dispatchEvent(new Event('change'));
            }
        });
    });
    
    incrementBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const value = parseInt(input.value);
            input.value = value + 1;
            // Trigger change event to update any dependent calculations
            input.dispatchEvent(new Event('change'));
        });
    });
    
    // Check if product has carton price before showing carton option
    const cartonPriceElement = document.getElementById('carton-price');
    if (cartonPriceElement && cartonPriceElement.dataset.price === "0") {
        const cartonOption = document.getElementById('carton-price-option');
        if (cartonOption) {
            cartonOption.style.display = 'none';
        }
    }
    
    // Flash message auto-close
    const flashMessages = document.querySelectorAll('.alert:not(.no-auto-close)');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.classList.add('fade-out');
                setTimeout(() => {
                    message.remove();
                }, 500);
            }, 5000);
        });
    }
    
    // Toggle password visibility
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const passwordInput = document.getElementById(this.dataset.target);
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Toggle icon
            this.innerHTML = type === 'password' ? 
                '<i class="fas fa-eye"></i>' : 
                '<i class="fas fa-eye-slash"></i>';
        });
    });
    
    // Order status color highlight
    const orderStatusElements = document.querySelectorAll('.order-status-badge');
    orderStatusElements.forEach(el => {
        const status = el.textContent.trim();
        
        switch(status) {
            case 'جاري التحضير':
                el.classList.add('bg-info');
                break;
            case 'تم الشحن':
                el.classList.add('bg-primary');
                break;
            case 'في الطريق':
                el.classList.add('bg-warning', 'text-dark');
                break;
            case 'تم التوصيل':
                el.classList.add('bg-success');
                break;
            case 'مرفوض':
            case 'تم الإلغاء':
                el.classList.add('bg-danger');
                break;
            default:
                el.classList.add('bg-secondary');
        }
    });
    
    // Order tracking visualization
    const orderStatusIndicator = document.getElementById('order-status-indicator');
    if (orderStatusIndicator) {
        const currentStatus = orderStatusIndicator.dataset.status;
        const steps = document.querySelectorAll('.status-step');
        
        let reachedCurrent = false;
        
        steps.forEach(step => {
            const stepStatus = step.dataset.status;
            
            if (reachedCurrent) {
                // Future steps
                step.classList.remove('active');
            } else {
                // Past and current steps
                step.classList.add('active');
                
                if (stepStatus === currentStatus) {
                    reachedCurrent = true;
                }
            }
        });
    }
});
