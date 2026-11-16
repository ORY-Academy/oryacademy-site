(function () {
  /* Cookie notice: remembers a choice on this device; analytics may only load after "accept" */
  var KEY = 'ory-cookies', bar = document.getElementById('cookieBar');
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function apply(v) {
    window.oryCookieChoice = v;
    try { document.dispatchEvent(new CustomEvent('ory-cookie-choice', { detail: v })); } catch (e) {}
  }
  if (!bar) { return; }
  var saved = get();
  if (saved) { apply(saved); } else { bar.hidden = false; }
  bar.addEventListener('click', function (e) {
    var c = e.target.getAttribute && e.target.getAttribute('data-choice');
    if (!c) { return; }
    set(c); apply(c); bar.hidden = true;
  });
  var again = document.querySelectorAll('[data-cookie-settings]');
  for (var i = 0; i < again.length; i++) {
    again[i].addEventListener('click', function (e) {
      e.preventDefault(); bar.hidden = false;
      var b = bar.querySelector('button'); if (b) { b.focus(); }
    });
  }
})();
