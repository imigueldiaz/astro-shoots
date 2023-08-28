function decimalToDMS(decimal, isLatitude) {
    const sign = decimal < 0 ? -1 : 1;
    const absDecimal = Math.abs(decimal);
    const degrees = Math.floor(absDecimal);
    const minutesFloat = (absDecimal - degrees) * 60;
    const minutes = Math.floor(minutesFloat);
    const seconds = (minutesFloat - minutes) * 60;
    return {
        degrees: degrees * sign,
        minutes: minutes,
        seconds: seconds.toFixed(2),
    };
}

function DMSStringToDecimal(degrees, minutes, seconds, isLatitude) {
    const sign = degrees < 0 ? -1 : 1;
    const absDegrees = Math.abs(degrees);
    const decimal = sign * (absDegrees + minutes / 60 + seconds / 3600);
    return isLatitude
        ? Math.max(-90, Math.min(90, decimal))
        : Math.max(-180, Math.min(180, decimal));
}

function updateHiddenCoordinates() {
    const latDeg = parseFloat(document.getElementById('latitude_deg').value);
    const latMin = parseFloat(document.getElementById('latitude_min').value);
    const latSec = parseFloat(document.getElementById('latitude_sec').value);
    const lonDeg = parseFloat(document.getElementById('longitude_deg').value);
    const lonMin = parseFloat(document.getElementById('longitude_min').value);
    const lonSec = parseFloat(document.getElementById('longitude_sec').value);

    if (
        !isNaN(latDeg) &&
        !isNaN(latMin) &&
        !isNaN(latSec) &&
        !isNaN(lonDeg) &&
        !isNaN(lonMin) &&
        !isNaN(lonSec)
    ) {
        const latitude = DMSStringToDecimal(latDeg, latMin, latSec, true);
        const longitude = DMSStringToDecimal(lonDeg, lonMin, lonSec, false);
        document.getElementById('latitude').value = latitude.toFixed(6);
        document.getElementById('longitude').value = longitude.toFixed(6);
    }
}

document
    .querySelectorAll(
        'latitude_deg, latitude_min, latitude_sec, longitude_deg, longitude_min, longitude_sec',
    )
    .forEach((input) => {
        input.addEventListener('input', updateHiddenCoordinates);
    });

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(setPosition);
    }
}

function setPosition(position) {
    const latitude = position.coords.latitude.toFixed(6);
    const longitude = position.coords.longitude.toFixed(6);
    const altitude = position.coords.altitude
        ? position.coords.altitude.toFixed(0)
        : '';
    // Establecer el valor de altitude solo si está vacío
    const altitudeInput = document.getElementById('altitude');
    if (altitudeInput.value === '') {
        altitudeInput.value = altitude;
    }

    document.getElementById('latitude').value = latitude;
    document.getElementById('longitude').value = longitude;

    const {
        degrees: latDeg,
        minutes: latMin,
        seconds: latSec,
    } = decimalToDMS(latitude, true);
    const {
        degrees: lonDeg,
        minutes: lonMin,
        seconds: lonSec,
    } = decimalToDMS(longitude, false);

    document.getElementById('latitude_deg').value = latDeg;
    document.getElementById('latitude_min').value = latMin;
    document.getElementById('latitude_sec').value = latSec;
    document.getElementById('longitude_deg').value = lonDeg;
    document.getElementById('longitude_min').value = lonMin;
    document.getElementById('longitude_sec').value = lonSec;
}
function generateApertureOptions() {
    const apertures = [
        1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 2.8, 3.2, 3.5, 4.0, 4.5,
        5.0, 5.6, 6.3, 7.1, 8.0, 9.0, 10.0, 11.0, 13.0, 14.0, 16.0, 18.0, 20.0,
        22.0, 25.0, 29.0, 32.0, 36.0, 40.0, 45.0, 51.0, 57.0, 64.0, 72.0, 81.0,
        91.0,
    ];

    const apertureSelect = document.getElementById('aperture');

    apertures.forEach((aperture) => {
        const option = document.createElement('option');
        option.value = aperture;
        option.text = `f/${aperture}`;
        apertureSelect.appendChild(option);
    });
}

generateApertureOptions();

const cameraPositionSelect = document.querySelector('#camera_position');
const selectedCameraPosition = cameraPositionSelect.dataset.selectedValue;

// Set the default value if there's no value in the request arguments
if (selectedCameraPosition === undefined) {
    cameraPositionSelect.value = '0';
} else {
    cameraPositionSelect.value = selectedCameraPosition;
}

const apertureSelect = document.querySelector('#aperture');
const selectedAperture = apertureSelect.dataset.selectedValue;

// Set the default value if there's no value in the request arguments
if (selectedAperture === undefined) {
    apertureSelect.value = '1';
} else {
    apertureSelect.value = selectedAperture;
}

document.addEventListener('DOMContentLoaded', function () {
    const objectNameInput = document.getElementById('object_name');

    const suggestionList = document.createElement('div');
    suggestionList.id = 'suggestion-list';
    suggestionList.className = 'suggestion-list';

    objectNameInput.parentNode.appendChild(suggestionList);

    function debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    objectNameInput.addEventListener(
        'input',
        debounce(function () {
            const query = objectNameInput.value.trim();

            if (query.length < 3) {
                suggestionList.innerHTML = '';
                return;
            }

            fetch(`${appRoute}/search_objects?query=${query}`)
                .then((response) => response.json())
                .then((suggestions) => {
                    suggestionList.innerHTML = '';

                    suggestions.forEach((suggestion, index) => {
                        const item = document.createElement('div');
                        item.className = 'suggestion-item';
                        item.textContent = suggestion.name;
                        item.tabIndex = 0; // Enable tab navigation

                        // Click event handler
                        item.addEventListener('click', function () {
                            objectNameInput.value = suggestion.name;
                            const objectIdInput =
                                document.getElementById('object_id');
                            objectIdInput.value = suggestion.id;
                            suggestionList.innerHTML = '';
                        });

                        // Keydown event handler for arrow navigation
                        item.addEventListener('keydown', function (e) {
                            if (e.key === 'ArrowDown') {
                                if (index < suggestions.length - 1) {
                                    suggestionList.children[index + 1].focus();
                                }
                            } else if (e.key === 'ArrowUp') {
                                if (index > 0) {
                                    suggestionList.children[index - 1].focus();
                                }
                            }
                        });

                        // Mouseover event handler for hover selection
                        item.addEventListener('mouseover', function () {
                            objectNameInput.value = suggestion.name;
                            const objectIdInput =
                                document.getElementById('object_id');
                            objectIdInput.value = suggestion.id;
                        });

                        suggestionList.appendChild(item);
                    });
                });
        }, 300),
    ); // 300 milliseconds delay
});

window.onload = getLocation;

/// Guardar datos del formulario en LocalStorage
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

// Rellenar campos del formulario con datos de LocalStorage
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

        if (savedFormData.aperture) {
            apertureSelect.value = savedFormData.aperture;
        } else {
            apertureSelect.value = '1'; // Valor predeterminado
        }

        if (savedFormData.camera_position) {
            cameraPositionSelect.value = savedFormData.camera_position;
        } else {
            cameraPositionSelect.value = '0'; // Valor predeterminado
        }
    }
}

// Actualizar LocalStorage al enviar el formulario
document.forms[0].addEventListener('submit', (event) => {
    const formData = new FormData(event.target);
    saveFormDataToLocalStorage(formData);
});

// Rellenar campos del formulario al cargar la página
window.addEventListener('load', fillFormFieldsFromLocalStorage);
