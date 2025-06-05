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

        // ⭐ FUNCIÓN SIMPLE: Insertar error DENTRO de .tab-content como primer hijo + scroll arriba
        showError: function(message, container = null) {
            console.log('🚨 Mostrando error:', message);
            
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
                console.log('✅ Encontrado .tab-content, insertando como primer hijo...');
                $(tabContent).prepend(alert);
                console.log('✅ Error insertado dentro de .tab-content');
                
                // ⭐ SCROLL SIMPLE: Ir hasta arriba
                setTimeout(() => {
                    $('html, body').animate({scrollTop: 0}, 600);
                    console.log('✅ Scroll hacia arriba completado');
                }, 100);
                
            } else {
                // Fallback simple
                console.log('❌ No se encontró .tab-content, usando fallback');
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
            
            console.log('✅ showError completado');
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
            console.log('📋 Inicializando página de items con collapse');
            this.setupForm();
            this.setupSelectionEffects();
            this.setupCollapseSystem();
            this.initAccessibility();
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
                                window.location.href = '/denuncia/Paso2/';
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

        // ... resto de funciones del itemsPage se mantienen igual ...
        setupSelectionEffects: function() { /* código existente */ },
        setupCollapseSystem: function() { /* código existente */ },
        // etc...
    },

    // ===========================================
    // MÓDULO: PÁGINA DEL WIZARD (sin cambios)
    // ===========================================
    wizardPage: {
        // ... todo el código del wizard se mantiene igual ...
        init: function() { /* código existente */ },
        setupSmartWizard: function() { /* código existente */ },
        // etc...
    },

    // ===========================================
    // MÓDULO: PÁGINA DE USUARIO ⭐ ACTUALIZADA CON VALIDACIÓN DE RUT
    // ===========================================
    usuarioPage: {
        // Variables para debounce y control de validación
        rutValidationTimeout: null,
        rutValidationRequest: null,
        
        init: function() {
            console.log('👤 Inicializando página de usuario con validación de RUT');
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
            console.log('🔍 Configurando validación de RUT en tiempo real');
            
            const rutInput = $('#rut');
            const rutContainer = rutInput.closest('.form-group');
            
            if (!rutInput.length) {
                console.log('❌ No se encontró campo RUT');
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
                    console.log(`🔍 Programando validación para RUT: ${rutValue}`);
                    
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
                    
                    console.log(`🔍 Validación inmediata por blur: ${rutValue}`);
                    this.validateRutRealTime(rutValue, rutContainer);
                }
            });
        },

        // ✅ FUNCIÓN PRINCIPAL DE VALIDACIÓN
        validateRutRealTime: function(rut, container) {
            console.log(`📡 Iniciando validación de RUT: ${rut}`);
            
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
                
                beforeSend: function() {
                    console.log('🔄 Enviando validación de RUT...');
                },
                
                success: (response) => {
                    console.log('✅ Respuesta de validación RUT:', response);
                    this.handleRutValidationResponse(response, container);
                },
                
                error: (xhr, status, error) => {
                    console.log('❌ Error en validación RUT:', {status, error});
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
                        console.log('⚠️ RUT ya existe en el sistema');
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
                        console.log('✅ RUT válido y disponible');
                        this.showRutValidationState(
                            container, 
                            'valid', 
                            response.message
                        );
                    }
                } else {
                    // ❌ RUT INVÁLIDO
                    console.log('❌ RUT con formato inválido');
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
                console.log('⏰ Timeout en validación de RUT');
            } else if (status === 'abort') {
                console.log('🛑 Validación de RUT cancelada');
                return; // No mostrar error si fue cancelada
            } else {
                console.log(`❌ Error de red: ${error}`);
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
            
            console.log(`🎨 Estado visual RUT: ${state} - ${message}`);
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
            console.log(`🪄 Autocompletando datos del usuario: ${userId}`);
            
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
                        
                        console.log('✅ Datos autocompletados');
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

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                console.log('📤 Enviando formulario de usuario...');

                const tipoSeleccionado = document.querySelector('input[name="tipo_denuncia"]:checked');
                if (!tipoSeleccionado) {
                    DenunciaApp.common.showError('Por favor, seleccione el tipo de denuncia');
                    return;
                }

                if (tipoSeleccionado.value === 'identificado') {
                    if (!this.validateIdentifiedForm()) {
                        return;
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
                                    window.location.href = response.redirect_url;
                                } else {
                                    window.location.href = '/denuncia/final/';
                                }
                            }, 1000);
                        } else {
                            DenunciaApp.common.showError(response.message || 'Error al procesar los datos');
                            btnEnviar.innerHTML = originalText;
                            btnEnviar.disabled = false;
                        }
                    },
                    error: function(xhr, status, error) {
                        console.log('❌ Error AJAX:', error);
                        DenunciaApp.common.showError('Error al enviar los datos. Por favor, inténtelo nuevamente.');
                        btnEnviar.innerHTML = originalText;
                        btnEnviar.disabled = false;
                    }
                });
            });
        },

        // ✅ ACTUALIZAR VALIDACIÓN DE FORMULARIO PARA INCLUIR ESTADO DE RUT
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
    // MÓDULO: PÁGINA DE CÓDIGO (sin cambios)
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