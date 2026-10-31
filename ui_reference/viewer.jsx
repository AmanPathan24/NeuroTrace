/* NeuroTrace — MRI viewer primitives */

const SERIES = {
  axial: { src: 'assets/mri-axial.png', label: 'Axial', abbr: 'AX', orient: 'R → L', slices: 176 },
  coronal: { src: 'assets/mri-coronal.png', label: 'Coronal', abbr: 'COR', orient: 'L → R', slices: 168 },
  sagittal: { src: 'assets/mri-sagittal.png', label: 'Sagittal', abbr: 'SAG', orient: 'A → P', slices: 184 },
};

/* Lesion geometry per plane, in percent of the frame — aligned to the
   synthetic tumour in each render. The overlay is an annotation of the
   segmentation, not a computed mask. */
const LESION = {
  axial: { cx: 33.4, cy: 28.6, rx: 8.6, ry: 8.0 },
  coronal: { cx: 33.6, cy: 30.4, rx: 8.0, ry: 8.4 },
  sagittal: { cx: 46.2, cy: 30.6, rx: 5.4, ry: 4.6 },
};

function SliceOverlay({ plane, show, mode, opacity }) {
  const L = LESION[plane];
  if (!show) return null;
  const isMask = mode === 'mask';
  return (
    <svg className="slice-overlay ov" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      <defs>
        <radialGradient id={`ed-${plane}`} cx="50%" cy="50%" r="50%">
          <stop offset="52%" stopColor="#7FA3B8" stopOpacity="0.36" />
          <stop offset="100%" stopColor="#7FA3B8" stopOpacity="0" />
        </radialGradient>
      </defs>
      {isMask ? (
        <g opacity={opacity}>
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx * 1.85} ry={L.ry * 1.8} fill={`url(#ed-${plane})`} />
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx} ry={L.ry} fill="#66756C" opacity="0.62" />
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx} ry={L.ry} className="ov-line-gold" opacity="0.95" />
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx * 0.52} ry={L.ry * 0.52} fill="#3B4A42" opacity="0.8" />
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx * 0.52} ry={L.ry * 0.52} className="ov-line-mauve" opacity="0.85" />
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx * 1.4} ry={L.ry * 1.35} className="ov-line" strokeDasharray="2 2" opacity="0.85" />
        </g>
      ) : (
        <g opacity={opacity}>
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx * 1.42} ry={L.ry * 1.38} className="ov-edge" strokeDasharray="3 2.5" />
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx} ry={L.ry} className="ov-contour" />
          <ellipse cx={L.cx} cy={L.cy} rx={L.rx * 0.5} ry={L.ry * 0.5} className="ov-core" />
        </g>
      )}
    </svg>
  );
}

