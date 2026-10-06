"use strict";
document.addEventListener("DOMContentLoaded", function(){
(function(){
  var headings=document.querySelectorAll('#article h2, #article h3');
  var lists=[document.getElementById('toc-desktop'),document.getElementById('toc-mobile')];
  var links=[];
  lists.forEach(function(root){
    if(!root) return;
    var ul=document.createElement('ul');
    headings.forEach(function(h){
      var li=document.createElement('li');
      if(h.tagName==='H3') li.className='sub';
      var a=document.createElement('a');
      a.href='#'+h.id;
      a.textContent=h.textContent.replace(/^\s*§?\s*\d+(?:\.\d+)?\s*/,"").trim();
      li.appendChild(a); ul.appendChild(li); links.push(a);
    });
    root.replaceChildren(ul);
  });
  var byId={};
  links.forEach(function(a){ var id=a.getAttribute('href').slice(1); (byId[id]=byId[id]||[]).push(a); });
  if('IntersectionObserver' in window){
    var obs=new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if(!e.isIntersecting) return;
        links.forEach(function(a){a.classList.remove('active');});
        (byId[e.target.id]||[]).forEach(function(a){a.classList.add('active');});
      });
    },{rootMargin:'-15% 0px -70% 0px'});
    headings.forEach(function(h){obs.observe(h);});
  }
})();
(function(){
  var bar=document.getElementById('bar');
  var article=document.getElementById('article');
  function updateProgress(){
    if(!bar || !article){ return; }
    var rect=article.getBoundingClientRect();
    var total=rect.height - window.innerHeight * 0.6;
    var progress=total > 0 ? (-rect.top / total) * 100 : 0;
    progress=Math.min(100,Math.max(0,progress));
    bar.style.width=progress+'%';
  }
  updateProgress();
  window.addEventListener('scroll',updateProgress,{passive:true});
  window.addEventListener('resize',updateProgress);

})();
(function(){
  var btn=document.querySelector('.theme-toggle');
  if(btn){
    btn.addEventListener('click',function(){
      var root=document.documentElement;
      var dark=root.getAttribute('data-theme')==='dark';
      if(dark) root.removeAttribute('data-theme'); else root.setAttribute('data-theme','dark');
      try{localStorage.setItem('mark-two-theme-v2',dark?'light':'dark');}catch(e){}
    });
  }
})();
});