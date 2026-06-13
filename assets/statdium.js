(function(){
"use strict";

/* ══ 1. PARTICLE NETWORK — enhanced with mouse attraction + color pulse ══ */
function initParticles(){
  if(document.getElementById('particle-canvas')) return;
  var c=document.createElement('canvas');
  c.id='particle-canvas';
  c.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;';
  document.body.appendChild(c);
  var ctx=c.getContext('2d'),W,H,pts=[];
  function resize(){W=c.width=window.innerWidth;H=c.height=window.innerHeight;}
  resize();
  window.addEventListener('resize',resize);
  var N=Math.min(70,Math.floor(window.innerWidth*window.innerHeight/14000));
  for(var i=0;i<N;i++){
    pts.push({
      x:Math.random()*W, y:Math.random()*H,
      vx:(Math.random()-.5)*.3, vy:(Math.random()-.5)*.3,
      r:Math.random()*1.6+.6,
      hue:Math.random()<.7?152:265, // mostly green, some purple
      phase:Math.random()*Math.PI*2
    });
  }
  var mx=-999,my=-999,t=0;
  document.addEventListener('mousemove',function(e){mx=e.clientX;my=e.clientY;});
  function frame(){
    t+=.008;
    ctx.clearRect(0,0,W,H);
    for(var i=0;i<pts.length;i++){
      var p=pts[i];
      // Mouse attraction
      var mdx=mx-p.x,mdy=my-p.y,md=Math.sqrt(mdx*mdx+mdy*mdy);
      if(md<180&&md>1){p.vx+=mdx/md*.025;p.vy+=mdy/md*.025;}
      // Speed cap
      var spd=Math.sqrt(p.vx*p.vx+p.vy*p.vy);
      if(spd>.65){p.vx=p.vx/spd*.65;p.vy=p.vy/spd*.65;}
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0||p.x>W)p.vx*=-1;
      if(p.y<0||p.y>H)p.vy*=-1;
      // Pulsing alpha
      var alpha=.2+.15*Math.sin(t+p.phase);
      // Draw connections
      for(var j=i+1;j<pts.length;j++){
        var q=pts[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.sqrt(dx*dx+dy*dy);
        if(d<130){
          ctx.beginPath();
          ctx.strokeStyle='rgba(0,229,160,'+(0.18*(1-d/130))+')';
          ctx.lineWidth=.7;
          ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke();
        }
      }
      // Draw dot with glow
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r*1.8,0,Math.PI*2);
      ctx.fillStyle='rgba(0,229,160,'+(alpha*.4)+')';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle='rgba(0,229,160,'+(alpha+.1)+')';
      ctx.fill();
    }
    requestAnimationFrame(frame);
  }
  frame();
}

/* ══ 2. GLOW CARD CURSOR TRACKING ════════════════════════════════════════ */
function initGlowCards(){
  document.querySelectorAll('.glow-card,.match-card,.stat-pill').forEach(function(el){
    if(el._glowInit)return;
    el._glowInit=true;
    el.addEventListener('mousemove',function(e){
      var r=el.getBoundingClientRect();
      el.style.setProperty('--mx',((e.clientX-r.left)/r.width*100)+'%');
      el.style.setProperty('--my',((e.clientY-r.top)/r.height*100)+'%');
    });
  });
}

/* ══ 3. CARD TILT ════════════════════════════════════════════════════════ */
function initTilt(){
  document.querySelectorAll('.match-card,.tilt-card').forEach(function(el){
    if(el._tiltInit)return;
    el._tiltInit=true;
    el.addEventListener('mousemove',function(e){
      var r=el.getBoundingClientRect();
      var dx=(e.clientX-r.left)/r.width-.5;
      var dy=(e.clientY-r.top)/r.height-.5;
      el.style.transform='perspective(500px) rotateX('+(dy*-6)+'deg) rotateY('+(dx*6)+'deg) translateY(-2px) scale(1.01)';
    });
    el.addEventListener('mouseleave',function(){
      el.style.transition='transform 0.45s cubic-bezier(0.22,1,0.36,1)';
      el.style.transform='';
      setTimeout(function(){el.style.transition='';},450);
    });
  });
}

/* ══ 4. COUNTUP ══════════════════════════════════════════════════════════ */
function countUp(el,target,dur){
  var t0=null,isF=String(target).indexOf('.')!==-1,dec=isF?String(target).split('.')[1].length:0;
  function step(ts){
    if(!t0)t0=ts;
    var p=Math.min((ts-t0)/dur,1),ease=1-Math.pow(1-p,3),val=ease*target;
    el.textContent=isF?val.toFixed(dec):Math.floor(val);
    if(p<1)requestAnimationFrame(step);
    else el.textContent=isF?Number(target).toFixed(dec):target;
  }
  requestAnimationFrame(step);
}
function initCountUp(){
  var obs=new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting&&!e.target._counted){
        e.target._counted=true;
        var v=parseFloat(e.target.dataset.target);
        if(!isNaN(v))countUp(e.target,v,1200);
      }
    });
  },{threshold:0.3});
  document.querySelectorAll('.countup-num[data-target]').forEach(function(el){
    if(!el._obsInit){el._obsInit=true;obs.observe(el);}
  });
}

