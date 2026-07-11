document.addEventListener('DOMContentLoaded', function () {
    function formatBRL(value) {
        if (value === '' || value === null || value === undefined) return '';
        // keep digits and comma/dot
        var v = String(value).replace(/[^0-9\,\.\-]/g, '');
        if (!v) return '';
        // normalize comma to dot
        v = v.replace(/,/g, '.');
        // remove extra dots leaving only the first as decimal separator
        var parts = v.split('.');
        if (parts.length > 1) {
            var dec = parts.pop();
            v = parts.join('') + '.' + dec;
        }
        var num = parseFloat(v);
        if (isNaN(num)) return '';
        return 'R$ ' + num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function toRawNumber(formatted) {
        if (!formatted) return '';
        // remove currency symbol and spaces
        var s = String(formatted).replace(/R\$|\s/g, '');
        // remove thousand separators and convert comma to dot
        s = s.replace(/\./g, '').replace(/,/g, '.');
        // if empty or invalid, return empty
        if (s === '' || s === '.' ) return '';
        return s;
    }

    // Helper: remove grouping and currency symbol for editing
    function unformatForEdit(value) {
        if (!value) return '';
        var s = String(value).replace(/R\$|\s/g, '');
        // remove thousand separators
        s = s.replace(/\./g, '');
        return s;
    }

    // sanitize input while editing: allow digits and one comma/dot
    function sanitizeEditingValue(value) {
        if (value === null || value === undefined) return '';
        var v = String(value);
        // remove all characters except digits, comma and dot
        v = v.replace(/[^0-9\.,\-]/g, '');
        // allow only first comma or dot as decimal separator; replace additional ones
        var firstComma = v.indexOf(',');
        var firstDot = v.indexOf('.');
        // if both present, keep the last one as decimal separator by normalizing dots to empty except the first occurrence
        if (firstComma !== -1 && firstDot !== -1) {
            // prefer comma as decimal separator for editing
            v = v.replace(/\./g, '');
            // keep comma
            var parts = v.split(',');
            v = parts[0] + (parts[1] ? ',' + parts[1].replace(/[,\.]/g, '') : '');
        } else if (firstComma !== -1) {
            // remove any other commas
            var p = v.split(',');
            v = p[0] + (p[1] ? ',' + p[1].replace(/[,\.]/g, '') : '');
        } else if (firstDot !== -1) {
            var p2 = v.split('.');
            v = p2[0] + (p2[1] ? '.' + p2[1].replace(/[\.\,]/g, '') : '');
        }
        return v;
    }

    // apply to currency inputs: format on blur, unformat on focus, sanitize on input
    var elements = document.querySelectorAll('input.currency, input[type="number"].currency');
    elements.forEach(function (el) {
        el.type = 'text';

        // initialize formatted display
        if (el.value) {
            el.value = formatBRL(el.value);
        }

        el.addEventListener('focus', function () {
            el.value = unformatForEdit(el.value);
            // place caret at end
            setTimeout(function () { try { el.setSelectionRange(el.value.length, el.value.length); } catch (e) {} }, 0);
        });

        el.addEventListener('input', function () {
            el.value = sanitizeEditingValue(el.value);
        });

        el.addEventListener('blur', function () {
            // if empty -> keep empty
            if (!el.value) return;
            el.value = formatBRL(el.value);
        });
    });

    // ensure forms send raw numeric values (dot decimal) on submit
    var forms = document.querySelectorAll('form');
    forms.forEach(function (form) {
        form.addEventListener('submit', function () {
            var els = form.querySelectorAll('input.currency, input[type="number"].currency');
            els.forEach(function (el) {
                var raw = toRawNumber(el.value);
                el.value = raw;
            });
            // convert date-mask fields from DD/MM/YYYY to YYYY-MM-DD for backend
            var dates = form.querySelectorAll('input.date-mask');
            dates.forEach(function (d) {
                var v = d.value || '';
                var m = v.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
                if (m) {
                    d.value = m[3] + '-' + m[2] + '-' + m[1];
                }
            });
        });
    });

    // Date mask DD/MM/YYYY for inputs with class date-mask
    function formatDateMask(value) {
        if (!value) return '';
        var digits = String(value).replace(/\D/g, '');
        if (digits.length === 0) return '';
        if (digits.length <= 2) return digits;
        if (digits.length <= 4) return digits.slice(0,2) + '/' + digits.slice(2);
        return digits.slice(0,2) + '/' + digits.slice(2,4) + '/' + digits.slice(4,8);
    }

    var dateInputs = document.querySelectorAll('input.date-mask');
    dateInputs.forEach(function (el) {
        el.type = 'text';
        el.setAttribute('inputmode', 'numeric');
        // initialize if ISO date present (YYYY-MM-DD) convert to DD/MM/YYYY
        if (/^\d{4}-\d{2}-\d{2}$/.test(el.value)) {
            var p = el.value.split('-');
            el.value = p[2] + '/' + p[1] + '/' + p[0];
        }
        el.addEventListener('input', function (e) {
            var pos = el.selectionStart;
            el.value = formatDateMask(el.value);
            el.setSelectionRange(el.value.length, el.value.length);
        });
    });
});
