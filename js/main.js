// ============================================================
// El Bolso de Esperanza — Main entry
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
  await loadData();
  
  // Render on home page
  const grid = document.getElementById('bolsos-grid');
  if (grid) {
    renderBolsosGrid(grid);
  }
  
  const blogList = document.getElementById('blog-list');
  if (blogList) {
    renderBlogList(blogList);
  }
});