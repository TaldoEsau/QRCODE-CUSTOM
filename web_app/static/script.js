document.addEventListener('DOMContentLoaded', () => {
    // --- Tabs Navigation ---
    const tabSheet = document.getElementById('tab-sheet');
    const tabSingle = document.getElementById('tab-single');
    const sheetView = document.getElementById('sheet-view');
    const singleView = document.getElementById('single-view');

    tabSheet.addEventListener('click', () => {
        tabSheet.classList.add('active');
        tabSingle.classList.remove('active');
        sheetView.classList.add('active');
        singleView.classList.remove('active');
    });

    tabSingle.addEventListener('click', () => {
        tabSingle.classList.add('active');
        tabSheet.classList.remove('active');
        singleView.classList.add('active');
        sheetView.classList.remove('active');
    });

    // --- Toast Helper ---
    const toast = document.getElementById('toast');
    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.remove('hidden');
        clearTimeout(toast._timeout);
        toast._timeout = setTimeout(() => {
            toast.classList.add('hidden');
        }, 3200);
    }

    // --- Color Presets ---
    document.querySelectorAll('.color-preset-dot').forEach(dot => {
        dot.addEventListener('click', (e) => {
            e.stopPropagation();
            const targetId = dot.getAttribute('data-target');
            const color = dot.getAttribute('data-color');
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                targetInput.value = color;
                dot.parentElement.querySelectorAll('.color-preset-dot').forEach(d => d.classList.remove('active'));
                dot.classList.add('active');
                if (targetId === 'sheet_fg_color') {
                    triggerDebouncedSheetSubmit();
                }
            }
        });
    });

    // ==========================================
    // 1. ABA: EXPORTADOR DE FOLHA A4 (2 ARTES)
    // ==========================================
    const sheetForm = document.getElementById('sheet-form');
    const sameQrCheckbox = document.getElementById('same_qr');
    const groupWordsRight = document.getElementById('group-words-right');
    const labelWordsLeft = document.getElementById('label-words-left');
    const wordsLeftInput = document.getElementById('words_left');
    const wordsRightInput = document.getElementById('words_right');
    const sheetRoundedCheckbox = document.getElementById('sheet_rounded');
    const sheetFgColorInput = document.getElementById('sheet_fg_color');

    // Logo choice elements
    const logoChoiceCards = document.querySelectorAll('.logo-option-card');
    const sheetCustomLogoContainer = document.getElementById('sheet-custom-logo-container');
    const sheetLogoHint = document.getElementById('sheet-logo-hint');
    const sheetDropZone = document.getElementById('sheet-custom-logo-container');
    const sheetCustomLogoInput = document.getElementById('sheet_custom_logo');
    const sheetUploadContent = document.getElementById('sheet-upload-content');
    const sheetFilePreviewWrap = document.getElementById('sheet-file-preview-wrap');
    const sheetLogoThumb = document.getElementById('sheet-logo-thumb');
    const sheetFileName = document.getElementById('sheet-file-name');
    const sheetRemoveLogoBtn = document.getElementById('sheet-remove-logo-btn');

    let currentLogoChoice = 'google';
    let customLogoFile = null;

    const btnGenerateSheet = document.getElementById('btn-generate-sheet');
    const sheetLoader = document.getElementById('sheet-loader');
    const sheetBtnLabel = btnGenerateSheet.querySelector('.btn-label');
    const sheetPreviewImg = document.getElementById('sheet-preview-img');
    const sheetEmptyState = document.getElementById('sheet-empty-state');
    const sheetLoadingOverlay = document.getElementById('sheet-loading-overlay');
    const sheetExportActions = document.getElementById('sheet-export-actions');
    const downloadSheetPdfBtn = document.getElementById('download-sheet-pdf-btn');
    const downloadSheetPngBtn = document.getElementById('download-sheet-png-btn');
    const printSheetBtn = document.getElementById('print-sheet-btn');

    // Toggle same QR checkbox
    sameQrCheckbox.addEventListener('change', () => {
        if (sameQrCheckbox.checked) {
            groupWordsRight.classList.add('hidden');
            labelWordsLeft.textContent = 'Link das Avaliações (Ambas as Placas)';
        } else {
            groupWordsRight.classList.remove('hidden');
            labelWordsLeft.textContent = 'Link da Placa 1 (Lado Esquerdo)';
            if (!wordsRightInput.value) {
                wordsRightInput.value = wordsLeftInput.value;
            }
        }
        triggerDebouncedSheetSubmit();
    });

    // Logo mode selector clicks
    logoChoiceCards.forEach(card => {
        card.addEventListener('click', () => {
            logoChoiceCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            const radio = card.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                currentLogoChoice = radio.value;
            }

            if (currentLogoChoice === 'google') {
                sheetCustomLogoContainer.classList.add('hidden');
                sheetLogoHint.textContent = 'Logo oficial do Google com fundo transparente.';
            } else if (currentLogoChoice === 'custom') {
                sheetCustomLogoContainer.classList.remove('hidden');
                sheetLogoHint.textContent = 'Carregue a imagem que você deseja colocar no centro dos QR Codes.';
            } else if (currentLogoChoice === 'none') {
                sheetCustomLogoContainer.classList.add('hidden');
                sheetLogoHint.textContent = 'O QR Code será gerado limpo, sem nenhuma imagem no centro.';
            }

            triggerDebouncedSheetSubmit();
        });
    });

    // Drag & drop and upload handling for sheet custom logo
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(name => {
        sheetDropZone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    sheetDropZone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length > 0) {
            handleCustomLogoFile(e.dataTransfer.files[0]);
        }
    });

    sheetDropZone.addEventListener('click', (e) => {
        if (!e.target.closest('#sheet-remove-logo-btn')) {
            sheetCustomLogoInput.click();
        }
    });

    sheetCustomLogoInput.addEventListener('change', () => {
        if (sheetCustomLogoInput.files.length > 0) {
            handleCustomLogoFile(sheetCustomLogoInput.files[0]);
        }
    });

    function handleCustomLogoFile(file) {
        if (!file.type.startsWith('image/')) {
            showToast('Por favor, selecione um arquivo de imagem válido (PNG, JPG, WebP).');
            return;
        }
        customLogoFile = file;
        sheetFileName.textContent = file.name;

        const reader = new FileReader();
        reader.onload = (e) => {
            sheetLogoThumb.src = e.target.result;
            sheetFilePreviewWrap.classList.remove('hidden');
            sheetUploadContent.classList.add('hidden');
            triggerDebouncedSheetSubmit();
        };
        reader.readAsDataURL(file);
    }

    sheetRemoveLogoBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        customLogoFile = null;
        sheetCustomLogoInput.value = '';
        sheetLogoThumb.src = '';
        sheetFilePreviewWrap.classList.add('hidden');
        sheetUploadContent.classList.remove('hidden');
        triggerDebouncedSheetSubmit();
    });

    // Debounced submission on input changes
    let sheetTimeout;
    function triggerDebouncedSheetSubmit() {
        clearTimeout(sheetTimeout);
        sheetTimeout = setTimeout(() => {
            if (wordsLeftInput.value.trim() !== '') {
                sheetForm.dispatchEvent(new Event('submit'));
            }
        }, 500);
    }

    wordsLeftInput.addEventListener('input', triggerDebouncedSheetSubmit);
    wordsRightInput.addEventListener('input', triggerDebouncedSheetSubmit);
    sheetRoundedCheckbox.addEventListener('change', triggerDebouncedSheetSubmit);
    sheetFgColorInput.addEventListener('input', triggerDebouncedSheetSubmit);

    // Form Submission: Generate Sheet
    sheetForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const wordsLeft = wordsLeftInput.value.trim();
        if (!wordsLeft) {
            showToast('Por favor, informe o link para o QR Code.');
            wordsLeftInput.focus();
            return;
        }

        // Loading state
        btnGenerateSheet.disabled = true;
        sheetBtnLabel.classList.add('hidden');
        sheetLoader.classList.remove('hidden');
        sheetLoadingOverlay.classList.remove('hidden');

        const formData = new FormData();
        formData.append('words_left', wordsLeft);
        formData.append('same_qr', sameQrCheckbox.checked);
        if (!sameQrCheckbox.checked) {
            formData.append('words_right', wordsRightInput.value.trim() || wordsLeft);
        }
        formData.append('logo_type', currentLogoChoice);
        formData.append('use_google_logo', currentLogoChoice === 'google');
        if (currentLogoChoice === 'custom' && customLogoFile) {
            formData.append('custom_logo', customLogoFile);
        }
        formData.append('rounded', sheetRoundedCheckbox.checked);
        formData.append('fg_color', sheetFgColorInput.value);

        try {
            const response = await fetch('/generate-sheet', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Display preview image
                sheetPreviewImg.src = result.preview_url;
                sheetPreviewImg.classList.remove('hidden');
                sheetEmptyState.classList.add('hidden');

                // Configure download buttons
                downloadSheetPdfBtn.href = result.pdf_url;
                downloadSheetPngBtn.href = result.png_url;

                sheetExportActions.classList.remove('hidden');
            } else {
                showToast('Erro: ' + (result.error || 'Falha ao gerar folha'));
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showToast('Erro de conexão ao gerar a folha.');
        } finally {
            btnGenerateSheet.disabled = false;
            sheetBtnLabel.classList.remove('hidden');
            sheetLoader.classList.add('hidden');
            sheetLoadingOverlay.classList.add('hidden');
        }
    });

    // Direct Print Button
    printSheetBtn.addEventListener('click', () => {
        if (!sheetPreviewImg.src) return;

        const printWin = window.open('', '_blank');
        if (!printWin) {
            showToast('Permita pop-ups no navegador para imprimir diretamente.');
            return;
        }

        printWin.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Imprimir Folha A4 - Display de Balcão</title>
                <style>
                    @page {
                        size: A4 landscape;
                        margin: 0;
                    }
                    html, body {
                        margin: 0;
                        padding: 0;
                        width: 100%;
                        height: 100%;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        background: #ffffff;
                    }
                    img {
                        width: 100%;
                        height: 100%;
                        object-fit: contain;
                    }
                </style>
            </head>
            <body>
                <img src="${sheetPreviewImg.src}" onload="window.print(); window.close();" />
            </body>
            </html>
        `);
        printWin.document.close();
    });

    // ==========================================
    // 2. ABA: QR CODE AVULSO
    // ==========================================
    const singleForm = document.getElementById('single-qr-form');
    const singleWords = document.getElementById('single_words');
    const singleDropZone = document.getElementById('single-drop-zone');
    const singleLogoInput = document.getElementById('single_logo');
    const singleFileName = document.getElementById('single-file-name');
    const singleUploadContent = document.getElementById('single-upload-content');
    const singleSubmitBtn = document.getElementById('single-submit-btn');
    const singleLoader = document.getElementById('single-loader');
    const singleBtnLabel = singleSubmitBtn.querySelector('.btn-label');
    const singleResultContainer = document.getElementById('single-result-container');
    const singleActionButtons = document.getElementById('single-action-buttons');
    const singleDownloadBtn = document.getElementById('single-download-btn');

    // Drag and drop for single logo
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(name => {
        singleDropZone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    singleDropZone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length > 0) {
            singleLogoInput.files = e.dataTransfer.files;
            updateSingleFileDisplay();
        }
    });

    singleDropZone.addEventListener('click', () => singleLogoInput.click());
    singleLogoInput.addEventListener('change', updateSingleFileDisplay);

    function updateSingleFileDisplay() {
        if (singleLogoInput.files.length > 0) {
            singleFileName.textContent = `Logo: ${singleLogoInput.files[0].name}`;
            singleFileName.classList.remove('hidden');
            singleUploadContent.classList.add('hidden');
            singleForm.dispatchEvent(new Event('submit'));
        } else {
            singleFileName.classList.add('hidden');
            singleUploadContent.classList.remove('hidden');
        }
    }

    // Auto submit on input change for single QR
    let singleTimeout;
    singleWords.addEventListener('input', () => {
        clearTimeout(singleTimeout);
        singleTimeout = setTimeout(() => {
            if (singleWords.value.trim() !== '') {
                singleForm.dispatchEvent(new Event('submit'));
            }
        }, 700);
    });

    ['single_rounded', 'single_transparent', 'single_fg_color'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', () => singleForm.dispatchEvent(new Event('submit')));
        }
    });

    singleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!singleWords.value.trim()) return;

        singleSubmitBtn.disabled = true;
        singleBtnLabel.classList.add('hidden');
        singleLoader.classList.remove('hidden');

        const formData = new FormData(singleForm);
        const roundedCheckbox = document.getElementById('single_rounded');
        if (roundedCheckbox) formData.set('rounded', roundedCheckbox.checked);

        const transparentCheckbox = document.getElementById('single_transparent');
        if (transparentCheckbox) formData.set('transparent', transparentCheckbox.checked);

        try {
            const res = await fetch('/generate', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.success) {
                singleResultContainer.innerHTML = `<img src="${data.image_url}" alt="QR Code" class="sheet-img">`;
                singleDownloadBtn.href = data.image_url;
                singleDownloadBtn.download = "qrcode.png";
                singleActionButtons.classList.remove('hidden');
            } else {
                showToast('Erro: ' + (data.error || 'Falha ao gerar QR Code'));
            }
        } catch (err) {
            console.error(err);
            showToast('Erro ao comunicar com o servidor.');
        } finally {
            singleSubmitBtn.disabled = false;
            singleBtnLabel.classList.remove('hidden');
            singleLoader.classList.add('hidden');
        }
    });

    // --- Inicia com a Folha Gerada Automaticamente ---
    sheetForm.dispatchEvent(new Event('submit'));
});
