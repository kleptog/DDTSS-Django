// Common javascript file for the DDTSS-Django project
function popup (url) {
 fenster = window.open(url, "msgwindow", "width=400,height=300,resizable=yes");
 fenster.focus();
 return true;
}

function setup_messagelinks() {
  $("a.messagelink").click(function () {
    popup(this.href)
    return false; // suppress normal click event
  })
}