/* ══ 5. TYPEWRITER ═══════════════════════════════════════════════════════ */
function initTypewriter(){
  var el=document.getElementById('typewriter-text');
  if(!el||el._tw)return;
  el._tw=true;
  var text=el.dataset.text||'FIFA World Cup 2026 · Live Analytics';
  var i=0;el.textContent='';
  (function type(){if(i<text.length){el.textContent+=text[i++];setTimeout(type,42+Math.random()*22);}})();
}

/* ══ 6. ACTIVE NAV ═══════════════════════════════════════════════════════ */
function updateNav(){
  var path=window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(function(a){
    var h=a.getAttribute('href');
    if(h===path||(h!=='/'&&path.startsWith(h)))a.classList.add('active');
    else a.classList.remove('active');
  });
}

/* ══ 7. BLUR-IN on page change ═══════════════════════════════════════════ */
function initPageBlur(){
  var pc=document.getElementById('page-content');
  if(!pc||pc._blurInit)return;
  pc._blurInit=true;
  new MutationObserver(function(){
    pc.classList.remove('page-blur-in');
    void pc.offsetWidth;
    pc.classList.add('page-blur-in');
    setTimeout(function(){initGlowCards();initTilt();initCountUp();updateNav();},100);
  }).observe(pc,{childList:true,subtree:false});
}

/* ══ 8. CURSOR SPOTLIGHT ════════════════════════════════════════════════ */
function initSpotlight(){
  if(document.getElementById('cursor-spotlight'))return;
  var spot=document.createElement('div');
  spot.id='cursor-spotlight';
  spot.style.cssText='position:fixed;width:400px;height:400px;border-radius:50%;pointer-events:none;z-index:0;'
    +'background:radial-gradient(circle,rgba(0,229,160,0.04) 0%,transparent 70%);'
    +'transform:translate(-50%,-50%);transition:left 0.08s,top 0.08s;';
  document.body.appendChild(spot);
  document.addEventListener('mousemove',function(e){
    spot.style.left=e.clientX+'px';
    spot.style.top=e.clientY+'px';
  });
}

/* ══ INIT ALL ════════════════════════════════════════════════════════════ */
function init(){
  initParticles();
  initGlowCards();
  initTilt();
  initCountUp();
  initTypewriter();
  updateNav();
  initPageBlur();
  initSpotlight();
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
else init();

document.addEventListener('click',function(){
  setTimeout(function(){initGlowCards();initTilt();initCountUp();updateNav();},200);
});

// Periodic refresh for Dash dynamic content
setInterval(function(){initGlowCards();initTilt();initCountUp();},2500);

})();
