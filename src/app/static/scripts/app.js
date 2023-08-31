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

document.getElementById('calculate_form').addEventListener('input', function (event) {
    const target = event.target;
    if (
        target.matches('#latitude_deg, #latitude_min, #latitude_sec, #longitude_deg, #longitude_min, #longitude_sec')
    ) {
        updateHiddenCoordinates();
    }
});

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

generateApertureOptions();

const cameraPositionSelect = document.querySelector('#camera_position');
const selectedCameraPosition = cameraPositionSelect.dataset.selectedValue || '0';
cameraPositionSelect.value = selectedCameraPosition;

const apertureSelect = document.querySelector('#aperture');
const selectedAperture = apertureSelect.dataset.selectedValue || '1';
apertureSelect.value = selectedAperture;

document.addEventListener('DOMContentLoaded', function () {
    const objectNameInput = document.getElementById('object_name');
    const suggestionList = document.createElement('div');
    suggestionList.id = 'suggestion-list';
    suggestionList.className = 'suggestion-list';
    objectNameInput.parentNode.appendChild(suggestionList);

    /**
     * Creates a debounced function that delays invoking the provided function until after `delay` milliseconds have elapsed since the last time it was invoked.
     *
     * @param {Function} func - The function to debounce.
     * @param {number} delay - The number of milliseconds to delay.
     * @return {Function} - The debounced function.
     */
    function debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    const handleInput = debounce(function () {
        const query = objectNameInput.value.trim();
        fetch(`${appRoute}search_objects?query=${query}`)
            .then((response) => response.json())
            .then((suggestions) => {
                suggestionList.innerHTML = '';
                suggestions.forEach((suggestion, index) => {
                    const item = document.createElement('div');
                    item.className = 'suggestion-item';
                    item.textContent = suggestion.name;
                    item.tabIndex = 0; // Enable tab navigation

                    item.addEventListener('click', function () {
                        objectNameInput.value = suggestion.name;
                        const objectIdInput = document.getElementById('object_id');
                        objectIdInput.value = suggestion.id;
                        suggestionList.innerHTML = '';
                    });

                    item.addEventListener('keydown', function (e) {
                        if (e.key === 'ArrowDown' && index < suggestions.length - 1) {
                            suggestionList.children[index + 1].focus();
                        } else if (e.key === 'ArrowUp' && index > 0) {
                            suggestionList.children[index - 1].focus();
                        }
                    });

                    item.addEventListener('mouseover', function () {
                        objectNameInput.value = suggestion.name;
                        const objectIdInput = document.getElementById('object_id');
                        objectIdInput.value = suggestion.id;
                    });

                    suggestionList.appendChild(item);
                });
            });
    }, 300);

    objectNameInput.addEventListener('input', handleInput);
});

window.onload = getLocation;

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

    // No guardar un valor vacío para altitude
    if (nonCsrfFormValues.altitude === '') {
        delete nonCsrfFormValues.altitude;
    }

    localStorage.setItem('formData', JSON.stringify(nonCsrfFormValues));
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

        // Manejar campos aperture y camera_position
        const apertureSelect = document.querySelector('#aperture');
        const cameraPositionSelect = document.querySelector('#camera_position');

        apertureSelect.value = savedFormData.aperture ? savedFormData.aperture : '1';
        cameraPositionSelect.value = savedFormData.camera_position ? savedFormData.camera_position : '0';
    }
}

// Update LocalStorage on form submit
document.forms[0].addEventListener('submit', (event) => {
    const formData = new FormData(event.target);
    saveFormDataToLocalStorage(formData);
});

// Fill form fields from local storage
window.addEventListener('load', fillFormFieldsFromLocalStorage);
