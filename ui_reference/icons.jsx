/* NeuroTrace — icon set (stroke 1.5, 24 grid) */

const ICON_PATHS = {
  home: <><path d="M3.5 10.5 12 3.8l8.5 6.7V20a.9.9 0 0 1-.9.9H4.4a.9.9 0 0 1-.9-.9z"/><path d="M9.4 20.9v-6.2h5.2v6.2"/></>,
  scan: <><path d="M3.8 8V5.6c0-1 .8-1.8 1.8-1.8H8M16 3.8h2.4c1 0 1.8.8 1.8 1.8V8M20.2 16v2.4c0 1-.8 1.8-1.8 1.8H16M8 20.2H5.6c-1 0-1.8-.8-1.8-1.8V16"/><circle cx="12" cy="12" r="3.4"/></>,
  history: <><circle cx="12" cy="12" r="8.4"/><path d="M12 7.2V12l3.2 2"/></>,
  chat: <><path d="M4 5.4h16v10.4H8.6L4 19.6z"/><path d="M8.4 10.6h.1M12 10.6h.1M15.6 10.6h.1" strokeLinecap="round" strokeWidth="2"/></>,
  report: <><path d="M6.2 3.6h7.4l4.2 4.2v12.6H6.2z"/><path d="M13.6 3.6v4.2h4.2"/><path d="M9 12.4h6M9 15.6h6M9 18.2h3.6"/></>,
  settings: <><path d="M4 7.5h9M17.5 7.5H20M4 16.5h4M12 16.5h8"/><circle cx="15.2" cy="7.5" r="2.2"/><circle cx="9.8" cy="16.5" r="2.2"/></>,
  upload: <><path d="M12 16.4V3.9M7.4 8.5 12 3.9l4.6 4.6"/><path d="M4 16v3.4c0 .8.7 1.4 1.5 1.4h13c.8 0 1.5-.6 1.5-1.4V16"/></>,
  search: <><circle cx="11" cy="11" r="6.2"/><path d="M20 20l-4.4-4.4"/></>,
  bell: <><path d="M6.4 9.4a5.6 5.6 0 0 1 11.2 0c0 4.6 1.8 5.8 1.8 5.8H4.6s1.8-1.2 1.8-5.8z"/><path d="M10 18.8a2.1 2.1 0 0 0 4 0"/></>,
  sun: <><circle cx="12" cy="12" r="3.8"/><path d="M12 2.8v2.2M12 19v2.2M4.2 12H2M22 12h-2.2M6.5 6.5 5 5M19 19l-1.5-1.5M17.5 6.5 19 5M5 19l1.5-1.5" strokeLinecap="round"/></>,
  moon: <><path d="M20.2 14.6A8.6 8.6 0 0 1 9.4 3.8a8.6 8.6 0 1 0 10.8 10.8z"/></>,
  chevR: <path d="M9.4 5.4 16 12l-6.6 6.6"/>,
  chevD: <path d="M5.4 9.4 12 16l6.6-6.6"/>,
  chevL: <path d="M14.6 5.4 8 12l6.6 6.6"/>,
  chevU: <path d="M5.4 14.6 12 8l6.6 6.6"/>,
  arrowR: <><path d="M3.8 12h16M13.6 5.8 20 12l-6.4 6.2"/></>,
  arrowL: <><path d="M20.2 12h-16M10.4 5.8 4 12l6.4 6.2"/></>,
  arrowUR: <><path d="M7 17 17 7M8.4 7H17v8.6"/></>,
  check: <path d="M4.4 12.4 9.6 17.6 19.8 6.6"/>,
  checkCircle: <><circle cx="12" cy="12" r="8.6"/><path d="M8.2 12.2 11 15l5-5.6"/></>,
  x: <path d="M6 6l12 12M18 6 6 18"/>,
  plus: <path d="M12 5v14M5 12h14"/>,
  move: <><path d="M12 3.4v17.2M3.4 12h17.2"/><path d="M9.6 5.8 12 3.4l2.4 2.4M9.6 18.2 12 20.6l2.4-2.4M5.8 9.6 3.4 12l2.4 2.4M18.2 9.6 20.6 12l-2.4 2.4"/></>,
  minus: <path d="M5 12h14"/>,
  download: <><path d="M12 3.8v11.4M7.4 10.8 12 15.4l4.6-4.6"/><path d="M4 16.4v2.8c0 .9.7 1.6 1.6 1.6h12.8c.9 0 1.6-.7 1.6-1.6v-2.8"/></>,
  share: <><circle cx="17.6" cy="6" r="2.6"/><circle cx="6.4" cy="12" r="2.6"/><circle cx="17.6" cy="18" r="2.6"/><path d="M8.7 10.8 15.3 7.2M8.7 13.2l6.6 3.6"/></>,
  filter: <path d="M3.8 6.4h16.4M6.8 12h10.4M10 17.6h4"/>,
  grid: <><path d="M3.8 3.8h7v7h-7zM13.2 3.8h7v7h-7zM3.8 13.2h7v7h-7zM13.2 13.2h7v7h-7z"/></>,
  cube: <><path d="M12 3.2 20 7.8v8.4L12 20.8 4 16.2V7.8z"/><path d="M4 7.8 12 12.4l8-4.6M12 12.4v8.4"/></>,
  ruler: <><path d="M3.4 9.6 9.6 3.4 20.6 14.4 14.4 20.6z"/><path d="M7.4 9.2l1.8 1.8M10 6.6l1.8 1.8M12.6 12l1.8 1.8M15.2 14.6l1.8 1.8"/></>,
  layers: <><path d="M12 3.4 3.6 8 12 12.6 20.4 8z"/><path d="M3.6 13 12 17.6 20.4 13"/></>,
  zoomIn: <><circle cx="10.8" cy="10.8" r="6.2"/><path d="M19.8 19.8l-4.3-4.3M10.8 8.2v5.2M8.2 10.8h5.2"/></>,
  zoomOut: <><circle cx="10.8" cy="10.8" r="6.2"/><path d="M19.8 19.8l-4.3-4.3M8.2 10.8h5.2"/></>,
  rotate: <><path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20 3.8v5h-5"/></>,
  play: <path d="M8.4 5.4v13.2L19 12z" fill="currentColor" stroke="none"/>,
  pause: <><path d="M8.6 5v14M15.4 5v14" strokeWidth="2.4"/></>,
  more: <><circle cx="5.6" cy="12" r="1.3" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none"/><circle cx="18.4" cy="12" r="1.3" fill="currentColor" stroke="none"/></>,
  alert: <><path d="M12 3.8 21.4 20H2.6z"/><path d="M12 9.6v4.8M12 17.2v.4" strokeLinecap="round"/></>,
  info: <><circle cx="12" cy="12" r="8.6"/><path d="M12 11v5.4M12 7.8v.4" strokeLinecap="round"/></>,
  clock: <><circle cx="12" cy="12" r="8.4"/><path d="M12 7v5.2l3.4 2"/></>,
  copy: <><path d="M8.4 8.4h-3a1 1 0 0 0-1 1v10.2a1 1 0 0 0 1 1h10.2a1 1 0 0 0 1-1v-3"/><path d="M9.4 3.4h10.2a1 1 0 0 1 1 1v10.2a1 1 0 0 1-1 1H9.4a1 1 0 0 1-1-1V4.4a1 1 0 0 1 1-1z"/></>,
  trash: <><path d="M4.4 6.8h15.2M9.4 6.8V4.4h5.2v2.4M6.4 6.8 7.2 20a1 1 0 0 0 1 .9h7.6a1 1 0 0 0 1-.9l.8-13.2"/></>,
  edit: <><path d="M4 20h4.2L20 8.2 15.8 4 4 15.8z"/><path d="M13.6 6.2 17.8 10.4"/></>,
  eye: <><path d="M2.4 12S5.8 5.8 12 5.8 21.6 12 21.6 12 18.2 18.2 12 18.2 2.4 12 2.4 12z"/><circle cx="12" cy="12" r="2.8"/></>,
  lock: <><path d="M5.6 10.4h12.8v9.4H5.6z"/><path d="M8.4 10.4V7.8a3.6 3.6 0 0 1 7.2 0v2.6"/></>,
  shield: <><path d="M12 3.4 19.2 6v6.2c0 4.8-3.8 7.6-7.2 8.4-3.4-.8-7.2-3.6-7.2-8.4V6z"/><path d="M9 12.2 11.2 14.4 15 10"/></>,
  database: <><ellipse cx="12" cy="6.2" rx="7.6" ry="2.8"/><path d="M4.4 6.2v11.6c0 1.6 3.4 2.8 7.6 2.8s7.6-1.2 7.6-2.8V6.2"/><path d="M4.4 12c0 1.6 3.4 2.8 7.6 2.8s7.6-1.2 7.6-2.8"/></>,
  cpu: <><path d="M6.4 6.4h11.2v11.2H6.4z"/><path d="M9.8 9.8h4.4v4.4H9.8z"/><path d="M9.4 3.4v3M14.6 3.4v3M9.4 17.6v3M14.6 17.6v3M3.4 9.4h3M3.4 14.6h3M17.6 9.4h3M17.6 14.6h3"/></>,
  terminal: <><path d="M3.6 5.2h16.8v13.6H3.6z"/><path d="M7.2 9.4 9.6 11.8 7.2 14.2M12.4 14.4h4"/></>,
  file: <><path d="M6.2 3.6h7.4l4.2 4.2v12.6H6.2z"/><path d="M13.6 3.6v4.2h4.2"/></>,
  book: <><path d="M4 4.6h6.2c1 0 1.8.8 1.8 1.8v13c0-1-.8-1.8-1.8-1.8H4z"/><path d="M20 4.6h-6.2c-1 0-1.8.8-1.8 1.8v13c0-1 .8-1.8 1.8-1.8H20z"/></>,
  maximize: <path d="M4 9V4h5M20 15v5h-5M15 4h5v5M9 20H4v-5"/>,
  refresh: <><path d="M20 12a8 8 0 0 1-13.7 5.6L4 15.4"/><path d="M4 12A8 8 0 0 1 17.7 6.4L20 8.6"/><path d="M20 4.2v4.4h-4.4M4 19.8v-4.4h4.4"/></>,
  external: <><path d="M14 4.4h5.6V10"/><path d="M19.6 4.4 11 13"/><path d="M18 13.4v5.2a1 1 0 0 1-1 1H5.4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5.2"/></>,
  calendar: <><path d="M4 6.4h16v14H4z"/><path d="M4 10.4h16M8.4 3.6v4M15.6 3.6v4"/></>,
  user: <><circle cx="12" cy="8.4" r="3.6"/><path d="M4.8 20.4c0-3.4 3.2-5.6 7.2-5.6s7.2 2.2 7.2 5.6"/></>,
  contrast: <><circle cx="12" cy="12" r="8.4"/><path d="M12 3.6v16.8a8.4 8.4 0 0 0 0-16.8z" fill="currentColor" stroke="none"/></>,
  crosshair: <><circle cx="12" cy="12" r="7.4"/><path d="M12 2.6v3.4M12 18v3.4M2.6 12H6M18 12h3.4"/></>,
  quote: <><path d="M9.4 6.4H5.2v5.2h4.2v3.6c0 1.4-1.2 2.4-2.8 2.4M19.8 6.4h-4.2v5.2h4.2v3.6c0 1.4-1.2 2.4-2.8 2.4"/></>,
  link: <><path d="M9.6 14.4 14.4 9.6"/><path d="M11.6 7.2l1.8-1.8a3.8 3.8 0 0 1 5.4 5.4l-1.8 1.8M12.4 16.8l-1.8 1.8a3.8 3.8 0 0 1-5.4-5.4l1.8-1.8"/></>,
  logout: <><path d="M14.4 4.4H5.6a1 1 0 0 0-1 1v13.2a1 1 0 0 0 1 1h8.8"/><path d="M16.4 8.2 20.2 12l-3.8 3.8M10 12h10"/></>,
  pin: <><path d="M12 3.6a5.6 5.6 0 0 1 3.2 10.2V21l-3.2-2.4L8.8 21v-7.2A5.6 5.6 0 0 1 12 3.6z"/></>,
  save: <><path d="M5.2 3.8h11.2l3.4 3.4v13H5.2z"/><path d="M8.6 3.8v5h6.4v-5M8.6 20.2v-6h6.8v6"/></>,
  wand: <><path d="M4 20 15.4 8.6M13.2 6.4 16 3.6M17.6 10.8 20.4 8M8.2 4.2l.8 1.8 1.8.8-1.8.8-.8 1.8-.8-1.8-1.8-.8 1.8-.8z"/></>,
  brain: <><path d="M12 4.4v15.2"/><path d="M12 5.4C10.6 4 8.2 4.2 7.4 5.8 5.6 5.8 4.4 7.4 4.8 8.8 3.6 9.8 3.8 11.8 5 12.6c-.6 1.6.6 3.2 2.2 3.2.2 1.8 2 2.8 3.6 2h1.2"/><path d="M12 5.4c1.4-1.4 3.8-1.2 4.6.4 1.8 0 3 1.6 2.6 3 1.2 1 1 3-.2 3.8.6 1.6-.6 3.2-2.2 3.2-.2 1.8-2 2.8-3.6 2H12"/></>,
};

function Icon({ name, size, stroke = 1.5, style, className }) {
  const p = ICON_PATHS[name];
  if (!p) return null;
  return (
    <svg viewBox="0 0 24 24" width={size || 16} height={size || 16} fill="none"
      stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round"
      style={style} className={className} aria-hidden="true">{p}</svg>
  );
}

/* Wordmark — cross-section glyph built from circles and a rule */
function BrandMark({ size = 22 }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" aria-hidden="true">
      <circle cx="12" cy="12" r="9" strokeWidth="1.2" opacity=".38" />
      <circle cx="12" cy="12" r="5.4" strokeWidth="1.5" />
      <path d="M12 2.6v4.4M12 17v4.4M2.6 12h4.4M17 12h4.4" strokeWidth="1.2" opacity=".55" />
      <circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none" />
    </svg>
  );
}

function Brand({ onClick, size = 17 }) {
  return (
    <button className="brand" onClick={onClick} style={{ fontFamily: 'var(--font-display)', fontSize: size }} aria-label="NeuroTrace home">
      <span className="brand-mark"><BrandMark size={size + 6} /></span>
      <span>NeuroTrace</span>
    </button>
  );
}

Object.assign(window, { Icon, ICON_PATHS, BrandMark, Brand });
