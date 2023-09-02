// ---------------------------
// Functions
// ---------------------------

/**
 * Converts a decimal value to degrees, minutes, and seconds.
 *
 * @param {number} decimal - The decimal value to convert.
 * @return {Object} - An object containing the converted values:
 *   - degrees: The whole number part of the decimal value.
 *   - minutes: The whole number part of the decimal value's fractional part multiplied by 60.
 *   - seconds: The fractional part of the decimal value's fractional part multiplied by 3600, rounded to 2 decimal places.
 */
function decimalToDMS(decimal) {
    const sign = Math.sign(decimal);
    const absDecimal = Math.abs(decimal);
    const degrees = Math.floor(absDecimal);
    const minutes = Math.floor((absDecimal - degrees) * 60);
    const seconds = ((absDecimal - degrees - (minutes / 60)) * 3600).toFixed(2);
    return {
        degrees: degrees * sign,
        minutes: minutes,
        seconds: seconds,
    };
}

/**
 * Converts a DMS (Degrees, Minutes, Seconds) string to decimal degrees.
 *
 * @param {number} degrees - The degrees part of the DMS string.
 * @param {number} minutes - The minutes part of the DMS string.
 * @param {number} seconds - The seconds part of the DMS string.
 * @param {boolean} isLatitude - Indicates whether the DMS string represents a latitude.
 * @return {number} The converted decimal degrees.
 */
function DMSStringToDecimal(degrees, minutes, seconds, isLatitude) {
    const decimal = degrees + minutes / 60 + seconds / 3600;

    if (isLatitude) {
        return Math.max(-90, Math.min(90, decimal));
    } else {
        return Math.max(-180, Math.min(180, decimal));
    }
}

/**
 * Updates the hidden coordinates based on the values entered the latitude and longitude input fields.
 *
 * @return {void}
 */
function updateHiddenCoordinates() {
    const getInputValue = (id) => parseFloat(document.getElementById(id).value);
    const setOutputValue = (id, value) => document.getElementById(id).value = value.toFixed(6);

    const latDeg = getInputValue('latitude_deg');
    const latMin = getInputValue('latitude_min');
    const latSec = getInputValue('latitude_sec');
    const lonDeg = getInputValue('longitude_deg');
    const lonMin = getInputValue('longitude_min');
    const lonSec = getInputValue('longitude_sec');

    const isValidInput = (
        !isNaN(latDeg) &&
        !isNaN(latMin) &&
        !isNaN(latSec) &&
        !isNaN(lonDeg) &&
        !isNaN(lonMin) &&
        !isNaN(lonSec)
    );

    if (isValidInput) {
        const latitude = DMSStringToDecimal(latDeg, latMin, latSec, true);
        const longitude = DMSStringToDecimal(lonDeg, lonMin, lonSec, false);
        setOutputValue('latitude', latitude);
        setOutputValue('longitude', longitude);
    }
}

/**
 * Retrieves the user's current location using the browser's geolocation API.
 *
 * @return {void} This function does not return a value.
 */
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(setPosition);
    }
}

/**
 * Sets the position values in the form inputs.
 *
 * @param {object} position - The position object containing latitude, longitude, and altitude coordinates.
 * @return {void} This function does not return a value.
 */
function setPosition(position) {
    const {latitude, longitude, altitude} = position.coords;
    const altitudeInput = document.getElementById('altitude');

    if (!altitudeInput.value) {
        altitudeInput.value = altitude ? altitude.toFixed(0) : '';
    }

    document.getElementById('latitude').value = latitude.toFixed(6);
    document.getElementById('longitude').value = longitude.toFixed(6);

    const {degrees: latDeg, minutes: latMin, seconds: latSec} = decimalToDMS(latitude);
    const {degrees: lonDeg, minutes: lonMin, seconds: lonSec} = decimalToDMS(longitude);

    document.getElementById('latitude_deg').value = latDeg;
    document.getElementById('latitude_min').value = latMin;
    document.getElementById('latitude_sec').value = latSec;
    document.getElementById('longitude_deg').value = lonDeg;
    document.getElementById('longitude_min').value = lonMin;
    document.getElementById('longitude_sec').value = lonSec;
}

