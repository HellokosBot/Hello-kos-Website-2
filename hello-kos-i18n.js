(function(){
  var LANGS={nl:'Nederlands',de:'Deutsch',en:'English',it:'Italiano',tr:'Türkçe'};
  var FLAGS={nl:'🇳🇱',de:'🇩🇪',en:'🇬🇧',it:'🇮🇹',tr:'🇹🇷'};
  var VOICE={nl:'nl-NL',de:'de-DE',en:'en-GB',it:'it-IT',tr:'tr-TR'};
  var T={
    shared:{
      read:'Voorlezen','stop':'Stop','gmaps:'📍 Google Maps','amaps:'🍏 Apple Maps','back':'← Terug','tip':'Tip'
    },
    palm:{
      title:'Palm Tree Lane',lead:'Brede laan met palmen en de oude boogbrug – vroeger water tussen kasteel-eiland en stad, nu een van de bekendste straten van Kos-stad.',
      b1:'Gratis',b2:'Kos-stad',b3:'Haven',c1:'Herkenningspunt van Kos-stad',c1p:'<strong>Palm Tree Lane</strong> (Finikon / Phoinikon Avenue) is een van de meest herkenbare plekken van Kos-stad: een brede laan met de oude stenen boogbrug en uitzicht op het kasteel van Neratzia.',
      f1:'Brug',f1l:'naar het kasteel',f2:'Gratis',f2l:'openbaar',c2:'Van eiland naar laan',c2p1:'Het kasteel van Neratzia stond vroeger op een <strong>klein eiland</strong>, gescheiden van het vasteland door water. Tijdens de Italiaanse bezetting (rond 1912–1943) vulden ze de gracht op met aarde, zodat het eilandje vast kwam te liggen aan de stad.',c2p2:'Ze maakten er een brede laan van, met de oude stenen <strong>boogbrug</strong> die er nog steeds ligt. De Italianen plantten hoge palmen langs beide kanten, voor schaduw en een mooi beeld.',
      cap1:'Laan met zicht op het kasteel',c3:'Palmen gekapt',c3p:'Enkele jaren geleden moesten alle palmen worden gekapt door een invasieve keversoort die de bomen aantastte en zich kon verspreiden. Er staan weer (nieuwe) palmen; de laan blijft een centrale wandel- en fietsroute bij de haven.',
      c4:'Video’s',c4p:'Beelden van Palm Tree Lane en de omgeving:',cap2:'Palm Tree Lane',cap3:'De laan en de brug',cap4:'Rondom Palm Tree Lane',g1:'De laan',g2:'Brug',c5:'Bezoeken',c5p:'Gratis, altijd toegankelijk – tussen haven, kasteel en centrum.',tip:'mooi om te wandelen of te fietsen, vooral tegen zonsondergang met het kasteel op de achtergrond.'
    },
    agia:{
      title:'Agia Paraskevi-kerk',lead:'Grote orthodoxe parochiekerk in het centrum – mozaïekvloer, kroonluchters, na 2017 weer gerestaureerd en open.',
      b1:'Gratis',b2:'Kos-stad',b3:'Weer open',c1:'Parochiekerk in het centrum',c1p:'<strong>Agia Paraskevi</strong> is een van de grootste orthodoxe kerken in Kos-stad en nog steeds actief als parochiekerk. Veel bezoekers lopen binnen om een kaarsje aan te steken of van de rust te genieten.',
      f1:'Open',f1l:'na renovatie',f2:'Gratis',f2l:'binnen kijken',c2:'Interieur',c2p:'Binnen zie je onder meer kroonluchters en een uniek <strong>mozaïek van kiezelstenen</strong> op de vloer. De sfeer is serene – heel anders dan de drukte buiten.',
      cap1:'De kerk in het centrum',c3:'Aardbeving 2017',c3p:'Na de grote aardbeving van <strong>2017</strong> had de kerk ernstige schade en was ze gesloten. Na een omvangrijke renovatie is ze <strong>weer geopend</strong> voor bezoekers.',
      g1:'Detail',g2:'In het centrum',c4:'Bezoeken',c4p:'Vaak open van ’s ochtends tot ’s avonds. Mooie stop tijdens een wandeling door het oude centrum.',tip:'kijk naar de kiezelmozaïekvloer en de kroonluchters – en houd het stil als er een dienst is.'
    },
    hatzi:{
      title:'Hatzi Pasha Mausoleum',lead:'Klein Ottomaans grafmonument met koepeltje – sarcofaag van officier Hatzi Pasha, gesneuveld in 1527 bij een piratenaanval.',
      b1:'Gratis',b2:'Kos-stad',b3:'16e eeuw',c1:'Onopvallend, bijna 500 jaar oud',c1p:'Een bescheiden, vierkant stenen gebouw in het hart van Kos-stad. Veel mensen lopen er voorbij zonder te weten dat hier de sarcofaag van <strong>Hatzi Pasha</strong> staat – al bijna 500 jaar.',
      f1:'1527',f1l:'gesneuveld',f2:'Gratis',f2l:'van buitenaf',c2:'Wie was Hatzi Pasha?',c2p1:'Hatzi Pasha was een Ottomaanse officier op het eiland. In <strong>1527</strong> sneuvelde hij tijdens een aanval van piraten die de kust onveilig maakten.',c2p2:'Zijn lichaam werd begraven in deze marmeren sarcofaag, die nog altijd op dezelfde plek staat. Het is het enige directe spoor dat van hem overblijft.',
      cap1:'Het mausoleum met koepeltje',c3:'Het gebouw',c3p:'Een eenvoudige, rechthoekige stenen mausoleum met een <strong>klein koepeltje</strong> erbovenop. Typisch Ottomaans grafmonument uit de vroege periode op Kos.',
      g1:'Detail',g2:'Gebouw',c4:'Bezoeken',c4p:'In het centrum van Kos-stad. Van buitenaf gratis te zien; makkelijk te missen als je er niet op let.',tip:'zoek het kleine gebouwtje met het koepeltje – het is snel over het hoofd gezien tussen de andere gebouwen.'
    }
  };
  var cur='nl';
  function getLang(){var l=localStorage.getItem('hk-lang')||'nl';return LANGS[l]?l:'nl';}
  function setLang(l){if(!LANGS[l])return;cur=l;localStorage.setItem('hk-lang',l);apply();}
  function tr(obj,key){if(!obj)return'';var o=obj[cur];return(o&&o[key])||obj.nl[key]||'';}
  function apply(){
    document.querySelectorAll('[data-i18n]').forEach(function(el){
      var k=el.getAttribute('data-i18n');var p=k.split('.');var v=T;for(var i=0;i<p.length;i++){v=v&&v[p[i]];}
      if(v){if(el.tagName==='INPUT'||el.tagName==='TEXTAREA')el.placeholder=v;else el.innerHTML=v;}
    });
    var bar=document.getElementById('hk-langbar');if(!bar){bar=document.createElement('div');bar.id='hk-langbar';bar.style.cssText='position:absolute;right:14px;top:50%;transform:translateY(-50%);display:flex;gap:4px;';var h=document.querySelector('.app-header');if(h){h.style.position='relative';h.appendChild(bar);}}
    bar.innerHTML='';Object.keys(LANGS).forEach(function(l){
      var b=document.createElement('button');b.type='button';b.textContent=FLAGS[l];b.title=LANGS[l];
      b.style.cssText='border:none;background:'+(l===cur?'#2A6F6F':'transparent')+';border-radius:6px;padding:4px 6px;cursor:pointer;font-size:1rem;';
      b.onclick=function(){setLang(l);};bar.appendChild(b);
    });
  }
  function pickVoice(code){var voices=speechSynthesis.getVoices()||[];var p=code.slice(0,2).toLowerCase();return voices.find(function(v){return v.lang===code;})||voices.find(function(v){return v.lang&&v.lang.toLowerCase().indexOf(p)===0;})||null;}
  var btnPlay=document.getElementById('btnPlay'),btnStop=document.getElementById('btnStop'),status=document.getElementById('ttsStatus'),readText=document.getElementById('readText);
  function setStatus(t){if(status)status.textContent=t;}
  function play(){
    if(!window.speechSynthesis){setStatus('Voorlezen niet ondersteund.');return;}
    speechSynthesis.cancel();var text=(readText?readText.innerText:'').replace(/\s+/g,' ').trim();if(!text)return;
    var u=new SpeechSynthesisUtterance(text);u.lang=VOICE[cur];u.rate=0.92;var v=pickVoice(VOICE[cur]);if(v)u.voice=v;
    u.onstart=function(){btnPlay.classList.add('playing');btnStop.classList.add('show');setStatus('▶ '+cur.toUpperCase());};u.onend=u.onerror=function(){btnPlay.classList.remove('playing');btnStop.classList.remove('show');setStatus('');};
    if(!speechSynthesis.getVoices().length){speechSynthesis.onvoiceschanged=function(){var v2=pickVoice(VOICE[cur]);if(v2)u.voice=v2;speechSynthesis.speak(u);};setTimeout(function(){speechSynthesis.speak(u);},250);}else speechSynthesis.speak(u);
  }
  function stop(){if(window.speechSynthesis)speechSynthesis.cancel();if(btnPlay)btnPlay.classList.remove('playing');if(btnStop)btnStop.classList.remove('show');setStatus('⏹ Gestopt.');}
  if(btnPlay)btnPlay.addEventListener('click',play);if(btnStop)btnStop.addEventListener('click',stop);
  if(window.speechSynthesis){speechSynthesis.getVoices();speechSynthesis.onvoiceschanged=function(){speechSynthesis.getVoices();};}
  cur=getLang();apply();window.HK_I18N={setLang:setLang,getLang:getLang,T:T,LANGS:LANGS};})();