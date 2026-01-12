(function(factory, global, $){
	global.captcha = typeof(global.captcha) !== 'function' ? factory.call(global, $) : global.captcha;
}(function($){
	function Captcha(){}
	function Helper(){}
	Helper.mapper = Helper.mapper ? Helper.mapper : {};
	Helper.format = function(){
		var s = arguments[0], i = arguments.length;
		while (--i) {
			s = s.replace(new RegExp('\\{' + (i - 1) + '\\}', 'gm'), arguments[i]);
		}
		return s;
	}
	Helper.isEn = function(){
		return ('' + Helper.mapper.lang).toLowerCase() == 'en';
	}
	Captcha.register = function(option) {
		// option : root, id, width, height, lang
		Helper.mapper.root = option.root;
		Helper.mapper.id = option.id;
		Helper.mapper.width = option.width;
		Helper.mapper.height = option.height;
		Helper.mapper.lang = option.lang;

		$(function(){
			Captcha.changeImgCode(Helper.mapper);

			$('#imageBlock_' + Helper.mapper.id).click(function() {
				Captcha.changeImgCode(Helper.mapper);
			});

			$('#voiceplay_' + Helper.mapper.id).click(function() {
				Captcha.playAudio(this, Helper.mapper.root, Helper.mapper.id);
			});

			$('#captchaKey_' + Helper.mapper.id).change(function() {
				Captcha.changeImgCode(Helper.mapper);
			});
		});
	}
	Captcha.triggerChange = function(newCaptchaKey){
		$('#captchaKey_'+Helper.mapper.id).val(newCaptchaKey).trigger('change');
	}

	Captcha.changeImgCode = function(option){
		var root = option.root,
			id = option.id,
			width = option.width,
			height = option.height,
			lang = option.lang;
		var captchaKey = $('#captchaKey_'+id).val();
		var now = new Date();
		var alt = Helper.isEn() ? 'Verification Code image' : '驗證碼影像';
		var src = Helper.format('{0}image?CAPTCHA_KEY={1}&time={2}', root, captchaKey, now.getTime()),
			url = Helper.format('<img id="captchaImage_{0}" name="captchaImage" style="padding: 6px;" src="{1}" alt="{2}" title="{2}" width="{3}" height="{4}" />', id, src, alt, width, height);
		$('#captchaBox_'+id).empty().append(url);
	}

	Captcha.playAudio = function(target, root, id) {
		var captchaKey = $('#captchaKey_' + id).val();
		var ua = navigator.userAgent.toLowerCase();
		var isIE = ua.match(/(msie|(rv:([\d.]+)\) like gecko))/);
		// var isFX = ua.match(/firefox/);
		var now = new Date();

		var voicetrack = $('#voicetrack_' + id);
		if (voicetrack.length == 0) {
			voicetrack = $('<div id="voicetrack_' + id + '" style="display:none;"></div>')
			$('body').append(voicetrack);
		}

		var urlSrc = root + 'sound/' + captchaKey + '/' + now.getTime();

		if (isIE) {
			var object = [
				'<object type="audio/x-wav" width="0px" height="0px">',
				'<param name="autoplay" value="true">', '<param name="autostart" value="true">', '<param name="hidden" value="true">',
				'<param name="src" value="', urlSrc, '">',
				'</object>'
			].join('');
			$(voicetrack).empty().html(object);
		} else {
			var button = $(target);
			button.attr('disabled', true);
	        $(voicetrack).empty().append(Helper.format('<audio id="audio_{0}" ><source id="source_{0}" src="" type="audio/wav" /></audio>', id));
	        var audio = $('#audio_'+id).on('canplay canplaythrough', function(){
	            window.setTimeout(function(){
	                button.attr('disabled', false);
	            }, 2000);
	        });

	        $('#source_'+id).attr('src', urlSrc);
	        audio.get(0).play();
		}
	}
	return Captcha;
}, window, jQuery));