/**
 * Generates the options for the aperture select element.
 *
 * @return {void} This function does not return anything.
 */
function generateApertureOptions() {
    const apertures = [
        1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 2.8, 3.2, 3.5, 4.0, 4.5,
        5.0, 5.6, 6.3, 7.1, 8.0, 9.0, 10.0, 11.0, 13.0, 14.0, 16.0, 18.0, 20.0,
        22.0, 25.0, 29.0, 32.0, 36.0, 40.0, 45.0, 51.0, 57.0, 64.0
    ];

    const apertureSelect = document.getElementById('aperture');

    const options = apertures.map((aperture) => {
        return new Option(`f/${aperture}`, String(aperture));
    });

    apertureSelect.append(...options);

}

/**
 * Saves the form data to local storage.
 *
 * @param {FormData} formData - The form data to be saved.
 * @return {void}
 */
function saveFormDataToLocalStorage(formData) {
    const nonCsrfFormValues = {};

    for (const [key, value] of formData.entries()) {
        if (key !== 'csrf_token' && value !== '') {
            nonCsrfFormValues[key] = value;
        }
    }

    nonCsrfFormValues['aperture'] = $('#aperture').val();
    nonCsrfFormValues['camera_position'] = $('#camera_position').val();
    nonCsrfFormValues['camera'] = $('#camera').val();
    nonCsrfFormValues['object_name'] = $('#object_name').val();

    // Comprobaciones adicionales
    if (nonCsrfFormValues.altitude === '') {
        delete nonCsrfFormValues.altitude;
    }

    localStorage.setItem('formData', JSON.stringify(nonCsrfFormValues));
}


/**
 * Fills a select2 element with data retrieved from a server based on a saved value.
 *
 * @param {string} selector - The CSS selector for the select2 element.
 * @param {string} savedValue - The value to be used to retrieve data from the server.
 * @param {string} url - The URL to send the AJAX request to.
 * @return {void} This function does not return anything.
 */
function fillSelect2WithSavedData(selector, savedValue, url) {
    $.ajax({
        url: `${url}?q=${savedValue}`,
        dataType: 'json',
        success: function (data) {
            data.forEach(item => {
                const option = new Option(item.text, item.value, true, true);

                for (let key in item) {
                    if (key !== 'value' && key !== 'text') {
                        const dataAttr = 'data-' + key;
                        $(option).attr(dataAttr, item[key]);

                        // Remove the 'data-' prefix to find the related input by its ID
                        const relatedElement = $(`#${key}`);
                        if (relatedElement.length && relatedElement.is('input')) {
                            relatedElement.val(item[key]);
                        }
                    }
                }

                $(selector).append(option);
            });

            $(selector).val(savedValue).trigger('change');
            $(selector).attr('data-selected-value', savedValue);
        }
    });
}


/**
 * Fill form fields from local storage.
 *
 * @return {void} No return value.
 */
function fillFormFieldsFromLocalStorage() {
    const savedFormData = JSON.parse(localStorage.getItem('formData'));

    if (savedFormData) {
        for (const key in savedFormData) {
            if (key !== 'csrf_token') {
                const inputElement = document.getElementById(key);
                if (inputElement) {
                    inputElement.value = savedFormData[key];
                }
            }
        }

        //noinspection JSUnresolvedVariable
        if (savedFormData.aperture) {
            $('#aperture').val(savedFormData.aperture).trigger('change');
        } else {
            $('#aperture').val('1').trigger('change');
        }

        //noinspection JSUnresolvedVariable
        if (savedFormData.camera_position) {
            $('#camera_position').val(savedFormData.camera_position).trigger('change');
        } else {
            $('#camera_position').val('0').trigger('change');
        }
        if (savedFormData.camera) {
            fillSelect2WithSavedData('#camera', savedFormData.camera, `${appRoute}cameras`);
        }

        if (savedFormData.object_name) {
            fillSelect2WithSavedData('#object_name', savedFormData.object_name, `${appRoute}search_objects`);
        }
    }
}