function SlicePanel({
  studyId,
  plane, index, total, showOverlay = true, overlayMode = 'contour', overlayOpacity = 0.62,
  windowLevel = 50, zoom = 100, crosshair = true, active, onActivate, onScrub, label, children,
}) {
  const s = SERIES[plane] || SERIES.axial;
  const pos = total > 1 ? index / (total - 1) : 0;
  const L = LESION[plane] || LESION.axial;

  const activeStudy = (studyId && window.NT_ACTIVE_STUDIES && window.NT_ACTIVE_STUDIES[studyId]) || (window.NT_CURRENT_STUDY && window.NT_CURRENT_STUDY.id === studyId ? window.NT_CURRENT_STUDY : null);
  const isReal = !!(activeStudy && activeStudy.isReal);
  const imgSrc = isReal
    ? `/api/slice/${studyId}/${plane}/${index}?overlay=${showOverlay ? 1 : 0}&opacity=${overlayOpacity}&mode=${overlayMode}`
    : s.src;

  const dragRef = React.useRef(null);
  const handleScrub = (e) => {
    const el = dragRef.current;
    if (!el || !onScrub || total <= 1) return;
    const r = el.getBoundingClientRect();
    const p = Math.max(0, Math.min(1, (e.clientY - r.top) / r.height));
    onScrub(Math.round(p * (total - 1)));
  };

  const contrast = 1 + (windowLevel - 50) / 110;
  const brightness = 1 + (windowLevel - 50) / 420;

  return (
    <div className={'cell' + (active ? ' is-active' : '')} onClick={onActivate}>
      <div className="slice-wrap">
        <img
          className="slice-img"
          src={imgSrc}
          alt={`${s.label} MRI slice ${index + 1} of ${total}`}
          style={{ filter: `contrast(${contrast.toFixed(2)}) brightness(${brightness.toFixed(2)})`, transform: `scale(${(zoom / 100).toFixed(2)})` }}
          draggable="false"
        />
        {!isReal && <SliceOverlay plane={plane} show={showOverlay} mode={overlayMode} opacity={overlayOpacity} />}
        {crosshair && (
          <svg className="slice-overlay" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" aria-hidden="true" style={{ zIndex: 2 }}>
            <line x1={L.cx} y1="0" x2={L.cx} y2="100" className="ov-cross" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
            <line x1="0" y1={L.cy} x2="100" y2={L.cy} className="ov-cross" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
            <rect x={L.cx - 1.6} y={L.cy - 1.6} width="3.2" height="3.2" className="ov-box" strokeWidth="0.6" vectorEffect="non-scaling-stroke" />
          </svg>
        )}
      </div>

      <div className="viewer-badge">
        <span className="orient">{s.abbr}</span>
        <span style={{ opacity: .45 }}>·</span>
        <span>{label || s.orient}</span>
      </div>

      <div
        className="slice-slider"
        ref={dragRef}
        role="slider"
        aria-label={`${s.label} slice position`}
        aria-valuemin={1} aria-valuemax={total} aria-valuenow={index + 1}
        tabIndex={0}
        onPointerDown={(e) => { e.stopPropagation(); e.currentTarget.setPointerCapture(e.pointerId); handleScrub(e); }}
        onPointerMove={(e) => { if (e.currentTarget.hasPointerCapture(e.pointerId)) handleScrub(e); }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') { e.preventDefault(); onScrub && onScrub(Math.min(total - 1, index + 1)); }
          if (e.key === 'ArrowUp') { e.preventDefault(); onScrub && onScrub(Math.max(0, index - 1)); }
        }}
      >
        <div className="fill" style={{ height: `${pos * 100}%` }} />
        <div className="knob" style={{ top: `${pos * 100}%` }} />
      </div>

      <div className="viewer-meta">
        <span>SL {String(index + 1).padStart(3, '0')} / {total}</span>
        <span>{children || 'T1 + Gd · 3.0 T'}</span>
      </div>
    </div>
  );
}

/* Region composition bar */
function VolBar({ parts, height = 6 }) {
  const total = parts.reduce((a, p) => a + p.vol, 0);
  return (
    <div className="vol-bar" style={{ height }}>
      {parts.map((p) => (
        <i key={p.key} style={{ width: `${(p.vol / total) * 100}%`, background: p.color }}
          title={`${p.label}: ${p.vol.toFixed(2)} mL`} />
      ))}
    </div>
  );
}

/* Axis triad for the 3D stage */
function AxisTriad() {
  return (
    <svg className="axis-triad" viewBox="0 0 60 60" fill="none" aria-hidden="true">
      <circle cx="30" cy="30" r="1.6" fill="rgba(255,255,255,.5)" />
      <line x1="30" y1="30" x2="30" y2="10" stroke="#8FD2C6" strokeWidth="1" />
      <line x1="30" y1="30" x2="49" y2="41" stroke="rgba(255,255,255,.35)" strokeWidth="1" />
      <line x1="30" y1="30" x2="11" y2="41" stroke="rgba(255,255,255,.35)" strokeWidth="1" />
      <text x="30" y="7" fill="#8FD2C6" fontSize="6" fontFamily="IBM Plex Mono, monospace" textAnchor="middle">S</text>
      <text x="53" y="45" fill="rgba(255,255,255,.42)" fontSize="6" fontFamily="IBM Plex Mono, monospace">R</text>
      <text x="3" y="45" fill="rgba(255,255,255,.42)" fontSize="6" fontFamily="IBM Plex Mono, monospace">L</text>
    </svg>
  );
}

Object.assign(window, { SERIES, LESION, SliceOverlay, SlicePanel, VolBar, AxisTriad });
