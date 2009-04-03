// Return true if an object has no enumerable members.
// Source: Douglas Crockford's Remedial JavaScript 
//         <javascript.crockford.com/remedial.html>
//
// TODO: is 'anyContext' needed?
//
function isEmpty(o, anyContext) {
    var i, v;
    if (typeOf(o, anyContext) === 'object') {
        for (i in o) {
            v = o[i];
            if (v !== undefined && typeOf(v) !== 'function') {
                return false;
            }
        }
    }
    return true;
}


// Fixed version of typeof operator, properly detecting arrays and null.
//
//   type        typeof      typeOf
//   ----        ------      ------
//   Object      'object'    <--
//   Array       'object'    'array'
//   Function    'function'  <--
//   String      'string'    <--
//   Number      'number'    <--
//   Boolean     'boolean'   <--
//   null        'object'    'null'
//   undefined   'undefined' <--
//
// If 'anyContext' is true, a more stringent array test is performed,
// detecting arrays from other contexts (windows or frames) as well.
// Otherwise, a faster test is used, which only works for the current context.
//
// Source: Douglas Crockford's Remedial JavaScript 
//         <javascript.crockford.com/remedial.html>
//
function typeOf(value, anyContext) {
    var s = typeof value;
    if (s === 'object') {
        if (value) {
            if (anyContext) {
                if (typeof value.length === 'number' &&
                        !(value.propertyIsEnumerable('length')) &&
                        typeof value.splice === 'function') {
                    s = 'array';
                }
            }
            else {
                if (value instanceof Array) {
                    s = 'array';
                }
            }
        } else {
            s = 'null';
        }
    }
    return s;
}


// Return a list of the enumerable items of an object.
function enumItems(o) {
    var a = [], i;
    for (i in o) a.push(i);
    return a;
}