/**
 * Initializes Select2 with the given selector, route, and minimum input length.
 *
 * @param {string} selector - The CSS selector for the Select2 element.
 * @param {string} route - The URL to fetch the data from.
 * @param {number} minInputLength - The minimum length of input required to trigger the AJAX request.
 * @param grouping
 */
function initializeSelect2(selector, route, minInputLength, grouping = null) {
    const selectElement = $(selector);

    selectElement.select2({
        minimumInputLength: minInputLength,
        ajax: {
            url: route,
            dataType: 'json',
            processResults: function (data) {
                if (grouping) {
                    const groupedData = {};
                    data.forEach(obj => {
                        if (!groupedData[obj[grouping]]) {
                            groupedData[obj[grouping]] = [];
                        }
                        groupedData[obj[grouping]].push({
                            id: obj.value,
                            text: obj.text
                        });
                    });

                    const finalGroupedData = Object.keys(groupedData).map(key => {
                        return {
                            text: key,
                            children: groupedData[key]
                        };
                    });

                    return {results: finalGroupedData};
                } else {
                    return {
                        results: data.map(function (obj) {
                            let extraData = Object.entries(obj).reduce(function (acc, [key, value]) {
                                if (key !== 'value' && key !== 'text') {
                                    acc['data-' + key] = value;
                                }
                                return acc;
                            }, {});
                            return {
                                id: obj.value,
                                text: obj.text,
                                ...extraData
                            };
                        })
                    };
                }
            }
        },
        templateResult: function (data) {
            if (data.children) {
                return $('<strong>').text(data.text);
            } else {
                return $('<span>').html(data.text);
            }
        },
        templateSelection: function (data) {
            return $('<span>').html(data.text);
        }
    }).on('select2:select', function (e) {
        const selectedData = e.params.data;
        const selectedValue = selectedData.id;
        selectElement.attr('data-selected-value', selectedValue);

        // Update related input fields based on the selected value
        for (let key in selectedData) {
            if (key.startsWith('data-')) {
                const relatedInputId = key.substring(5);
                const relatedElement = $('#' + relatedInputId);
                if (relatedElement.length && relatedElement.is('input')) {
                    relatedElement.val(selectedData[key]);
                }
            }
        }
    });
}


/**
 * Initializes a select2 dropdown with a pre-selected value.
 *
 * @param {string} selector - The CSS selector of the select element.
 * @return {void} This function does not return a value.
 */
function initSelect2WithSelectedValue(selector) {
    const selectElement = $(selector);

    selectElement.select2().on('select2:select', function (e) {
        const selectedValue = e.params.data.id;
        selectElement.attr('data-selected-value', selectedValue);
    });
}


// ---------------------------
// Initialization and Events
// ---------------------------

document.addEventListener("DOMContentLoaded", function () {

    document.getElementById('calculate_form').addEventListener('input', function (event) {
        const target = event.target;
        if (
            target.matches('#latitude_deg, #latitude_min, #latitude_sec, #longitude_deg, #longitude_min, #longitude_sec')
        ) {
            updateHiddenCoordinates();
        }
    });

    // Generate aperture options
    generateApertureOptions();


    // Get location
    getLocation();

    // Save form data to local storage on submit
    document.forms[0].addEventListener('submit', (event) => {
        const formData = new FormData(event.target);
        saveFormDataToLocalStorage(formData);
    });

    // Fill select2 dropdowns
    initializeSelect2('#object_name', `${appRoute}search_objects`, 3, "type");
    initializeSelect2('#camera', `${appRoute}cameras`, 3, "brand");

    // Initialize select2 dropdowns
    initSelect2WithSelectedValue("#aperture");
    initSelect2WithSelectedValue("#camera_position");

    // Fill form fields from local storage
    fillFormFieldsFromLocalStorage();
});
