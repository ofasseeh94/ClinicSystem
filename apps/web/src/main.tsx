import React from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function Foundation() {
  return <main><p className="eyebrow">PEDIATRIC CLINIC SYSTEM · M0</p>
    <h1>A foundation for better clinic care.</h1>
    <p>The repository is ready for incremental development. Patient registration is the next milestone.</p>
    <aside>Development scaffold · Synthetic data only · No clinical features enabled</aside>
  </main>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><Foundation /></React.StrictMode>);
