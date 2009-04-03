// ==UserScript==
	// @include http://crap.fi/*
	// ==/UserScript==

// Remove the huge logo div (contains an IMG and has a height set by CSS).

/*
NOTE:
A normal 'load' event listener or inline, top-level commands
don't work quite right: the DIV is first displayed
and then immediately removed.

The trick is to use 'BeforeEvent.load', which must be set
to 'window.opera' instead of just 'document'.
*/

window.opera.addEventListener(
    'BeforeEvent.load',
    function (e) {
        if (!document.body) { return; }
        var logo = document.getElementById('logo');
        document.body.removeChild(logo);
        },
    false
    );
