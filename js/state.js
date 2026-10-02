// ============================================================
// El Bolso de Esperanza — estado global
// ============================================================

const APP = {
  tag: 'nti0c8-21',
  baseUrl: window.location.origin,
  bolsos: [],
  blog: [],
  loaded: false
};

async function loadData() {
  if (APP.loaded) return APP;
  
  try {
    const [bolsosRes, blogRes] = await Promise.all([
      fetch('data/bolsos.json').then(r => r.json()),
      fetch('data/blog.json').then(r => r.json())
    ]);
    APP.bolsos = bolsosRes.bolsos;
    APP.blog = blogRes.entradas;
    APP.loaded = true;
  } catch (e) {
    console.error('Error cargando datos:', e);
  }
  return APP;
}

function getBolsoBySlug(slug) {
  return APP.bolsos.find(b => b.slug === slug);
}

function getBolsosByTag(tag) {
  return APP.bolsos.filter(b => {
    const url = b.afiliado || b.busqueda;
    return url && url.includes(tag);
  });
}

function renderStars(rating) {
  let html = '';
  for (let i = 1; i <= 5; i++) {
    html += `<span class="rating-star${i > rating ? ' empty' : ''}">★</span>`;
  }
  return html;
}

function getAfiliadoUrl(bolso) {
  if (bolso.afiliado) {
    // Already has tag
    return bolso.afiliado;
  }
  if (bolso.busqueda) {
    // Add tag to search URL
    return bolso.busqueda;
  }
  return '#';
}

// Load data on init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadData);
} else {
  loadData();
}