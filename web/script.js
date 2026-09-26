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
      a.textContent=h.textContent.replace(/^\s*\d+(?:\.\d+)?\s*/,"").trim();
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
  var btn=document.querySelector('.theme-toggle');
  if(btn){
    btn.addEventListener('click',function(){
      var root=document.documentElement;
      var dark=root.getAttribute('data-theme')==='dark';
      if(dark) root.removeAttribute('data-theme'); else root.setAttribute('data-theme','dark');
      try{localStorage.setItem('theme',dark?'light':'dark');}catch(e){}
    });
  }
})();
});