// string trim funcs 
// Source: comp.lang.javascript FAQ v8.0 - 4.16
String.prototype.ltrim = function () { return this.replace(/^\s+/, ''); };
String.prototype.rtrim = function () { return this.replace(/\s+$/, ''); };
String.prototype.trim  = function () { return this.replace(/^\s+|\s+$/g, ''); };


// Replace '<', '>', and '&' with their HTML entity equivalents.
// This is essential for placing arbitrary strings into HTML texts.
// Source: Douglas Crockford's Remedial JavaScript 
//         <javascript.crockford.com/remedial.html>
String.prototype.entityify = function () {
    return this.replace(/&/g, "&amp;").
                replace(/</g, "&lt;").
                replace(/>/g, "&gt;");
};


/*
//quote() produces a quoted string. 
// This method returns a string that is like the original string 
// except that it is wrapped in quotes and all quote and backslash characters 
// are preceded with backslash.
String.prototype.quote = function () {
    var c, i, slen = this.length, o = '"';
    for (i = 0; i < slen; ++i) {
        c = this.charAt(i);
        if (c >= ' ') {
            if (c === '\\' || c === '"') {
                o += '\\';
            }
            o += c;
        } else {
            switch (c) {
            case '\b':
                o += '\\b';
                break;
            case '\f':
                o += '\\f';
                break;
            case '\n':
                o += '\\n';
                break;
            case '\r':
                o += '\\r';
                break;
            case '\t':
                o += '\\t';
                break;
            default:
                c = c.charCodeAt();
                o += '\\u00' + Math.floor(c / 16).toString(16) +
                    (c % 16).toString(16);
            }
        }
    }
    return o + '"';
};

escapeCtrl(s)
    { '\\':'\\\\', '\b':'\\b', '\f':'\\f', '\n':'\\n', '\r':'\\r', '\t':'\\t' }
    c.charCodeAt() < 32 --> '\x??'

escapeWide(s, i=256)
    c.charCodeAt() >= i --> '\u????'

*/


// Perform variable substitution on a string.
// Fields are string keys enclosed in curly braces ('{}').
// 'o' maps keys to values via subscripting.
// Only strings and numbers are substituted.
//
// Example:
//   info = { name:'foo', state:'bar' };
//   'the {name} is {state}'.supplant(info);  // --> 'the foo is bar'
//
// Source: Douglas Crockford's Remedial JavaScript 
//         <javascript.crockford.com/remedial.html>
//
String.prototype.supplant = function (o) {
    return this.replace(/{([^{}]*)}/g,
        function (a, b) {
            var r = o[b];
            return typeof r === 'string' || typeof r === 'number' ? r : a;
        }
    );
};

// Perform variable substitution on a string.
// Fields are keys enclosed in curly braces ('{}').
// 'x' maps keys to values via subscripting (object or array).
// Values are converted to string before substitution.
//
String.prototype.format = function (x) {
    return this.replace(/{([^{}]*)}/g,
        function (a, b) {
            return b in x ? x[b].toString() : a;
        }
    );
}
