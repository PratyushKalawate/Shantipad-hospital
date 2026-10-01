(() => {
  "use strict";
  const routes = ["/", "/about/", "/child-care/", "/dental-care/", "/doctors/", "/contact/"];
  const page = Math.max(0, routes.indexOf(location.pathname.replace(/index\.html$/, "").replace(/\/?$/, "/")));
  let lang = "en", data;
  try { lang = localStorage.getItem("shantipad-language") || "en"; } catch {}
  if (!["en", "hi", "mr"].includes(lang)) lang = "en";
  const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const text = value => typeof value === "object" && value ? (value[lang] || value.en || "") : (value || "");
  const html = value => escape(text(value)).replace(/\n/g, "<br>");
  const copy = key => data?.copy?.[lang]?.[key] ?? data?.copy?.en?.[key] ?? "";
  const t = key => html(copy(key));
  const icon = name => '<i data-lucide="' + name + '" aria-hidden="true"></i>';
  const safeUrl = value => {
    if (!value) return "";
    try {
      const u = new URL(value, location.origin);
      return u.protocol === "https:" || (u.protocol === "http:" && u.origin === location.origin) ? u.href : "";
    } catch { return ""; }
  };
  const link = (url, label, cls = "text-link") => '<a class="' + cls + '" href="' + escape(url) + '">' + label + icon("arrow-up-right") + '</a>';
  const call = (white = false) => '<button class="button ' + (white ? "button-white" : "button-primary") + '" data-call>' + icon("phone") + '<span>' + t("call") + '</span></button>';
  const phoneLink = number => /^[+][0-9]{8,15}$/.test(number) ? '<a class="phone-link" href="tel:' + number + '">' + icon("phone") + '<bdi>' + escape(number.replace(/^([+]91)([0-9]{5})([0-9]{5})$/, "$1 $2 $3")) + '</bdi></a>' : "";
  const appointmentLinks = () => '<div class="appointment-options">' + data.appointments.map(phoneLink).join("") + '</div>';
  const navLabels = () => ["Home", "About us", "Child care", "Dental care", "Our doctors", "Contact"].map((v,i) => {
    const names = {hi:["होम","हमारे बारे में","बाल चिकित्सा","दंत चिकित्सा","हमारे डॉक्टर","संपर्क"],mr:["मुख्यपृष्ठ","आमच्याबद्दल","बालरोग विभाग","दंत विभाग","आमचे डॉक्टर","संपर्क"]};
    return lang === "en" ? v : names[lang][i];
  });
  function brand() {
    const logo = safeUrl(data.hospital.logo_url);
    return '<a href="/" class="brand" aria-label="' + escape(text(data.hospital.name)) + '">' +
      (logo ? '<img class="brand-logo" src="' + escape(logo) + '" alt="" width="56" height="56">' : '<span class="brand-icon">' + icon("cross") + '</span>') +
      '<span><strong>' + html(data.hospital.name) + '</strong><small>' + t("descriptor") + '</small></span></a>';
  }
  function photo() {
    const url = safeUrl(data.hospital.hero_image_url);
    return url ? '<figure class="family-photo"><img src="' + escape(url) + '" alt="' + escape(copy("heroImageAlt")) + '" width="2000" height="1333"><figcaption>' + t("heroImageCaption") + '</figcaption></figure>' : "";
  }
  function care() {
    return '<section class="section care-section" id="care"><div class="container"><div class="section-heading"><div><p class="eyebrow">' + t("careLabel") + '</p><h2>' + t("careTitle") + '</h2></div><p>' + t("careIntro") + '</p></div><div class="care-grid">' +
      ["child","dental"].map((key,i) => '<a class="care-card ' + key + '" href="' + routes[i+2] + '"><div class="care-card-top"><span class="care-icon">' + icon(i ? "smile" : "baby") + '</span><span class="number">0' + (i+1) + '</span></div><p class="eyebrow">' + t(key+"Tag") + '</p><h3>' + t(key) + '</h3><p>' + t(key+"Desc") + '</p><span class="card-link">' + t(key+"Link") + icon("arrow-up-right") + '</span></a>').join("") + '</div></div></section>';
  }
  function doctorCards() {
    return '<div class="doctor-grid">' + data.doctors.map(d => {
      const image = safeUrl(d.photo_url);
      const department = d.specialty === "dental" ? "dental" : "child";
      return '<article class="doctor-card"><div class="doctor-portrait ' + department + '">' + (image ? '<img src="' + escape(image) + '" alt="' + escape(text(d.name)) + '" loading="lazy">' : icon("user-round") + '<span>' + t("photoPending") + '</span>') +
        '</div><div class="doctor-copy"><p class="eyebrow">' + t(department) + '</p><h3>' + html(d.name) + '</h3><p class="qualification">' + html(d.qualifications) + '</p>' +
        (text(d.experience) ? '<p class="doctor-experience">' + html(d.experience) + '</p>' : "") +
        (text(d.bio) ? '<p>' + html(d.bio) + '</p>' : "") +
        (d.registration ? '<p>' + t("registrationLabel") + ': ' + html(d.registration) + '</p>' : "") +
        (text(d.consultation) ? '<p class="consultation">' + html(d.consultation) + '</p>' : "") +
        link(routes[department === "dental" ? 3 : 2], t(department+"Link")) + '</div></article>';
    }).join("") + '</div>';
  }
  function doctors() {
    return '<section class="section"><div class="container"><div class="section-heading"><div><p class="eyebrow">' + t("doctorsLabel") + '</p><h2>' + t("doctorsTitle") + '</h2></div>' + link("/doctors/", t("meet")) + '</div>' + doctorCards() + '</div></section>';
  }
  function faq() {
    if (!data.faqs.length) return "";
    return '<section class="section faq-section"><div class="container faq-grid"><div><p class="eyebrow">' + t("faqLabel") + '</p><h2>' + t("faqTitle") + '</h2></div><div class="faqs">' +
      data.faqs.map(f => '<details><summary>' + html(f.question) + icon("plus") + '</summary><p>' + html(f.answer) + '</p></details>').join("") + '</div></div></section>';
  }
  function visit() {
    return '<section class="visit-band"><div class="container visit-content"><div><p class="eyebrow">' + t("visitLabel") + '</p><h2>' + t("visitTitle") + '</h2><p>' + t("visitBody") + '</p></div>' + call(true) + '</div></section>';
  }
  function local() {
    const logo = safeUrl(data.hospital.logo_url);
    return '<section class="section local-section" id="rooted"><div class="container local-grid"><figure class="local-identity">' +
      (logo ? '<img class="local-logo" src="' + escape(logo) + '" alt="' + escape(text(data.hospital.name)) + '" width="240" height="240" loading="lazy">' : '<h3>' + html(data.hospital.name) + '</h3>') +
      '<figcaption>' + icon("map-pin") + '<span>' + html(data.hospital.address) + '</span></figcaption></figure><div><p class="eyebrow">' + t("localLabel") + '</p><h2>' + t("localTitle") + '</h2><p class="body-large">' + html(data.hospital.about) + '</p>' + link("/about/", t("aboutLink")) + '</div></div></section>';
  }
  function innerHeading(eyebrow, title, intro) {
    return '<section class="inner-hero"><div class="container"><div class="breadcrumb"><a href="/">' + escape(navLabels()[0]) + '</a>' + icon("chevron-right") + '<span>' + escape(navLabels()[page]) + '</span></div><p class="eyebrow">' + eyebrow + '</p><h1>' + title + '</h1><p class="body-large">' + intro + '</p></div></section>';
  }
  function hours() {
    return '<dl class="hours-list">' + data.hours.map(h => '<div><dt>' + html(h.label) + '</dt><dd>' + html(h.times) + (text(h.note) ? '<small>' + html(h.note) + '</small>' : "") + '</dd></div>').join("") + '</dl><p class="hours-note">' + t("hoursNote") + '</p>';
  }
  function facilities() {
    if (!data.facilities.length) return "";
    return '<section class="section"><div class="container"><p class="eyebrow">' + t("localLabel") + '</p><h2>' + t("facilitiesHeading") + '</h2><div class="facility-grid">' + data.facilities.map(f => '<article>' + icon("check") + '<div><h3>' + html(f.name) + '</h3>' + (text(f.description) ? '<p>' + html(f.description) + '</p>' : "") + '</div></article>').join("") + '</div></div></section>';
  }
  function support() {
    return '<section class="section support-section"><div class="container"><p class="eyebrow">' + t("faqLabel") + '</p><div class="support-grid visit-information"><div><h2>' + t("opd") + '</h2>' + hours() +
      (data.hospital.emergency_24h ? '<p class="emergency-note">' + icon("clock") + t("emergency") + '</p>' : "") + phoneLink(data.hospital.phone) + '</div>' +
      (data.partners.length ? '<div class="cashless"><h2>' + t("cashlessTitle") + '</h2><p>' + t("cashlessIntro") + '</p><ul>' + data.partners.map(s=>'<li>'+html(s)+'</li>').join("") + '</ul></div>' : "") + '</div></div></section>';
  }
  function home() {
    return '<section class="hero">' + photo() + '<div class="hero-wash"></div><div class="container hero-content"><p class="eyebrow">' + t("eyebrow") + '</p><h1>' + t("hero") + '</h1><h2>' + t("tagline") + '</h2><p class="hero-intro">' + t("intro") + '</p><div class="hero-actions">' + call() + link("#care",t("explore"),"button button-outline") + '</div><div class="hero-location">' + icon("map-pin") + t("location") + '</div></div></section>' +
      '<div class="quick-band"><div class="container quick-links">' + [[2,"baby","child"],[3,"smile","dental"],[4,"stethoscope","meet"],[5,"map-pin","mapLabel"]].map(([i,ico,key])=>'<a href="'+routes[i]+'">'+icon(ico)+'<span>'+t(key)+'</span>'+icon("arrow-up-right")+'</a>').join("") + '</div></div>' +
      care() + local() + doctors() + facilities() + support() + faq() + visit();
  }
  function about() {
    return innerHeading(t("aboutSmall"),t("aboutTitle"),t("aboutIntro")) + '<section class="section"><div class="container about-grid">' + photo() + '<div><p class="eyebrow">' + t("localLabel") + '</p><h2>' + t("localTitle") + '</h2><p class="body-large">' + html(data.hospital.about) + '</p></div></div></section>' + facilities() + support() + visit();
  }
  function department(dental) {
    const key = dental ? "dental" : "child";
    const services = data.services.filter(s=>s.department===key);
    return innerHeading(t(key),t(dental?"deptDentalTitle":"deptChildTitle"),t(dental?"deptDentalBody":"deptChildBody")) +
      '<section class="section"><div class="container department-grid"><div><span class="department-icon '+key+'">'+icon(dental?"smile":"baby")+'</span><h2>'+t("serviceHeading")+'</h2><ul class="service-list">'+services.map(s=>'<li>'+icon("check")+'<div><strong>'+html(s.name)+'</strong>'+(text(s.description)?'<p>'+html(s.description)+'</p>':"")+'</div></li>').join("")+'</ul>'+(services.length?"":'<p>'+t("emptyServices")+'</p>')+call()+'</div><aside class="prepare"><p class="eyebrow">'+t("faqLabel")+'</p><h3>'+t("opd")+'</h3>'+hours()+link("/doctors/",t("meet"))+'</aside></div></section>'+faq()+visit();
  }
  function contact() {
    const maps = safeUrl(data.hospital.maps_url);
    return innerHeading(escape(navLabels()[5]),t("contactTitle"),t("contactIntro"))+
      '<section class="section"><div class="container contact-grid"><div class="contact-details"><div class="contact-row">'+icon("phone")+'<div><h3>'+t("phoneLabel")+'</h3>'+appointmentLinks()+'</div></div><div class="contact-row">'+icon("building-2")+'<div><h3>'+t("hospitalLine")+'</h3>'+phoneLink(data.hospital.phone)+(data.hospital.emergency_24h?'<p>'+t("emergency")+'</p>':"")+'</div></div><div class="contact-row">'+icon("map-pin")+'<div><h3>'+t("addressLabel")+'</h3><p>'+html(data.hospital.address)+'</p>'+(maps?link(maps,t("mapLabel")):"")+'</div></div>'+(data.hospital.email?'<div class="contact-row">'+icon("mail")+'<a href="mailto:'+escape(data.hospital.email)+'">'+html(data.hospital.email)+'</a></div>':"")+'</div><div class="booking-panel"><p class="eyebrow">'+t("visitLabel")+'</p><h2>'+t("bookingTitle")+'</h2><p class="body-large">'+t("bookingIntro")+'</p>'+call()+'</div></div></section>'+support()+faq();
  }
  function render() {
    const nav=navLabels();
    document.documentElement.lang=lang;
    document.title=nav[page]+" | "+text(data.hospital.name);
    document.querySelector('meta[name="description"]').content=copy("intro");
    document.getElementById("app").innerHTML='<a href="#main" class="skip-link">'+({en:"Skip to content",hi:"मुख्य सामग्री पर जाएँ",mr:"मुख्य मजकुरावर जा"}[lang])+'</a><div class="topbar"><div class="container"><span>'+icon("map-pin")+t("location")+'</span><span class="top-message">'+t("top")+'</span>'+(data.hospital.emergency_24h?'<a href="tel:'+escape(data.hospital.phone)+'">'+t("emergency")+'</a>':"")+'</div></div><header class="site-header"><div class="container header-inner">'+brand()+'<nav aria-label="'+escape(copy("menu"))+'" id="navigation">'+routes.map((r,i)=>'<a href="'+r+'" '+(i===page?'aria-current="page"':"")+'>'+escape(nav[i])+'</a>').join("")+'</nav><div class="header-tools"><label class="language-select">'+icon("languages")+'<select id="language" aria-label="'+escape(copy("language"))+'">'+[["en","EN"],["hi","हिंदी"],["mr","मराठी"]].map(([v,label])=>'<option value="'+v+'" '+(lang===v?"selected":"")+'>'+label+'</option>').join("")+'</select></label><button class="menu-toggle" aria-label="'+escape(copy("menu"))+'" aria-controls="navigation" aria-expanded="false">'+icon("menu")+'</button></div></div></header><main id="main">'+
      [home,about,()=>department(false),()=>department(true),()=>innerHeading(t("doctorsLabel"),t("doctorPageTitle"),t("doctorPageBody"))+'<section class="section"><div class="container">'+doctorCards()+'</div></section>'+visit(),contact][page]()+
      '</main><footer><div class="container footer-grid"><div>'+brand()+'<p>'+t("footerLine")+'</p></div><div><h3>'+t("footerNav")+'</h3>'+[1,4,5].map(i=>'<a href="'+routes[i]+'">'+escape(nav[i])+'</a>').join("")+'</div><div><h3>'+t("footerCare")+'</h3><a href="/child-care/">'+t("child")+'</a><a href="/dental-care/">'+t("dental")+'</a></div><div><h3>'+t("footerContact")+'</h3><p>'+html(data.hospital.address)+'</p><button class="footer-call" data-call>'+t("call")+icon("arrow-up-right")+'</button></div></div><div class="container footer-bottom"><span>© '+new Date().getFullYear()+' '+t("rights")+'</span><span>'+t("previewNote")+'</span></div></footer><div class="mobile-call">'+call()+'</div><dialog id="call-dialog" aria-labelledby="dialog-title"><button class="dialog-close" aria-label="'+escape(copy("close"))+'">'+icon("x")+'</button><span class="dialog-icon">'+icon("phone")+'</span><h2 id="dialog-title">'+t("dialogTitle")+'</h2><p>'+t("bookingIntro")+'</p>'+appointmentLinks()+'</dialog>';
    if(window.lucide) window.lucide.createIcons({attrs:{"stroke-width":1.7}});
    document.getElementById("language").addEventListener("change",e=>{
      const y=scrollY;lang=e.target.value;
      try{localStorage.setItem("shantipad-language",lang);}catch{}
      render();document.getElementById("language").focus();scrollTo(0,y);
    });
    const toggle=document.querySelector(".menu-toggle");
    toggle.addEventListener("click",()=>{
      const open=toggle.getAttribute("aria-expanded")==="true";
      toggle.setAttribute("aria-expanded",String(!open));document.getElementById("navigation").classList.toggle("open",!open);
    });
    const dialog=document.getElementById("call-dialog");
    document.querySelectorAll("[data-call]").forEach(b=>b.addEventListener("click",()=>dialog.showModal()));
    document.querySelector(".dialog-close").addEventListener("click",()=>dialog.close());
    dialog.addEventListener("click",e=>{
      if(e.target!==dialog)return;const r=dialog.getBoundingClientRect();
      if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();
    });
  }
  async function load() {
    const app=document.getElementById("app");
    app.innerHTML='<div class="load-state" role="status">Shantipad<br><span>Loading hospital information…</span></div>';
    try {
      const response=await fetch("/api/content/",{cache:"no-store",signal:AbortSignal.timeout(10000)});
      if(!response.ok)throw new Error("Content unavailable");
      data=await response.json();
      if(!data.hospital||!data.copy)throw new Error("Incomplete content");
      render();
    } catch {
      app.innerHTML='<div class="load-state"><h1>Hospital information is unavailable</h1><p>Please try again in a moment.</p><button class="button button-primary" id="retry">Try again</button></div>';
      document.getElementById("retry").addEventListener("click",load);
    }
  }
  load();
})();
