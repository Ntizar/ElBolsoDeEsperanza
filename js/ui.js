// ============================================================
// El Bolso de Esperanza — UI helpers
// ============================================================

function renderBolsosGrid(container) {
  const grid = container || document.getElementById('bolsos-grid');
  if (!grid || !APP.loaded || APP.bolsos.length === 0) return;

  grid.innerHTML = APP.bolsos.map((b, i) => `
    <article class="bolso-card" onclick="location.href='blog/${b.slug}.html'">
      <div class="bolso-card-image">
        <img src="https://38f9cd01dec7d1d1807eace23c4f00a4.r2.cloudflarestorage.com/nan-images-prod/users/63b86175-cba7-4f20-ba97-649e0f593049/images/1790941973270116134-6364a85ed468.jpg" alt="${b.titulo}" loading="lazy" onerror="this.parentElement.style.background='linear-gradient(135deg, var(--crema-oscuro), var(--rosa-polvo))'">
        <span class="day-badge">Día ${i + 1}</span>
      </div>
      <div class="bolso-card-body">
        <div class="rating">${renderStars(b.rating || 3)}</div>
        <h3>${b.titulo}</h3>
        <p class="extracto">${b.extracto || b.resumen}</p>
        <div class="bolso-card-footer">
          <span class="bolso-card-price">${b.precio_aprox}</span>
          <a href="${getAfiliadoUrl(b)}" class="bolso-card-link" rel="sponsored nofollow noopener" target="_blank" onclick="event.stopPropagation()">Ver en Amazon ↗</a>
        </div>
      </div>
    </article>
  `).join('');
}

function renderBlogList(container) {
  const list = container || document.getElementById('blog-list');
  if (!list || !APP.loaded || APP.blog.length === 0) return;

  list.innerHTML = APP.blog.map((entry, i) => `
    <a href="blog/${entry.slug}.html" class="blog-item">
      <div class="blog-item-image">
        <img src="https://38f9cd01dec7d1d1807eace23c4f00a4.r2.cloudflarestorage.com/nan-images-prod/users/63b86175-cba7-4f20-ba97-649e0f593049/images/1790941973270116134-6364a85ed468.jpg" alt="${entry.titulo}" loading="lazy">
      </div>
      <div class="blog-item-content">
        <div class="blog-item-day handwritten">Día ${entry.dia} · ${new Date(entry.fecha).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}</div>
        <h3>${entry.titulo}</h3>
        <p>${entry.extracto}</p>
        <div class="blog-item-meta">
          Por ${entry.autor} · ${entry.leido || '2 min'} de lectura
        </div>
      </div>
    </a>
  `).join('');
}

function renderBlogPost(container, entry, bolso) {
  const post = container || document.querySelector('.blog-post');
  if (!post || !entry) return;

  post.innerHTML = `
    <div class="blog-post-date handwritten">Día ${entry.dia} · ${new Date(entry.fecha).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</div>
    <h1>${entry.titulo}</h1>
    
    <div class="blog-post-image">
      <img src="https://38f9cd01dec7d1d1807eace23c4f00a4.r2.cloudflarestorage.com/nan-images-prod/users/63b86175-cba7-4f20-ba97-649e0f593049/images/1790941973270116134-6364a85ed468.jpg" alt="${entry.titulo}">
    </div>

    <div class="blog-post-text">
      <p>${entry.resumen}</p>
      <p>
        No me voy a poner poética. No es un bolso de marca famosa ni tiene etiqueta dorada. Pero es el bolso que llevé el día que me cambié la vida.
      </p>
      <p>
        Lo compré después de pensar durante tres días enteros. Tres días mirando páginas, comparando precios, leyendo opiniones. Y al final, no fue por el diseño — fue por el peso. Cuando lo cogí en la mano, sentí que algo dentro de mí decía "sí, este es el que necesito".
      </p>
      <p>
        No sé si necesitaba un bolso o necesitaba la excusa para comprarme algo bonito después de un día terrible. Quizás eso no importa.
      </p>
      <div class="marina-voice" style="border:none; background:none; text-align:center; padding:20px 0; margin:32px 0;">
        A veces lo peor que te pasa es lo mejor que te puede comprar un bolso.
      </div>
      <p>
        Este bolso tiene tres bolsillos interiores, un cierre que no se abre solo — eso es importante, lo aprendí sobre las 11 de la noche en Gran Vía — y un forro que se limpia con un trapo húmedo. Todo lo que necesita un bolso que va a acompañarte a sitios donde no sabes si vas a volver.
      </p>
      <p>
        Lo llevo a todas partes. Al trabajo, al gym, a comer con mis amigas, a las reuniones que odio. No lo quito ni para dormir.
      </p>
    </div>

    ${bolso ? `
    <div class="producto-card">
      <span class="num">0${entry.dia}</span>
      <div>
        <h4>${bolso.titulo}</h4>
        <div class="marca">El Bolso de Esperanza · Selección</div>
        <p class="desc">${bolso.resumen}</p>
        <div class="precio">${bolso.precio_aprox}</div>
        <div class="rating">${renderStars(bolso.rating || 3)}</div>
        <a href="${getAfiliadoUrl(bolso)}" class="btn-afiliado" rel="sponsored nofollow noopener" target="_blank">Ver en Amazon ↗</a>
      </div>
    </div>
    ` : ''}

    <div style="text-align:center; margin-top:40px;">
      <a href="blog/dia-00${entry.dia}.html" style="font-size:14px; color:var(--rosa-fuerte); text-decoration:none; font-family:var(--fuente-hand); font-size:18px;">
        ← Ver el día ${entry.dia > 1 ? entry.dia - 1 : 'siguiente'}
      </a>
    </div>
  `;
}

// Smooth scroll for anchor links
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

// Nav scroll effect
function initNavScroll() {
  const nav = document.getElementById('nav');
  if (!nav) return;
  
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
}

// Animate on scroll
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.bolso-card, .blog-item, .section-center').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initSmoothScroll();
    initNavScroll();
    initScrollAnimations();
  });
} else {
  initSmoothScroll();
  initNavScroll();
  initScrollAnimations();
}