document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('qr-form');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('logo');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadContent = document.querySelector('.upload-content');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('span');
    const loader = submitBtn.querySelector('.loader');
    
    const resultContainer = document.getElementById('result-container');
    const actionButtons = document.getElementById('action-buttons');
    const downloadBtn = document.getElementById('download-btn');

    // Drag and Drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileDisplay();
        }
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', updateFileDisplay);

    function updateFileDisplay() {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            fileNameDisplay.textContent = `Arquivo: ${file.name}`;
            fileNameDisplay.classList.remove('hidden');
            uploadContent.classList.add('hidden');
            // Auto submit when file is selected
            form.dispatchEvent(new Event('submit'));
        } else {
            fileNameDisplay.classList.add('hidden');
            uploadContent.classList.remove('hidden');
        }
    }

    // Live preview: auto submit form on changes
    let timeoutId;
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (input.type === 'text') {
            input.addEventListener('input', () => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    if (input.value.trim() !== '') {
                        form.dispatchEvent(new Event('submit'));
                    }
                }, 800);
            });
        } else if (input.type !== 'file') {
            input.addEventListener('change', () => {
                form.dispatchEvent(new Event('submit'));
            });
        }
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (document.getElementById('words').value.trim() === '') return;
        
        // UI Loading state
        submitBtn.disabled = true;
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        
        const formData = new FormData(form);
        // Handle checkbox properly for form data
        const roundedCheckbox = document.getElementById('rounded');
        if (roundedCheckbox) formData.set('rounded', roundedCheckbox.checked);
        
        const transparentCheckbox = document.getElementById('transparent');
        if (transparentCheckbox) formData.set('transparent', transparentCheckbox.checked);

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show result (Base64 data url)
                resultContainer.innerHTML = `<img src="${result.image_url}" alt="QR Code Gerado" class="result-image">`;
                downloadBtn.href = result.image_url;
                downloadBtn.download = "qrcode.png";
                actionButtons.classList.remove('hidden');
            } else {
                alert('Erro ao gerar QR Code: ' + result.error);
            }
        } catch (error) {
            console.error(error);
        } finally {
            // Restore UI
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });
});
