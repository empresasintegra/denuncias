/**
 * APLICACIÓN DE DENUNCIAS - JAVASCRIPT CONSOLIDADO
 * Autor: Sistema de Denuncias Integra
 * Versión: 1.2 - Corregido formateo de celular
 */

// Namespace principal
const DenunciaApp = {
    // Configuración global
    config: {
        sessionTimeout: 1800000, // 30 minutos
        maxFileSize: 500 * 1024 * 1024, // 500MB
        allowedFileTypes: ['.pdf','.doc','.docx','.jpg','.jpeg','.png','.gif','.xlsx','.xls','.txt']
    },

    // Variables globales
    vars: {
        currentStep: 0,
        totalSteps: 4,
        selectedFiles: []
    },

    // Detección de página actual - MEJORADA
    getCurrentPage: function() {
        console.log('🔍 Detectando página actual...');
        console.log('📍 URL actual:', window.location.pathname);
        
        // Detectar por elementos únicos en el DOM
        if (document.getElementById('codigo-texto')) {
            console.log('✅ Página detectada: CÓDIGO');
            return 'codigo';
        }
        
        if (document.getElementById('smartwizard')) {
            console.log('✅ Página detectada: WIZARD');
            return 'wizard';
        }
        
        if (document.getElementById('usuarioForm')) {
            console.log('✅ Página detectada: USUARIO');
            return 'usuario';
        }
        
        if (document.getElementById('denunciaForm')) {
            console.log('✅ Página detectada: ITEMS');
            return 'items';
        }

        console.log('⚠️ Página no reconocida');
        return 'unknown';
    },

    // Inicialización general
    init: function() {
        console.log('🚀 DenunciaApp iniciado');
        
        // Detectar página y ejecutar código específico
        const currentPage = this.getCurrentPage();
        
        // Ejecutar código común
        this.common.init();
        
        // Ejecutar código específico de la página
        switch(currentPage) {
            case 'items':
                this.itemsPage.init();
                break;
            case 'wizard':
                this.wizardPage.init();
                break;
            case 'usuario':
                this.usuarioPage.init();
                break;
            case 'codigo':
                this.codigoPage.init();
                break;
            default:
                console.log('⚠️ No hay código específico para esta página');
        }
    },

    // ===========================================
    // MÓDULO: FUNCIONES COMUNES
    // ===========================================
    common: {
        init: function() {
            console.log('🔧 Inicializando funciones comunes');
            this.setupErrorHandling();
            this.setupCommonAnimations();
        },

        // Obtener CSRF token - MEJORADO
        getCSRFToken: function() {
            // Opción 1: Desde variable global del template
            if (window.CSRF_TOKEN) {
                console.log('✅ CSRF token encontrado desde variable global:', window.CSRF_TOKEN.substring(0, 10) + '...');
                return window.CSRF_TOKEN;
            }

            // Opción 2: Desde input hidden
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfInput && csrfInput.value) {
                console.log('✅ CSRF token encontrado desde input:', csrfInput.value.substring(0, 10) + '...');
                return csrfInput.value;
            }

            // Opción 3: Desde cookie (si está configurado)
            const cookieValue = this.getCookie('csrftoken');
            if (cookieValue) {
                console.log('✅ CSRF token encontrado desde cookie:', cookieValue.substring(0, 10) + '...');
                return cookieValue;
            }

            // Opción 4: Desde meta tag (si está configurado)
            const metaTag = document.querySelector('meta[name=csrf-token]');
            if (metaTag && metaTag.content) {
                console.log('✅ CSRF token encontrado desde meta:', metaTag.content.substring(0, 10) + '...');
                return metaTag.content;
            }

            console.error('❌ No se encontró CSRF token en ningún lugar');
            return '';
        },

        // Función auxiliar para leer cookies
        getCookie: function(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        // Mostrar errores - Función universal
        showError: function(message, container = null) {
            // Remover alertas previas
            $('.alert-danger').remove();
            
            const alert = `<div class="alert alert-danger d-flex justify-content-between align-items-center" role="alert">
                            <span><i class="fas fa-exclamation-circle me-2"></i>${message}</span>
                            <button type="button" class="btn btn-sm btn-outline-red" onclick="DenunciaApp.common.removeAlert(this)">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>`;
            
            // Buscar contenedor específico o usar uno por defecto
            let targetContainer;
            if (container) {
                targetContainer = $(container);
            } else {
                // Buscar contenedores en orden de prioridad
                targetContainer = $('.form-container').first();
                if (targetContainer.length === 0) {
                    targetContainer = $('.container.px-5').first();
                }
                if (targetContainer.length === 0) {
                    targetContainer = $('body');
                }
            }
            
            targetContainer.prepend(alert);
            $('html, body').animate({scrollTop: 0}, 300);
            
            // Auto-remover después de 5 segundos
            setTimeout(() => {
                $('.alert-danger').fadeOut(300, function() {
                    $(this).remove();
                });
            }, 5000);
        },

        // Remover alerta
        removeAlert: function(button) {
            $(button).closest('.alert').fadeOut(300, function() {
                $(this).remove();
            });
        },

        // Mostrar notificación temporal
        showNotification: function(mensaje, tipo = 'success') {
            const bgColor = tipo === 'success' ? '#48bb78' : '#e53e3e';
            
            const notificacion = document.createElement('div');
            notificacion.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${bgColor};
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                font-weight: 600;
                animation: slideIn 0.3s ease-out;
            `;
            notificacion.textContent = mensaje;
            
            // Agregar estilos de animación si no existen
            if (!document.querySelector('#notification-styles')) {
                const style = document.createElement('style');
                style.id = 'notification-styles';
                style.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(notificacion);
            
            setTimeout(() => {
                notificacion.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    if (document.body.contains(notificacion)) {
                        document.body.removeChild(notificacion);
                    }
                }, 300);
            }, 3000);
        },

        // Configurar manejo de errores globales
        setupErrorHandling: function() {
            window.addEventListener('error', function(e) {
                console.error('❌ Error global capturado:', e.error);
            });
        },

        // Animaciones comunes
        setupCommonAnimations: function() {
            // Efecto de entrada para elementos con fadeInUp
            const elementsToAnimate = document.querySelectorAll('.categoria-card, .form-card, .codigo-card');
            elementsToAnimate.forEach((el, index) => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                
                setTimeout(() => {
                    el.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, 100 + (index * 100));
            });
        }
    },

    // ===========================================
    // MÓDULO: PÁGINA DE ITEMS/CATEGORÍAS
    // ===========================================
    itemsPage: {
        init: function() {
            console.log('📋 Inicializando página de items');
            this.setupForm();
            this.setupSelectionEffects();
        },

        setupForm: function() {
            const form = $('#denunciaForm');
            if (form.length === 0) {
                console.log('❌ No se encontró #denunciaForm');
                return;
            }

            console.log('✅ Configurando formulario de items');
            console.log('📍 Action:', form.attr('action'));

            form.submit(function (e) {
                e.preventDefault();
                console.log('📤 Enviando formulario de items...');

                // Validar que se haya seleccionado algo
                if (!$('input[name="denuncia_item"]:checked').length) {
                    DenunciaApp.common.showError('Debe seleccionar el tipo de denuncia');
                    return;
                }

                $.ajax({
                    type: form.attr('method') || 'POST',
                    url: form.attr('action'),
                    data: form.serialize(),
                    beforeSend: function() {
                        console.log('🔄 Enviando datos...');
                    },
                    success: function (response) {
                        console.log('✅ Respuesta recibida:', response);
                        
                        if (response.success) {
                            console.log('✅ Envío exitoso');
                            console.log('🔄 Redirect URL:', response.redirect_url);
                            
                            if (response.redirect_url) {
                                window.location.href = response.redirect_url;
                            } else {
                                console.log('⚠️ No hay redirect_url, usando fallback');
                                window.location.href = '/denuncia/Paso2/'; // URL real del wizard
                            }        
                        } else {
                            console.log('❌ Error en respuesta:', response.message);
                            DenunciaApp.common.showError(response.message || 'Error al procesar la denuncia');
                        }
                    },
                    error: function (xhr, status, error) {
                        console.log('❌ Error AJAX:', error);
                        console.log('📄 Response text:', xhr.responseText);
                        DenunciaApp.common.showError('Error al procesar la denuncia. Por favor intente nuevamente.');
                    },
                });
            });
        },

        setupSelectionEffects: function() {
            document.querySelectorAll('.form-check-input').forEach(radio => {
                radio.addEventListener('change', function() {
                    // Remover selección previa
                    document.querySelectorAll('.form-check-input[name="denuncia_item"]').forEach(r => {
                        r.closest('.form-check-label').classList.remove('selected');
                    });
                    
                    // Agregar selección actual
                    if (this.checked) {
                        this.closest('.form-check-label').classList.add('selected');
                        console.log('✅ Item seleccionado:', this.value);
                    }
                });
            });
        }
    },

    // ===========================================
    // MÓDULO: PÁGINA DEL WIZARD
    // ===========================================
    wizardPage: {
        init: function() {
            console.log('🧙‍♂️ Inicializando wizard');
            
            // Esperar a que jQuery y SmartWizard estén listos
            if (typeof $ === 'undefined') {
                console.log('⏳ Esperando jQuery...');
                setTimeout(() => this.init(), 100);
                return;
            }

            this.setupSmartWizard();
            this.setupTextareaCounter();
            this.initFileUpload();
        },

        setupSmartWizard: function() {
            const wizardElement = $('#smartwizard');
            if (wizardElement.length === 0) {
                console.log('❌ No se encontró #smartwizard');
                return;
            }

            console.log('✅ Configurando SmartWizard');

            wizardElement.smartWizard({
                selected: 0,
                theme: 'default',
                justified: true,
                autoAdjustHeight: true,
                backButtonSupport: false,
                enableUrlHash: false,
                transition: {
                    animation: 'slideHorizontal',
                    speed: '200'
                },
                toolbar: {
                    showNextButton: false,
                    showPreviousButton: false
                }
            });

            this.showStep(0);

            wizardElement.on("leaveStep", (e, anchorObject, currentStepIndex, nextStepIndex, stepDirection) => {
                if (stepDirection === 'forward') {
                    return this.validateStep(currentStepIndex);
                }
                return true;
            });

            wizardElement.on("showStep", (e, anchorObject, stepIndex, stepDirection, stepPosition) => {
                DenunciaApp.vars.currentStep = stepIndex;
                console.log(`📍 Mostrando paso: ${stepIndex + 1}`);
                this.updateNavigation();
                
                if (stepIndex === 3) {
                    setTimeout(() => {
                        this.setupFileUpload();
                    }, 100);
                }
            });
        },

        setupTextareaCounter: function() {
            $('#descripcion-textarea').on('input', function() {
                const texto = $(this).val().trim();
                const caracteres = texto.length;
                
                $('#palabras-count').text(caracteres);
                
                const contador = $('#contador-palabras');
                if (caracteres < 50) {
                    contador.css('color', '#d63384').removeClass('text-success');
                } else {
                    contador.css('color', '#198754').addClass('text-success');
                }
            });
        },

        // Navegación
        nextStep: function() {
            console.log(`➡️ Avanzando desde paso ${DenunciaApp.vars.currentStep + 1}`);
            if (this.validateStep(DenunciaApp.vars.currentStep)) {
                $('#smartwizard').smartWizard("next");
            }
        },

        prevStep: function() {
            console.log(`⬅️ Retrocediendo desde paso ${DenunciaApp.vars.currentStep + 1}`);
            $('#smartwizard').smartWizard("prev");
        },

        showStep: function(step) {
            $('#smartwizard').smartWizard("goToStep", step);
        },

        updateNavigation: function() {
            for (let i = 1; i <= DenunciaApp.vars.totalSteps; i++) {
                const prevBtn = document.getElementById(`btn-prev-${i}`);
                if (prevBtn) {
                    prevBtn.disabled = DenunciaApp.vars.currentStep === 0;
                }
            }
        },

        // Validación por paso
        validateStep: function(stepIndex) {
            let isValid = true;
            let errorMessage = '';

            console.log(`🔍 Validando paso ${stepIndex + 1}`);

            switch(stepIndex) {
                case 0:
                    if (!$('input[name="denuncia_relacion"]:checked').length) {
                        errorMessage = 'Por favor seleccione su relación con la empresa';
                        isValid = false;
                    }
                    break;
                
                case 1:
                    if (!$('select[name="denuncia_tiempo"]').val()) {
                        errorMessage = 'Por favor seleccione hace cuánto tiempo ocurren los hechos';
                        isValid = false;
                    }
                    break;
                
                case 2:
                    const descripcion = $('textarea[name="descripcion"]').val().trim();
                    if (!descripcion) {
                        errorMessage = 'Por favor ingrese una descripción de los hechos';
                        isValid = false;
                    } else if (descripcion.length < 50) {
                        errorMessage = 'La descripción debe tener al menos 50 caracteres';
                        isValid = false;
                    }
                    break;
                
                case 3:
                    isValid = true;
                    break;
            }

            if (!isValid) {
                console.log(`❌ Validación falló: ${errorMessage}`);
                DenunciaApp.common.showError(errorMessage);
            } else {
                console.log('✅ Validación exitosa');
            }

            return isValid;
        },

        // ===========================================
        // SUBMÓDULO: MANEJO DE ARCHIVOS
        // ===========================================
        initFileUpload: function() {
            setTimeout(() => {
                if (DenunciaApp.vars.currentStep === 3) {
                    this.setupFileUpload();
                }
            }, 500);
        },

        setupFileUpload: function() {
            console.log('📎 Configurando upload de archivos');
            
            const uploadArea = document.getElementById('upload-area');
            const fileInput = document.getElementById('file-input');
            const selectBtn = document.getElementById('select-files-btn');

            if (!uploadArea || !fileInput || !selectBtn) {
                console.log('❌ No se encontraron elementos de upload');
                return;
            }

            console.log('✅ Elementos de upload encontrados');

            // Event listeners
            selectBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                fileInput.click();
            };

            uploadArea.onclick = (e) => {
                if (e.target !== selectBtn && !selectBtn.contains(e.target)) {
                    fileInput.click();
                }
            };

            uploadArea.ondragover = (e) => {
                e.preventDefault();
                e.stopPropagation();
                uploadArea.classList.add('drag-over');
            };

            uploadArea.ondragleave = (e) => {
                e.preventDefault();
                e.stopPropagation();
                uploadArea.classList.remove('drag-over');
            };

            uploadArea.ondrop = (e) => {
                e.preventDefault();
                e.stopPropagation();
                uploadArea.classList.remove('drag-over');
                this.handleFiles(e.dataTransfer.files);
            };

            fileInput.onchange = (e) => {
                this.handleFiles(e.target.files);
            };
        },

        handleFiles: function(files) {
            console.log(`📁 Procesando ${files.length} archivos`);
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                
                // Validar tipo
                const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
                if (!DenunciaApp.config.allowedFileTypes.includes(fileExtension)) {
                    DenunciaApp.common.showError('Tipo de archivo no permitido: ' + file.name);
                    continue;
                }

                // Validar tamaño
                if (file.size > DenunciaApp.config.maxFileSize) {
                    DenunciaApp.common.showError('El archivo ' + file.name + ' excede el tamaño máximo permitido (500MB)');
                    continue;
                }

                DenunciaApp.vars.selectedFiles.push(file);
                this.displayFile(file, DenunciaApp.vars.selectedFiles.length - 1);
                console.log(`✅ Archivo agregado: ${file.name}`);
            }
        },

        displayFile: function(file, index) {
            const fileSize = this.formatFileSize(file.size);
            const fileIcon = this.getFileIcon(file.name);

            const fileItem = `
                <div class="file-item" data-index="${index}">
                    <div class="file-info">
                        <span class="file-icon">${fileIcon}</span>
                        <div>
                            <div class="file-name">${file.name}</div>
                            <div class="file-size">${fileSize}</div>
                        </div>
                    </div>
                    <button type="button" class="remove-file" onclick="DenunciaApp.wizardPage.removeFile(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;

            $('.file-list').append(fileItem);
        },

        removeFile: function(index) {
            console.log(`🗑️ Removiendo archivo en índice: ${index}`);
            DenunciaApp.vars.selectedFiles.splice(index, 1);
            $(`.file-item[data-index="${index}"]`).remove();
            
            // Re-indexar
            $('.file-item').each(function(i) {
                $(this).attr('data-index', i);
                $(this).find('.remove-file').attr('onclick', `DenunciaApp.wizardPage.removeFile(${i})`);
            });
        },

        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        getFileIcon: function(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const icons = {
                'pdf': '<i class="fas fa-file-pdf" style="color: #e74c3c;"></i>',
                'doc': '<i class="fas fa-file-word" style="color: #2980b9;"></i>',
                'docx': '<i class="fas fa-file-word" style="color: #2980b9;"></i>',
                'jpg': '<i class="fas fa-file-image" style="color: #27ae60;"></i>',
                'jpeg': '<i class="fas fa-file-image" style="color: #27ae60;"></i>',
                'png': '<i class="fas fa-file-image" style="color: #27ae60;"></i>',
                'gif': '<i class="fas fa-file-image" style="color: #27ae60;"></i>',
                'xlsx': '<i class="fas fa-file-excel" style="color: #16a085;"></i>',
                'xls': '<i class="fas fa-file-excel" style="color: #16a085;"></i>',
                'txt': '<i class="fas fa-file-alt" style="color: #34495e;"></i>'
            };
            return icons[ext] || '<i class="fas fa-file" style="color: #95a5a6;"></i>';
        },

        // Envío final del wizard
        submitDenuncia: function() {
            console.log('📤 Enviando denuncia final...');
            
            const submitBtn = $('#btn-submit');
            submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Procesando...');

            const formData = new FormData();
            formData.append('denuncia_relacion', $('input[name="denuncia_relacion"]:checked').val());
            formData.append('denuncia_tiempo', $('select[name="denuncia_tiempo"]').val());
            formData.append('descripcion', $('textarea[name="descripcion"]').val());
            
            // Obtener y validar CSRF token
            const csrfToken = DenunciaApp.common.getCSRFToken();
            if (!csrfToken) {
                console.error('❌ CSRF token no encontrado');
                DenunciaApp.common.showError('Error de seguridad: Token CSRF no encontrado');
                submitBtn.prop('disabled', false).html('<i class="fas fa-paper-plane me-2"></i>Continuar');
                return;
            }
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // Agregar archivos
            DenunciaApp.vars.selectedFiles.forEach((file, index) => {
                formData.append('archivos[]', file);
            });

            console.log('📊 Datos a enviar:');
            console.log('- Relación:', $('input[name="denuncia_relacion"]:checked').val());
            console.log('- Tiempo:', $('select[name="denuncia_tiempo"]').val());
            console.log('- Descripción chars:', $('textarea[name="descripcion"]').val().length);
            console.log('- Archivos:', DenunciaApp.vars.selectedFiles.length);
            console.log('- CSRF Token:', csrfToken ? 'Presente (' + csrfToken.substring(0, 10) + '...)' : 'FALTA');

            // Obtener URL desde diferentes fuentes (en orden de prioridad)
            let submitUrl;
            
            // 1. Variable global del template (RECOMENDADO)
            if (window.WIZARD_SUBMIT_URL) {
                submitUrl = window.WIZARD_SUBMIT_URL;
                console.log('🎯 URL desde variable global:', submitUrl);
            }
            // 2. Data attribute del smartwizard
            else if ($('#smartwizard').data('submit-url')) {
                submitUrl = $('#smartwizard').data('submit-url');
                console.log('🎯 URL desde data attribute:', submitUrl);
            }
            // 3. Action de formulario padre
            else if ($('#wizard-form').attr('action')) {
                submitUrl = $('#wizard-form').attr('action');
                console.log('🎯 URL desde action del form:', submitUrl);
            }
            // 4. Fallback con URL real del API
            else {
                submitUrl = '/api/post/denuncia/wizzard/';
                console.log('⚠️ Usando URL fallback:', submitUrl);
            }

            $.ajax({
                url: submitUrl,
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    console.log('✅ Respuesta del servidor:', response);
                    
                    if (response.success) {
                        DenunciaApp.common.showNotification('¡Denuncia enviada exitosamente!');
                        setTimeout(() => {
                            if (response.redirect_url) {
                                window.location.href = response.redirect_url;
                            } else {
                                window.location.href = '/denuncia/Paso3/'; // URL real de usuario
                            }
                        }, 1000);
                    } else {
                        console.log('❌ Error en respuesta:', response.message);
                        DenunciaApp.common.showError(response.message || 'Error al procesar la denuncia');
                        submitBtn.prop('disabled', false).html('<i class="fas fa-paper-plane me-2"></i>Continuar');
                    }
                },
                error: function(xhr, status, error) {
                    console.log('❌ Error AJAX:', error);
                    console.log('📄 Response text:', xhr.responseText);
                    DenunciaApp.common.showError('Error al enviar la denuncia. Por favor intente nuevamente.');
                    submitBtn.prop('disabled', false).html('<i class="fas fa-paper-plane me-2"></i>Continuar');
                }
            });
        }
    },

    // ===========================================
    // MÓDULO: PÁGINA DE USUARIO
    // ===========================================
    usuarioPage: {
        init: function() {
            console.log('👤 Inicializando página de usuario');
            this.setupFormValidation();
            this.setupInputFormatting();
            this.setupPrivacySelection();
            this.setupFormSubmission();
            this.setupNavigation();
        },

        setupFormValidation: function() {
            document.querySelectorAll('.form-control').forEach(input => {
                input.addEventListener('focus', function() {
                    if (this.parentElement) {
                        this.parentElement.classList.add('focused');
                    }
                });
                
                input.addEventListener('blur', function() {
                    if (this.parentElement) {
                        this.parentElement.classList.remove('focused');
                    }
                });
            });
        },

        setupInputFormatting: function() {
            // Formateo de RUT
            $('#rut').on('input', function () {
                let valor = $(this).val();
                let limpio = valor.replace(/[^\dkK]/g, '');
                if (limpio.length > 9) limpio = limpio.slice(0, 9);

                let formateado = DenunciaApp.usuarioPage.formatearRUT(limpio);
                $(this).val(formateado);
            });

            // Formateo de celular - CORREGIDO ✅
            $('#celular').on('input', function () {
                console.log('📱 Formateando celular...');
                let val = $(this).val();
                
                // Remover todo lo que no sean números
                val = val.replace(/\D/g, '');
                
                // Limitar a 8 dígitos máximo
                val = val.substring(0, 8);
                
                console.log('📱 Dígitos limpios:', val);
                
                // Formatear como "1234 5678"
                let formatted = '';
                if (val.length > 0) {
                    if (val.length <= 4) {
                        formatted = val;
                    } else {
                        formatted = val.substring(0, 4) + ' ' + val.substring(4, 8);
                    }
                }
                
                console.log('📱 Formato aplicado:', formatted);
                $(this).val(formatted);
            });

            // Validación en tiempo real del celular
            $('#celular').on('blur', function() {
                const val = $(this).val().replace(/\D/g, '');
                if (val.length > 0 && val.length !== 8) {
                    console.log('⚠️ Celular incompleto:', val);
                } else if (val.length === 8) {
                    console.log('✅ Celular válido:', val);
                }
            });
        },

        formatearRUT: function(rut) {
            rut = rut.replace(/[^0-9kK]/g, '').toUpperCase();
            if (rut.length <= 1) return rut;

            let cuerpo = rut.slice(0, -1);
            let dv = rut.slice(-1);
            cuerpo = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
            return `${cuerpo}-${dv}`;
        },

        validarRUT: function(rut) {
            const rutLimpio = rut.replace(/[.-]/g, '');
            
            if (rutLimpio.length < 8 || rutLimpio.length > 9) {
                return false;
            }
            
            const numero = rutLimpio.slice(0, -1);
            const dv = rutLimpio.slice(-1).toUpperCase();
            
            if (!/^\d+$/.test(numero)) {
                return false;
            }
            
            let suma = 0;
            let multiplo = 2;
            
            for (let i = numero.length - 1; i >= 0; i--) {
                suma += parseInt(numero.charAt(i)) * multiplo;
                multiplo = multiplo === 7 ? 2 : multiplo + 1;
            }
            
            const resto = suma % 11;
            const dvCalculado = resto === 0 ? '0' : resto === 1 ? 'K' : (11 - resto).toString();
            
            return dv === dvCalculado;
        },

        setupPrivacySelection: function() {
            const radioButtons = document.querySelectorAll('input[name="tipo_denuncia"]');
            const datosPersonales = document.getElementById('datosPersonales');
            const requiredFields = ['nombre_completo', 'apellidos', 'rut', 'correo_electronico', 'celular'];

            radioButtons.forEach(radio => {
                radio.addEventListener('change', function() {
                    document.querySelectorAll('.privacy-btn').forEach(btn => {
                        btn.classList.remove('selected');
                    });
                    
                    if (this.checked) {
                        this.closest('.privacy-btn').classList.add('selected');
                        console.log(`🔒 Tipo de denuncia seleccionado: ${this.value}`);
                        
                        if (this.value === 'identificado') {
                            datosPersonales.classList.add('show');
                            requiredFields.forEach(fieldId => {
                                const field = document.getElementById(fieldId);
                                if (field) field.required = true;
                            });
                        } else {
                            datosPersonales.classList.remove('show');
                            requiredFields.forEach(fieldId => {
                                const field = document.getElementById(fieldId);
                                if (field) {
                                    field.required = false;
                                    field.value = '';
                                }
                            });
                        }
                    }
                });
            });
        },

        setupFormSubmission: function() {
            const form = document.getElementById('usuarioForm');
            const btnEnviar = document.getElementById('btnEnviar');
            
            if (!form) {
                console.log('❌ No se encontró #usuarioForm');
                return;
            }

            console.log('✅ Configurando formulario de usuario');
            console.log('📍 Action:', form.action);

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                console.log('📤 Enviando formulario de usuario...');

                const tipoSeleccionado = document.querySelector('input[name="tipo_denuncia"]:checked');
                if (!tipoSeleccionado) {
                    DenunciaApp.common.showError('Por favor, seleccione el tipo de denuncia');
                    return;
                }

                console.log(`🔒 Tipo seleccionado: ${tipoSeleccionado.value}`);

                if (tipoSeleccionado.value === 'identificado') {
                    if (!this.validateIdentifiedForm()) {
                        return;
                    }
                }

                const originalText = btnEnviar.innerHTML;
                btnEnviar.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
                btnEnviar.disabled = true;

                // Preparar datos del formulario con formato correcto ✅
                const formData = new FormData(form);
                
                // Corregir formato del celular si está presente
                const celularInput = document.getElementById('celular');
                if (celularInput && celularInput.value) {
                    const celularLimpio = celularInput.value.replace(/\D/g, ''); // Solo números
                    const celularFormateado = `+569${celularLimpio}`; // Formato: +56912345678
                    formData.set('celular', celularFormateado);
                    console.log('📱 Celular formateado:', celularFormateado);
                }

                $.ajax({
                    type: 'POST',
                    url: form.action,
                    data: formData,
                    processData: false,
                    contentType: false,
                    beforeSend: function() {
                        console.log('🔄 Enviando datos de usuario...');
                    },
                    success: function(response) {
                        console.log('✅ Respuesta recibida:', response);
                        
                        if (response.success) {
                            btnEnviar.innerHTML = '<i class="fas fa-check me-2"></i>¡Enviado!';
                            
                            setTimeout(() => {
                                if (response.redirect_url) {
                                    console.log('🔄 Redirigiendo a:', response.redirect_url);
                                    window.location.href = response.redirect_url;
                                } else {
                                    console.log('⚠️ No hay redirect_url, usando fallback');
                                    window.location.href = '/denuncia/final/'; // URL real del código
                                }
                            }, 1000);
                        } else {
                            console.log('❌ Error en respuesta:', response.message);
                            DenunciaApp.common.showError(response.message || 'Error al procesar los datos');
                            btnEnviar.innerHTML = originalText;
                            btnEnviar.disabled = false;
                        }
                    },
                    error: function(xhr, status, error) {
                        console.log('❌ Error AJAX:', error);
                        console.log('📄 Response text:', xhr.responseText);
                        DenunciaApp.common.showError('Error al enviar los datos. Por favor, inténtelo nuevamente.');
                        btnEnviar.innerHTML = originalText;
                        btnEnviar.disabled = false;
                    }
                });
            });
        },

        validateIdentifiedForm: function() {
            const fields = {
                nombre_completo: {
                    element: document.getElementById('nombre_completo'),
                    regex: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
                    errorMsg: 'El nombre solo puede contener letras y espacios'
                },
                apellidos: {
                    element: document.getElementById('apellidos'),
                    regex: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
                    errorMsg: 'Los apellidos solo pueden contener letras y espacios'
                },
                correo_electronico: {
                    element: document.getElementById('correo_electronico'),
                    regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    errorMsg: 'Por favor, ingrese un correo electrónico válido'
                },
                celular: {
                    element: document.getElementById('celular'),
                    // CORREGIDO: Solo validar 8 dígitos con espacio opcional ✅
                    regex: /^\d{4}\s?\d{4}$/,
                    errorMsg: 'Por favor, ingrese un número de celular válido (8 dígitos)'
                }
            };

            // Validación especial para RUT
            const rutElement = document.getElementById('rut');
            if (rutElement) {
                const rutValue = rutElement.value.trim();
                if (!rutValue) {
                    DenunciaApp.common.showError('Por favor, ingrese su RUT');
                    rutElement.focus();
                    return false;
                }
                
                if (!this.validarRUT(rutValue)) {
                    DenunciaApp.common.showError('Por favor, ingrese un RUT válido');
                    rutElement.focus();
                    return false;
                }
            }

            for (const [fieldName, config] of Object.entries(fields)) {
                const element = config.element;
                if (!element) continue;

                const value = element.value.trim();
                
                if (!value) {
                    DenunciaApp.common.showError(`Por favor, ingrese ${fieldName.replace('_', ' ')}`);
                    element.focus();
                    return false;
                }

                if (config.regex && !config.regex.test(value)) {
                    DenunciaApp.common.showError(config.errorMsg);
                    element.focus();
                    return false;
                }
            }

            console.log('✅ Validación de formulario identificado exitosa');
            return true;
        },

        setupNavigation: function() {
            const btnAtras = document.getElementById('btnAtras');
            if (btnAtras) {
                btnAtras.addEventListener('click', function() {
                    console.log('⬅️ Navegando hacia atrás');
                    window.history.back();
                });
            }
        }
    },

    // ===========================================
    // MÓDULO: PÁGINA DE CÓDIGO
    // ===========================================
    codigoPage: {
        init: function() {
            console.log('🎫 Inicializando página de código');
            this.setupCopyFunction();
            this.setupAnimations();
            this.setupSessionClearance();
        },

        setupCopyFunction: function() {
            // Función global para copiar código
            window.copiarCodigo = () => {
                console.log('📋 Copiando código...');
                
                const codigo = document.getElementById('codigo-texto').textContent.trim();
                const copyButton = document.querySelector('.copy-button');
                const copyText = document.getElementById('copy-text');
                
                const tempInput = document.createElement('input');
                tempInput.value = codigo;
                document.body.appendChild(tempInput);
                tempInput.select();
                tempInput.setSelectionRange(0, 99999);
                
                try {
                    document.execCommand('copy');
                    
                    copyButton.classList.add('copied');
                    copyText.innerHTML = '<i class="fas fa-check"></i> ¡Copiado!';
                    
                    DenunciaApp.common.showNotification('Código copiado al portapapeles', 'success');
                    console.log('✅ Código copiado exitosamente');
                    
                    setTimeout(() => {
                        copyButton.classList.remove('copied');
                        copyText.innerHTML = '<i class="fas fa-copy"></i> Copiar Código';
                    }, 3000);
                    
                } catch (err) {
                    console.error('❌ Error al copiar:', err);
                    DenunciaApp.common.showNotification('Error al copiar código', 'error');
                }
                
                document.body.removeChild(tempInput);
            };
        },

        setupAnimations: function() {
            const card = document.querySelector('.codigo-card');
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                
                setTimeout(() => {
                    card.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 100);
            }
        },

        setupSessionClearance: function() {
            // Prevenir navegación hacia atrás sin advertencia
            window.addEventListener('beforeunload', function(e) {
                e.preventDefault();
                e.returnValue = '¿Está seguro? Se perderá el código de denuncia.';
            });

            // Limpiar sesión después de 30 segundos
            setTimeout(() => {
                if (typeof fetch !== 'undefined') {
                    fetch('/clear-session/', {method: 'POST'})
                        .then(() => console.log('🗑️ Sesión limpiada automáticamente'))
                        .catch(() => console.log('⚠️ No se pudo limpiar la sesión automáticamente'));
                }
            }, 30000);
        }
    }
};

// ===========================================
// FUNCIONES GLOBALES PARA COMPATIBILIDAD
// ===========================================

// Funciones del wizard que se llaman desde HTML
function nextStep() {
    DenunciaApp.wizardPage.nextStep();
}

function prevStep() {
    DenunciaApp.wizardPage.prevStep();
}

function submitDenuncia() {
    DenunciaApp.wizardPage.submitDenuncia();
}

// ===========================================
// INICIALIZACIÓN AUTOMÁTICA
// ===========================================

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔥 DOM listo - Iniciando DenunciaApp...');
    DenunciaApp.init();
});

// Inicializar también cuando jQuery esté listo (por compatibilidad)
$(document).ready(function() {
    console.log('🟢 jQuery listo');
    // La inicialización ya se hizo en DOMContentLoaded
});

// Exportar para uso global
window.DenunciaApp = DenunciaApp;