// === Script 1 ===
$(function () {
	org.owasp.esapi.ESAPI.initialize();
});

// === Script 2 ===
$(function(){
		var c=window.BROWSER&&window.BROWSER.device&&!window.BROWSER.device.mobile?{'text-align':'left'}:{};
		var btns=$("button.ps-classification"),form=$(btns[0]).closest("form");btns.css(c).on("click",function(){var t=$(this).attr("data-type");t&&(btns.prop("disabled",!0),t=String.format('<input type="hidden" name="searchType" value="{0}" />',t),form.append(t).submit())});
	});

// === Script 3 ===
window.dataLayer = window.dataLayer || [];
	  function gtag(){dataLayer.push(arguments);}
	  gtag('js', new Date());

	  gtag('config', 'UA-28221981-1');

