/* NeuroTrace — shared UI primitives */

function Badge({ tone = 'neutral', children, dot, mono, style }) {
  const cls = { neutral: '', ok: 'badge-ok', accent: 'badge-accent', warn: 'badge-warn', danger: 'badge-danger', line: 'badge-line' }[tone] || '';
  return (
    <span className={`badge ${cls} ${mono ? 'chip-mono' : ''}`} style={style}>
      {dot && <i className="b-dot" />}
      {children}
    </span>
  );
}

function StatusBadge({ status }) {
  const map = {
    complete: ['ok', 'Complete', 'Complete'],
    review: ['warn', 'Needs review', 'Review'],
    failed: ['danger', 'Failed', 'Failed'],
    running: ['accent', 'Processing', 'Running'],
    queued: ['line', 'Queued', 'Queued'],
  };
  const [tone, label] = map[status] || ['', status, status];
  return <Badge tone={tone} dot>{label}</Badge>;
}

function Segmented({ value, options, onChange, label }) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map((o) => {
        const v = typeof o === 'string' ? o : o.value;
        const t = typeof o === 'string' ? o : o.label;
        return (
          <button key={v} aria-pressed={value === v} onClick={() => onChange(v)} type="button">{t}</button>
        );
      })}
    </div>
  );
}

function Switch({ checked, onChange, label }) {
  return (
    <button className="switch" data-on={checked} role="switch" aria-checked={checked} aria-label={label}
      onClick={() => onChange(!checked)} type="button" />
  );
}

function Check({ checked, onChange, children, label }) {
  return (
    <label className="check">
      <input type="checkbox" className="sr-only" checked={checked} onChange={(e) => onChange(e.target.checked)} aria-label={label} />
      <span className="box" data-on={checked} aria-hidden="true">{checked && <Icon name="check" stroke={2.4} />}</span>
      <span>{children}</span>
    </label>
  );
}

function Field({ label, hint, children, htmlFor }) {
  return (
    <div className="field">
      {label && <label htmlFor={htmlFor}>{label}</label>}
      {children}
      {hint && <span className="help">{hint}</span>}
    </div>
  );
}

function StatCell({ label, value, unit, meta, sub }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}{unit && <span className="unit">{unit}</span>}</div>
      {meta && <div className="stat-meta">{meta}</div>}
      {sub && <div className="stat-meta" style={{ marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function Slider({ label, value, min, max, step = 1, unit = '', onChange, format }) {
  return (
    <div className="stack" style={{ gap: 4 }}>
      <div className="hrow" style={{ justifyContent: 'space-between' }}>
        <span className="tiny" style={{ fontWeight: 500, color: 'var(--ink-2)' }}>{label}</span>
        <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-3)' }}>{format ? format(value) : `${value}${unit}`}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} aria-label={label}
        onChange={(e) => onChange(Number(e.target.value))} />
    </div>
  );
}

function EmptyState({ icon = 'scan', title, body, action }) {
  return (
    <div className="empty">
      <div className="empty-icon"><Icon name={icon} size={19} /></div>
      <div className="h2" style={{ fontSize: 16 }}>{title}</div>
      {body && <p className="small" style={{ maxWidth: 340, margin: '7px auto 0', lineHeight: 1.6 }}>{body}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}

function SkeletonLine({ w = '100%', h = 10 }) {
  return <div className="skeleton" style={{ width: w, height: h }} />;
}

/* ---------- toast ---------- */
const ToastCtx = React.createContext(() => {});
function useToast() { return React.useContext(ToastCtx); }

function ToastProvider({ children }) {
  const [items, setItems] = React.useState([]);
  const push = React.useCallback((msg, icon = 'checkCircle') => {
    const id = Math.random().toString(36).slice(2);
    setItems((prev) => [...prev, { id, msg, icon }]);
    setTimeout(() => setItems((prev) => prev.filter((i) => i.id !== id)), 3200);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toast-wrap" role="status" aria-live="polite">
        {items.map((t) => (
          <div className="toast" key={t.id}><Icon name={t.icon} size={13} />{t.msg}</div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

/* ---------- design notes drawer ---------- */
function NotesDrawer({ screenKey, onClose }) {
  const note = SCREEN_NOTES[screenKey] || SCREEN_NOTES.dashboard;
  React.useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  const blocks = [
    ['Purpose', note.purpose],
    ['Typography', note.type],
    ['Colour', note.color],
    ['Orientation & organisation', note.layout],
    ['Interaction logic', note.logic],
    ['Notes', note.notes],
  ];
  return (
    <>
      <div className="overlay" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={`Design notes for ${note.title}`}>
        <div className="drawer-head">
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Design notes</div>
            <div className="h2">{note.title}</div>
          </div>
          <button className="btn-icon" onClick={onClose} aria-label="Close design notes"><Icon name="x" /></button>
        </div>
        <div className="drawer-body">
          {blocks.map(([k, v]) => (
            <div className="note-block" key={k}>
              <span className="eyebrow">{k}</span>
              <p>{v}</p>
            </div>
          ))}
          <div className="note-block">
            <span className="eyebrow">Palette</span>
            <div className="swatch-row">
              {PALETTE_SWATCHES.map((s) => {
                const dark = document.documentElement.dataset.theme === 'dark';
                return (
                  <div className="swatch" key={s.name}>
                    <i style={{ background: dark ? s.dark : s.light }} />
                    <span>{s.name}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="note-block">
            <span className="eyebrow">Structure</span>
            <p>Serif display · neutral UI sans · mono for all metadata. Hairline rules over nested cards, 3–8 px radii, motion limited to 120–240 ms opacity and position transitions.</p>
          </div>
        </div>
      </aside>
    </>
  );
}

Object.assign(window, {
  Badge, StatusBadge, Segmented, Switch, Check, Field, StatCell, Slider,
  EmptyState, SkeletonLine, ToastProvider, useToast, ToastCtx, NotesDrawer,
});
