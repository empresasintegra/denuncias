/**
 * APLICACIÓN DE DENUNCIAS - JAVASCRIPT CON VALIDACIÓN DE RUT
 * Autor: Sistema de Denuncias Integra
 * Versión: 1.5 - Agregada validación de RUT en tiempo real
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
        selectedFiles: [],
        expandedCategories: new Set() // Tracking de categorías expandidas
    },

    // Detección de página actual - MEJORADA
    getCurrentPage: function() {
        
        // Detectar por elementos únicos en el DOM
        if (document.getElementById('codigo-texto')) {
           
            return 'codigo';
        }
        
        if (document.getElementById('smartwizard')) {
           
            return 'wizard';
        }
        
        if (document.getElementById('usuarioForm')) {
           
            return 'usuario';
        }
        
        if (document.getElementById('denunciaForm')) {
            
            return 'items';
        }

       

        return 'unknown';
    },

    // Inicialización general
    init: function() {
      
        
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
               
        }
    },

    // ===========================================
    // MÓDULO: FUNCIONES COMUNES
    // ===========================================
    common: {
        init: function() {
            
            this.setupErrorHandling();
            this.setupCommonAnimations();
        },

        // Obtener CSRF token - MEJORADO
        getCSRFToken: function() {
            // Opción 1: Desde variable global del template
            if (window.CSRF_TOKEN) {
               
                return window.CSRF_TOKEN;
            }

            // Opción 2: Desde input hidden
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfInput && csrfInput.value) {
                
                return csrfInput.value;
            }

            // Opción 3: Desde cookie (si está configurado)
            const cookieValue = this.getCookie('csrftoken');
            if (cookieValue) {
               
                return cookieValue;
            }

            // Opción 4: Desde meta tag (si está configurado)
            const metaTag = document.querySelector('meta[name=csrf-token]');
            if (metaTag && metaTag.content) {
               
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

        // ⭐ FUNCIÓN SIMPLE: Insertar error DENTRO de .tab-content como primer hijo + scroll arriba
        showError: function(message, container = null) {
           
            
            // Remover alertas previas
            $('.alert-danger, .emergency-alert').remove();
            
            const alert = `<div class="alert alert-danger alert-dismissible mb-3" role="alert" style="margin: 15px 0; z-index: 1000; background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; border-radius: 0.375rem; padding: 0.75rem 1rem;">
                            <div class="d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-exclamation-circle me-2"></i>${message}</span>
                                <button type="button" class="btn btn-sm ms-2" onclick="DenunciaApp.common.removeAlert(this)" style="border: none; background: none; color: inherit; font-size: 1.2em; padding: 0;">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>`;
            
            // ⭐ ESTRATEGIA SIMPLE: Buscar .tab-content e insertar DENTRO como primer hijo
            const tabContent = document.querySelector('.tab-content');
            if (tabContent) {
               
                $(tabContent).prepend(alert);
               
                
                // ⭐ SCROLL SIMPLE: Ir hasta arriba
                setTimeout(() => {
                    $('html, body').animate({scrollTop: 0}, 600);
                    
                }, 100);
                
            } else {
                // Fallback simple
               
                if (container) {
                    $(container).prepend(alert);
                } else {
                    $('body').prepend(`<div class="emergency-alert" style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; background: #dc3545; color: white; padding: 12px 20px; border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-weight: 500;"><i class="fas fa-exclamation-triangle me-2"></i>${message}</div>`);
                }
                // Scroll hacia arriba también en fallbacks
                $('html, body').animate({scrollTop: 0}, 600);
            }
            
            // Auto-remover después de 8 segundos
            setTimeout(() => {
                $('.alert-danger, .emergency-alert').fadeOut(300, function() {
                    $(this).remove();
                });
            }, 8000);
            
            
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
    // MÓDULO: PÁGINA DE ITEMS/CATEGORÍAS CON COLLAPSE (sin cambios)
    // ===========================================
    itemsPage: {
        init: function() {
            
            this.setupForm();
            this.setupSelectionEffects();
            this.setupCollapseSystem();
            this.initAccessibility();
        },

        setupForm: function() {
            const form = $('#denunciaForm');
            if (form.length === 0) {
                
                return;
            }


            form.submit(function (e) {
                e.preventDefault();
                
                // Validar que se haya seleccionado algo
                if (!$('input[name="denuncia_item"]:checked').length) {
                    DenunciaApp.common.showError('Debe seleccionar el tipo de denuncia');
                    return;
                }

                $.ajax({
                    type: form.attr('method') || 'POST',
                    url: form.attr('action'),
                    data: form.serialize(),

                    success: function (response) {
                        
                        
                        if (response.success) {
                           
                            
                            if (response.redirect_url) {
                                window.location.href = response.redirect_url;
                            } else {
                               
                                window.location.href = '/denuncia/Paso2/';
                            }        
                        } else {
                            
                            DenunciaApp.common.showError(response.message || 'Error al procesar la denuncia');
                        }
                    },
                    error: function (xhr, status, error) {
                        
                        DenunciaApp.common.showError('Error al procesar la denuncia. Por favor intente nuevamente.');
                    },
                });
            });
        },

        // ... resto de funciones del itemsPage se mantienen igual ...
       setupSelectionEffects: function() {
            document.querySelectorAll('.form-check-input').forEach(radio => {
                radio.addEventListener('change', function() {
                    // Remover selección previa de todas las categorías
                    document.querySelectorAll('.categoria-card').forEach(card => {
                        card.classList.remove('has-selection');
                    });
                    
                    // Remover selección previa de todos los radio buttons
                    document.querySelectorAll('.form-check-input[name="denuncia_item"]').forEach(r => {
                        r.closest('.form-check-label').classList.remove('selected');
                    });
                    
                    // Agregar selección actual
                    if (this.checked) {
                        this.closest('.form-check-label').classList.add('selected');
                        
                        // Marcar la categoría como seleccionada
                        const categoriaCard = this.closest('.categoria-card');
                        if (categoriaCard) {
                            categoriaCard.classList.add('has-selection');
                        }
                        
                       
                    }
                });
            });
        },

        // ===========================================
        // SISTEMA DE COLLAPSE
        // ===========================================
        setupCollapseSystem: function() {
            
            
            // Inicializar todas las categorías como colapsadas
            document.querySelectorAll('.categoria-card').forEach(card => {
                this.collapseCategory(card, false); // Sin animación inicial
            });

            // Configurar eventos de teclado para accesibilidad
            document.querySelectorAll('.categoria-header').forEach(header => {
                header.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const categoriaId = header.closest('.categoria-card').dataset.categoriaId;
                        this.toggleCategoria(parseInt(categoriaId));
                    }
                });
            });
        },

        toggleCategoria: function(categoriaId) {
            
            const card = document.querySelector(`[data-categoria-id="${categoriaId}"]`);
            if (!card) {
                console.error(`❌ No se encontró categoría con ID: ${categoriaId}`);
                return;
            }

            const isExpanded = DenunciaApp.vars.expandedCategories.has(categoriaId);
            
            if (isExpanded) {
                this.collapseCategory(card);
                DenunciaApp.vars.expandedCategories.delete(categoriaId);
               
            } else {
                this.expandCategory(card);
                DenunciaApp.vars.expandedCategories.add(categoriaId);
               
            }

            // Actualizar atributos de accesibilidad
            this.updateAccessibilityAttributes(card, !isExpanded);
        },

        expandCategory: function(card, withAnimation = true) {
            const content = card.querySelector('.categoria-content');
            const toggle = card.querySelector('.categoria-toggle');
            const icon = toggle.querySelector('i');

            // Aplicar clases CSS
            card.classList.remove('collapsed');
            card.classList.add('expanded');
            toggle.classList.add('expanded');
            
            if (withAnimation) {
                // Animar la expansión
                content.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            } else {
                content.style.transition = 'none';
            }
            
            content.classList.add('expanded');
            
            // Cambiar icono
            icon.className = 'fas fa-chevron-up';

            // Scroll suave hacia la categoría expandida
            if (withAnimation) {
                setTimeout(() => {
                    card.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'nearest' 
                    });
                }, 200);
            }
        },

        collapseCategory: function(card, withAnimation = true) {
            const content = card.querySelector('.categoria-content');
            const toggle = card.querySelector('.categoria-toggle');
            const icon = toggle.querySelector('i');

            // Aplicar clases CSS
            card.classList.remove('expanded');
            card.classList.add('collapsed');
            toggle.classList.remove('expanded');
            
            if (withAnimation) {
                content.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            } else {
                content.style.transition = 'none';
            }
            
            content.classList.remove('expanded');
            
            // Cambiar icono
            icon.className = 'fas fa-chevron-down';
        },

        updateToggleButtons: function() {
            const totalCategories = document.querySelectorAll('.categoria-card').length;
            const expandedCount = DenunciaApp.vars.expandedCategories.size;
            
            const expandBtn = document.querySelector('.toggle-all-btn:not(.collapse-all)');
            const collapseBtn = document.querySelector('.toggle-all-btn.collapse-all');
            
            if (expandedCount === 0) {
                // Todas colapsadas
                if (expandBtn) {
                    expandBtn.innerHTML = '<i class="fas fa-expand-arrows-alt"></i> Expandir Todo';
                    expandBtn.disabled = false;
                }
                if (collapseBtn) {
                    collapseBtn.disabled = true;
                }
            } else if (expandedCount === totalCategories) {
                // Todas expandidas
                if (expandBtn) {
                    expandBtn.disabled = true;
                }
                if (collapseBtn) {
                    collapseBtn.innerHTML = '<i class="fas fa-compress-arrows-alt"></i> Contraer Todo';
                    collapseBtn.disabled = false;
                }
            } else {
                // Estado mixto
                if (expandBtn) {
                    expandBtn.innerHTML = `<i class="fas fa-expand-arrows-alt"></i> Expandir Restantes (${totalCategories - expandedCount})`;
                    expandBtn.disabled = false;
                }
                if (collapseBtn) {
                    collapseBtn.innerHTML = `<i class="fas fa-compress-arrows-alt"></i> Contraer Expandidas (${expandedCount})`;
                    collapseBtn.disabled = false;
                }
            }
        },

        // ===========================================
        // ACCESIBILIDAD
        // ===========================================
        initAccessibility: function() {
            
            
            // Agregar atributos ARIA
            document.querySelectorAll('.categoria-header').forEach(header => {
                header.setAttribute('role', 'button');
                header.setAttribute('tabindex', '0');
                header.setAttribute('aria-label', 'Expandir/contraer categoría');
            });

            document.querySelectorAll('.categoria-content').forEach(content => {
                content.setAttribute('role', 'region');
                content.setAttribute('aria-hidden', 'true');
            });

            // Configurar navegación por teclado
            document.addEventListener('keydown', (e) => {
                if (e.target.classList.contains('categoria-header')) {
                    switch(e.key) {
                        case 'ArrowDown':
                            e.preventDefault();
                            this.focusNextCategory(e.target);
                            break;
                        case 'ArrowUp':
                            e.preventDefault();
                            this.focusPrevCategory(e.target);
                            break;
                    }
                }
            });
        },

        updateAccessibilityAttributes: function(card, isExpanded) {
            const header = card.querySelector('.categoria-header');
            const content = card.querySelector('.categoria-content');
            
            header.setAttribute('aria-expanded', isExpanded.toString());
            content.setAttribute('aria-hidden', (!isExpanded).toString());
        },

        focusNextCategory: function(currentHeader) {
            const headers = Array.from(document.querySelectorAll('.categoria-header'));
            const currentIndex = headers.indexOf(currentHeader);
            const nextIndex = (currentIndex + 1) % headers.length;
            headers[nextIndex].focus();
        },

        focusPrevCategory: function(currentHeader) {
            const headers = Array.from(document.querySelectorAll('.categoria-header'));
            const currentIndex = headers.indexOf(currentHeader);
            const prevIndex = currentIndex === 0 ? headers.length - 1 : currentIndex - 1;
            headers[prevIndex].focus();
        }
    },
       

    // ===========================================
    // MÓDULO: PÁGINA DEL WIZARD (sin cambios)
    // ===========================================
    wizardPage: {
        init: function() {
            
            
            // Esperar a que jQuery y SmartWizard estén listos
            if (typeof $ === 'undefined') {
                
                setTimeout(() => this.init(), 100);
                return;
            }

            this.setupSmartWizard();
            this.setupTextareaCounter();
            this.initFileUpload();
            this.setupRelacionEmpresaHandler();
        },

        setupRelacionEmpresaHandler: function() {
            
            
            // Detectar cambios en los radio buttons de relación empresa
            $('input[name="denuncia_relacion"]').on('change', function() {
                const rol = $(this).data('rol');
                const otroContainer = $('#otro-descripcion-container');
                const otroInput = $('#descripcion_relacion');
                
              
                
                if (rol && rol.toLowerCase() === 'otro') {
                    // Mostrar campo con animación
                    otroContainer.slideDown(300);
                    otroInput.prop('required', true);
                  
                } else {
                    // Ocultar campo y limpiar valor
                    otroContainer.slideUp(300);
                    otroInput.prop('required', false).val('');
                   
                }
            });
            
            // Verificar si ya hay una selección al cargar
            const selectedRadio = $('input[name="denuncia_relacion"]:checked');
            if (selectedRadio.length > 0) {
                selectedRadio.trigger('change');
            }
        },

        setupSmartWizard: function() {
            const wizardElement = $('#smartwizard');
            if (wizardElement.length === 0) {
               
                return;
            }

           

            wizardElement.smartWizard({
                selected: 0,                    // Paso inicial 
                theme: 'default',               // Tema
                justified: true,                // Justificación del menú
                autoAdjustHeight: true,         // Ajustar altura automáticamente
                enableURLhash: true,           // Hash en URL
                transition: {
                    animation: 'slideHorizontal', // 'none'|'fade'|'slideHorizontal'|'slideVertical'|'slideSwing'|'css'
                    speed: '200',                // Velocidad
                    easing: ''                   // Easing (requiere plugin jQuery)
                },
               toolbarSettings: {
                    toolbarPosition: 'bottom',
                    toolbarButtonPosition: 'right',
                    showNextButton: false,
                    showPreviousButton: false,
                    toolbarExtraButtons: [] // Sin botones extra
                }
            });


            this.showStep(0);

            wizardElement.on("leaveStep", (e, anchorObject, currentStepIndex, nextStepIndex, stepDirection) => {
                if (stepDirection === 'forward') {
                    return this.validateStep(currentStepIndex);
                }
                return true;
            });


    $('.sw-toolbar').hide(); // Oculta toda la toolbar
        // O específicamente:
    $('.sw-btn-prev, .sw-btn-next').hide(); // Oculta solo esos botones
            // ⭐ USANDO EL EVENTO CORRECTO CON PARÁMETROS REALES
    wizardElement.on("showStep", function(e, anchorObject, stepIndex, stepDirection, stepPosition) {
    DenunciaApp.vars.currentStep = stepIndex;
    this.updateNavigation();
    
    // ⭐ LIMPIAR ERRORES PREVIOS
    $('.alert-danger').fadeOut(300, function() {
        $(this).remove();
    });
    
    // ⭐⭐ AUTO-SCROLL CON TIMING CORRECTO ⭐⭐
    setTimeout(() => {
        // Método 1: jQuery (más compatible)
        $('html, body').stop(true, true).animate({
            scrollTop: 0
        }, 100);
        
        // Método 2: JavaScript nativo (más moderno)
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        
        }, 25); // Esperar 300ms para que termine la animación slideHorizontal
        
        if (stepIndex === 3) {
            setTimeout(() => {
                this.setupFileUpload();
            }, 50);
         }
        }.bind(this)); // ⭐ IMPORTANTE: bind(this) para mantener el contexto
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
            
            if (this.validateStep(DenunciaApp.vars.currentStep)) {
                $('#smartwizard').smartWizard("next");
                
                // ⭐ AUTO-SCROLL DESPUÉS DE CAMBIAR PASO
            }
        },

        prevStep: function() {
           
            $('#smartwizard').smartWizard("prev");
            
            // ⭐ AUTO-SCROLL DESPUÉS DE CAMBIAR PASO
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

        // ⭐ FUNCIÓN MEJORADA: Validación por paso con mejor manejo de errores
        validateStep: function(stepIndex) {
            let isValid = true;
            let errorMessage = '';

            

            switch(stepIndex) {
                case 0:
                    // Validar selección de relación
                    const relacionSeleccionada = $('input[name="denuncia_relacion"]:checked');
                    if (!relacionSeleccionada.length) {
                        errorMessage = 'Por favor seleccione su relación con la empresa';
                        isValid = false;
                    } else {
                        // Si seleccionó "Otro", validar el campo de descripción
                        const rol = relacionSeleccionada.data('rol');
                        if (rol && rol.toLowerCase() === 'otro') {
                            const descripcionOtro = $('#descripcion_relacion').val().trim();
                            if (!descripcionOtro) {
                                errorMessage = 'Por favor especifique su relación con la empresa';
                                isValid = false;
                            } else if (descripcionOtro.length < 3) {
                                errorMessage = 'La descripción debe tener al menos 3 caracteres';
                                isValid = false;
                            }
                        }
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
                
                // ⭐ MEJORADO: Usar la función de error mejorada que detecta el paso activo
                DenunciaApp.common.showError(errorMessage);
            }

            return isValid;
        },

        // Archivo upload y demás funciones del wizard
        initFileUpload: function() {
            setTimeout(() => {
                if (DenunciaApp.vars.currentStep === 3) {
                    this.setupFileUpload();
                }
            }, 500);
        },

        setupFileUpload: function() {
            
            const uploadArea = document.getElementById('upload-area');
            const fileInput = document.getElementById('file-input');
            const selectBtn = document.getElementById('select-files-btn');

            if (!uploadArea || !fileInput || !selectBtn) {
                return;
            }


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

                if ($('.file-item').length <5){
                    DenunciaApp.vars.selectedFiles.push(file);
                    this.displayFile(file, DenunciaApp.vars.selectedFiles.length - 1);
                }
                else{
                    DenunciaApp.common.showError('No se puede ingresar mas archivos');
                    continue;
                }
                
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
            
            const submitBtn = $('#btn-submit');
            submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Procesando...');

            const formData = new FormData();
            
            // Datos básicos
            formData.append('denuncia_relacion', $('input[name="denuncia_relacion"]:checked').val());
            formData.append('denuncia_tiempo', $('select[name="denuncia_tiempo"]').val());
            formData.append('descripcion', $('textarea[name="descripcion"]').val());
            
            const relacionSeleccionada = $('input[name="denuncia_relacion"]:checked');
            const rol = relacionSeleccionada.data('rol');
            if (rol && rol.toLowerCase() === 'otro') {
                const descripcionRelacion = $('#descripcion_relacion').val().trim();
                formData.append('descripcion_relacion', descripcionRelacion);
            }
            
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

           
            // Obtener URL desde diferentes fuentes
            let submitUrl;
            
            if (window.WIZARD_SUBMIT_URL) {
                submitUrl = window.WIZARD_SUBMIT_URL;
               
            } else if ($('#smartwizard').data('submit-url')) {
                submitUrl = $('#smartwizard').data('submit-url');
              
            } else if ($('#wizard-form').attr('action')) {
                submitUrl = $('#wizard-form').attr('action');
              
            } else {
                submitUrl = '/api/post/denuncia/wizzard/';
               
            }

            $.ajax({
                url: submitUrl,
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                  
                    
                    if (response.success) {
                        DenunciaApp.common.showNotification('¡Denuncia enviada exitosamente!');
                        setTimeout(() => {
                            if (response.redirect_url) {
                                window.location.href = response.redirect_url;
                            } else {
                                window.location.href = '/denuncia/Paso3/';
                            }
                        }, 1000);
                    } else {
                       
                        DenunciaApp.common.showError(response.message || 'Error al procesar la denuncia');
                        submitBtn.prop('disabled', false).html('<i class="fas fa-paper-plane me-2"></i>Continuar');
                    }
                },
                error: function(xhr, status, error) {
                     
                    DenunciaApp.common.showError('Error al enviar la denuncia. Por favor intente nuevamente.');
                    submitBtn.prop('disabled', false).html('<i class="fas fa-paper-plane me-2"></i>Continuar');
                }
            });
        }
    },
    // ===========================================
    // MÓDULO: PÁGINA DE USUARIO ⭐ ACTUALIZADA CON VALIDACIÓN DE RUT
    // ===========================================
    usuarioPage: {
        // Variables para debounce y control de validación
        rutValidationTimeout: null,
        rutValidationRequest: null,
        
        init: function() {
           
            this.setupFormValidation();
            this.setupInputFormatting();
            this.setupPrivacySelection();
            this.setupFormSubmission();
            this.setupNavigation();
            this.setupRutValidation(); // ⭐ NUEVA FUNCIÓN
        },

        // =================================================================
        // 🆕 VALIDACIÓN DE RUT EN TIEMPO REAL
        // =================================================================
        setupRutValidation: function() {
            
            
            const rutInput = $('#rut');
            const rutContainer = rutInput.closest('.form-group');
            
            if (!rutInput.length) {
                
                return;
            }

            // ✅ EVENTO PRINCIPAL: Validar cuando el usuario termine de escribir
            rutInput.on('input', (e) => {
                const rutValue = $(e.target).val().trim();
                
                // Limpiar timeout anterior
                if (this.rutValidationTimeout) {
                    clearTimeout(this.rutValidationTimeout);
                }
                
                // Cancelar request anterior si existe
                if (this.rutValidationRequest) {
                    this.rutValidationRequest.abort();
                }
                
                // Limpiar estado visual previo
                this.clearRutValidationState(rutContainer);
                
                // Solo validar si el RUT parece completo (al menos 8 caracteres)
                if (rutValue.length >= 8) {
                    
                    
                    // ⭐ DEBOUNCE: Esperar 2 segundos antes de validar
                    this.rutValidationTimeout = setTimeout(() => {
                        this.validateRutRealTime(rutValue, rutContainer);
                    }, 2000);
                    
                    // Mostrar indicador de "escribiendo..."
                    this.showRutValidationState(rutContainer, 'typing', 'Termine de escribir para validar...');
                }
            });

            // ✅ EVENTO BLUR: Validar inmediatamente cuando pierda el foco
            rutInput.on('blur', (e) => {
                const rutValue = $(e.target).val().trim();
                
                if (rutValue.length >= 8) {
                    // Cancelar timeout si existe
                    if (this.rutValidationTimeout) {
                        clearTimeout(this.rutValidationTimeout);
                    }
                    
                   
                    this.validateRutRealTime(rutValue, rutContainer);
                }
            });
        },

        // ✅ FUNCIÓN PRINCIPAL DE VALIDACIÓN
        validateRutRealTime: function(rut, container) {
            
            
            // Mostrar estado de carga
            this.showRutValidationState(container, 'loading', 'Validando RUT...');
            
            // ⭐ LLAMADA AJAX CON TIMEOUT DE 2 SEGUNDOS
            this.rutValidationRequest = $.ajax({
                url: window.VALIDATE_RUT_URL || '/api/validate/rut/',
                method: 'POST',
                data: {
                    rut: rut,
                    csrfmiddlewaretoken: DenunciaApp.common.getCSRFToken()
                },
                timeout: 2000, // ⭐ TIMEOUT DE 2 SEGUNDOS
                
                success: (response) => {
                   
                    this.handleRutValidationResponse(response, container);
                },
                
                error: (xhr, status, error) => {
                    
                    this.handleRutValidationError(xhr, status, error, container);
                },
                
                complete: () => {
                    this.rutValidationRequest = null;
                }
            });
        },

        // ✅ MANEJAR RESPUESTA EXITOSA
        handleRutValidationResponse: function(response, container) {
            if (response.success) {
                if (response.valid) {
                    if (response.exists) {
                        // ⚠️ RUT EXISTE - Mostrar información del usuario
                      
                        this.showRutValidationState(
                            container, 
                            'exists', 
                            `${response.message}. ${response.suggestion || ''}`
                        );
                        
                        // ✅ AUTOCOMPLETAR DATOS SI ESTÁN DISPONIBLES
                        if (response.user_info && !response.user_info.es_anonimo) {
                            this.showAutoCompleteOption(response.user_info);
                        }
                        
                    } else {
                        // ✅ RUT VÁLIDO Y DISPONIBLE
                        this.showRutValidationState(
                            container, 
                            'valid', 
                            response.message
                        );
                    }
                } else {
                    // ❌ RUT INVÁLIDO
                   
                    this.showRutValidationState(
                        container, 
                        'invalid', 
                        response.message
                    );
                }
            } else {
                // Error en la respuesta
                this.showRutValidationState(
                    container, 
                    'error', 
                    response.message || 'Error al validar RUT'
                );
            }
        },

        // ✅ MANEJAR ERRORES DE RED/TIMEOUT
        handleRutValidationError: function(xhr, status, error, container) {
            let errorMessage = 'Error al validar RUT';
            
            if (status === 'timeout') {
                errorMessage = 'Tiempo de espera agotado. Intente nuevamente.';
            
            } else if (status === 'abort') {
              
                return; // No mostrar error si fue cancelada
            } else {
               
                errorMessage = 'Error de conexión. Verifique su internet.';
            }
            
            this.showRutValidationState(container, 'error', errorMessage);
        },

        // ✅ MOSTRAR ESTADO VISUAL DE VALIDACIÓN
        showRutValidationState: function(container, state, message) {
            // Remover estados previos
            this.clearRutValidationState(container);
            
            const rutInput = container.find('#rut');
            const feedbackElement = this.createRutFeedbackElement(state, message);
            
            // Agregar nuevo estado
            container.addClass(`rut-validation-${state}`);
            rutInput.addClass(`validation-${state}`);
            
            // Insertar mensaje de feedback
            container.append(feedbackElement);
            
           
        },

        // ✅ LIMPIAR ESTADO VISUAL
        clearRutValidationState: function(container) {
            // Remover clases de estado
            const states = ['typing', 'loading', 'valid', 'invalid', 'exists', 'error'];
            states.forEach(state => {
                container.removeClass(`rut-validation-${state}`);
                container.find('#rut').removeClass(`validation-${state}`);
            });
            
            // Remover elementos de feedback
            container.find('.rut-validation-feedback').remove();
            container.find('.autocomplete-option').remove();
        },

        // ✅ CREAR ELEMENTO DE FEEDBACK VISUAL
        createRutFeedbackElement: function(state, message) {
            const icons = {
                typing: '<i class="fas fa-keyboard text-muted"></i>',
                loading: '<i class="fas fa-spinner fa-spin text-primary"></i>',
                valid: '<i class="fas fa-check-circle text-success"></i>',
                invalid: '<i class="fas fa-times-circle text-danger"></i>',
                exists: '<i class="fas fa-user-check text-warning"></i>',
                error: '<i class="fas fa-exclamation-triangle text-danger"></i>'
            };

            const colors = {
                typing: '#6c757d',
                loading: '#007bff',
                valid: '#28a745',
                invalid: '#dc3545',
                exists: '#ffc107',
                error: '#dc3545'
            };

            return $(`
                <div class="rut-validation-feedback mt-2 d-flex align-items-center" style="color: ${colors[state]}; font-size: 0.9rem;">
                    ${icons[state]}
                    <span class="ms-2">${message}</span>
                </div>
            `);
        },

        // ✅ MOSTRAR OPCIÓN DE AUTOCOMPLETADO
        showAutoCompleteOption: function(userInfo) {
            const rutContainer = $('#rut').closest('.form-group');
            
            const autoCompleteElement = $(`
                <div class="autocomplete-option mt-3 p-3" style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px;">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1" style="color: #1976d2;">
                                <i class="fas fa-user me-2"></i>Datos encontrados
                            </h6>
                            <p class="mb-2" style="font-size: 0.9rem; color: #424242;">
                                <strong>${userInfo.nombre_completo || 'Usuario registrado'}</strong><br>
                                ${userInfo.correo ? `📧 ${userInfo.correo}<br>` : ''}
                                ${userInfo.celular ? `📱 ${userInfo.celular}<br>` : ''}
                                📅 Registrado: ${userInfo.fecha_registro}<br>
                                📋 Denuncias: ${userInfo.total_denuncias}
                            </p>
                        </div>
                        <button type="button" class="btn btn-sm btn-primary" onclick="DenunciaApp.usuarioPage.autoCompleteUserData('${userInfo.id}')">
                            <i class="fas fa-magic me-1"></i>Autocompletar
                        </button>
                    </div>
                </div>
            `);
            
            rutContainer.append(autoCompleteElement);
        },

        // ✅ AUTOCOMPLETAR DATOS DEL USUARIO
        autoCompleteUserData: function(userId) {
           
            
            // Llamada para obtener datos detallados
            $.ajax({
                url: window.AUTOCOMPLETE_USER_URL || '/api/autocomplete/user/',
                method: 'POST',
                data: {
                    rut: $('#rut').val(),
                    csrfmiddlewaretoken: DenunciaApp.common.getCSRFToken()
                },
                success: (response) => {
                    if (response.success && response.autocomplete_data) {
                        const data = response.autocomplete_data;
                        
                        // Rellenar campos automáticamente
                        $('#nombre_completo').val(data.nombre_completo || '');
                        $('#apellidos').val(data.apellidos || '');
                        $('#correo_electronico').val(data.correo_electronico || '');
                        $('#celular').val(data.celular || '');
                        
                        // Mostrar notificación
                        DenunciaApp.common.showNotification('Datos autocompletados correctamente', 'success');
                        
                        // Remover opción de autocompletado
                        $('.autocomplete-option').fadeOut(300, function() {
                            $(this).remove();
                        });
                        
                        
                    } else {
                        DenunciaApp.common.showNotification('No se pudieron autocompletar los datos', 'error');
                    }
                },
                error: () => {
                    DenunciaApp.common.showNotification('Error al autocompletar datos', 'error');
                }
            });
        },

        // ===========================================
        // RESTO DE FUNCIONES EXISTENTES (sin cambios)
        // ===========================================
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

            // Formateo de celular
            $('#celular').on('input', function () {
                let val = $(this).val();
                val = val.replace(/\D/g, '');
                val = val.substring(0, 8);
                
                let formatted = '';
                if (val.length > 0) {
                    if (val.length <= 4) {
                        formatted = val;
                    } else {
                        formatted = val.substring(0, 4) + ' ' + val.substring(4, 8);
                    }
                }
                
                $(this).val(formatted);
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
                
                return;
            }

           

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                

                const existeInput= document.querySelector('input[name="tipo_denuncia"]');

                if(existeInput){
                    const tipoSeleccionado = document.querySelector('input[name="tipo_denuncia"]:checked');
                    if (!tipoSeleccionado ) {
                        DenunciaApp.common.showError('Por favor, seleccione el tipo de denuncia');
                        return;
                    }   

                    if (tipoSeleccionado.value === 'identificado') {
                        if (!this.validateIdentifiedForm()) {
                            return;
                        }
                    }
                }

                const originalText = btnEnviar.innerHTML;
                btnEnviar.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
                btnEnviar.disabled = true;

                const formData = new FormData(form);
                
                // Corregir formato del celular si está presente
                const celularInput = document.getElementById('celular');
                if (celularInput && celularInput.value) {
                    const celularLimpio = celularInput.value.replace(/\D/g, '');
                    const celularFormateado = `+569${celularLimpio}`;
                    formData.set('celular', celularFormateado);
                }
                

                // ✅ PRIMER REQUEST: Crear usuario y denuncia
                $.ajax({
                    type: 'POST',
                    url: form.action,
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(response) {
                        
                        if (response.success) {
                        
                            const codigo = response.data.codigo;
                            const esAnonima = response.data.es_anonima;
                            
                         
                            
                            btnEnviar.innerHTML = '<i class="fas fa-check me-2"></i>Usuario creado, enviando email...';
                            
                           
                            setTimeout(function() {
                        
                                if (!esAnonima) {
                                    const emailData = new FormData();
                                    emailData.set('correo_electronico', formData.get('correo_electronico'));
                                    emailData.set('codigo', codigo); 
                                    
                                    
                                    $.ajax({
                                        type: 'POST',
                                        url: '/api/email/send/',
                                        data: emailData,
                                        processData: false,
                                        contentType: false,
                                       
                                        success: function(emailResponse) {
                                            
                                            btnEnviar.innerHTML = '<i class="fas fa-check me-2"></i>¡Completado!';
                                            
                                            // Redirigir después de 500ms
                                            setTimeout(() => {
                                                if (emailResponse.redirect_url) {
                                                   
                                                    window.location.href = emailResponse.redirect_url;
                                                } else {
                                                    window.location.href = '/denuncia/final/';
                                                }
                                            }, 500);
                                        },
                                        error: function(xhr, status, error) {
                                           
                                            

                                            alert('Denuncia creada correctamente, pero hubo un error al enviar el email de confirmación.');
                                            
                                            setTimeout(() => {
                                                window.location.href = '/denuncia/final/';
                                            }, 500);
                                        }
                                    });
                                } else {
                                
                                   
                                    btnEnviar.innerHTML = '<i class="fas fa-check me-2"></i>¡Completado!';
                                    
                                    setTimeout(() => {
                                        window.location.href = '/denuncia/final/';
                                    }, 500);
                                }
                            }, 300);
                            
                        } else {
                            console.error('❌ Error en la respuesta:', response.message);
                            DenunciaApp.common.showError(response.message || 'Error al procesar los datos');
                            btnEnviar.innerHTML = originalText;
                            btnEnviar.disabled = false;
                        }
                    },
                    error: function(xhr, status, error) {
                        
                        
                        const errorMsg = xhr.responseJSON && xhr.responseJSON.message 
                            ? xhr.responseJSON.message 
                            : 'Error al enviar los datos. Por favor, inténtelo nuevamente.';
                        
                        DenunciaApp.common.showError(errorMsg);
                        btnEnviar.innerHTML = originalText;
                        btnEnviar.disabled = false;
                    }
                });
            });
        },

    
        validateIdentifiedForm: function() {
            // Verificar si el RUT está en estado válido
            const rutContainer = $('#rut').closest('.form-group');
            if (rutContainer.hasClass('rut-validation-invalid') || rutContainer.hasClass('rut-validation-error')) {
                DenunciaApp.common.showError('Por favor, ingrese un RUT válido');
                $('#rut').focus();
                return false;
            }

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

            
            return true;
        },

        setupNavigation: function() {
            const btnAtras = document.getElementById('btnAtras');
            if (btnAtras) {
                btnAtras.addEventListener('click', function() {
                   
                    window.history.back();
                });
            }
        }
    },

    // ===========================================
    // MÓDULO: PÁGINA DE CÓDIGO (sin cambios)
    // ===========================================
    codigoPage: {
        init: function() {
          
            this.setupCopyFunction();
            this.setupAnimations();
            this.setupSessionClearance();
        },

        setupCopyFunction: function() {
            // Función global para copiar código
            window.copiarCodigo = () => {
               
                
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
   
    DenunciaApp.init();
});

// Inicializar también cuando jQuery esté listo (por compatibilidad)
$(document).ready(function() {
    
    // La inicialización ya se hizo en DOMContentLoaded
});

// Exportar para uso global
window.DenunciaApp = DenunciaApp;