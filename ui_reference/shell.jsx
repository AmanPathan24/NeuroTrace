/* NeuroTrace — application shell */

const THEME_KEY = 'nt.theme';
const NAV_KEY = 'nt.nav';

const RAIL_ITEMS = [
  { id: 'dashboard', label: 'Home', icon: 'home', group: 'main' },
  { id: 'upload', label: 'Upload', icon: 'upload', group: 'main' },
  { id: 'workspace', label: 'Analyse', icon: 'scan', group: 'main' },
  { id: 'assistant', label: 'Assistant', icon: 'chat', group: 'main' },
  { id: 'reports', label: 'Reports', icon: 'report', group: 'library' },
  { id: 'history', label: 'History', icon: 'history', group: 'library' },
  { id: 'settings', label: 'Settings', icon: 'settings', group: 'foot' },
];

const ROUTE_META = {
  dashboard: { section: 'Workspace', title: 'Overview', screen: 'dashboard' },
  upload: { section: 'Workspace', title: 'New analysis', screen: 'upload' },
  workspace: { section: 'Analysis', title: 'NT-2026-0148', screen: 'workspace2d' },
  quant: { section: 'Analysis', title: 'Quantitative analysis', screen: 'quant' },
  assistant: { section: 'Analysis', title: 'Research assistant', screen: 'assistant' },
  reports: { section: 'Library', title: 'Research reports', screen: 'reports' },
  history: { section: 'Library', title: 'Study history', screen: 'history' },
  settings: { section: 'Configuration', title: 'Settings', screen: 'settings' },
};

function Rail({ route, go }) {
  const main = RAIL_ITEMS.filter((i) => i.group === 'main');
  const library = RAIL_ITEMS.filter((i) => i.group === 'library');
  const foot = RAIL_ITEMS.filter((i) => i.group === 'foot');
  const btn = (i) => (
    <button key={i.id} className="rail-btn" aria-current={route === i.id ? 'page' : undefined}
      onClick={() => go(i.id)} title={i.label}>
      <Icon name={i.icon} />
      <span>{i.label}</span>
    </button>
  );
  return (
    <nav className="rail" aria-label="Primary">
      <button className="rail-logo" onClick={() => go('dashboard')} aria-label="NeuroTrace — go to overview">
        <BrandMark size={30} />
      </button>
      {main.map(btn)}
      <div className="rail-sep" />
      {library.map(btn)}
      <div className="rail-spacer" />
      {foot.map(btn)}
      <div style={{ paddingTop: 10 }}>
        <button className="rail-btn" onClick={() => go('landing')} title="Sign out">
          <Icon name="logout" />
          <span>Exit</span>
        </button>
      </div>
    </nav>
  );
}

/* ---------- contextual second panel ---------- */
function Sidebar({ route, go, theme, setTheme, study }) {
  const [pinned, setPinned] = React.useState(['NT-2026-0148', 'NT-2026-0146']);

  if (route === 'dashboard' || route === 'upload') {
    return (
      <aside className="sidebar" aria-label="Workspace">
        <div className="sidebar-head">
          <div className="eyebrow">Workspace</div>
          <div className="sidebar-title">Neuroimaging lab</div>
          <div className="small" style={{ marginTop: 5, fontSize: 11.5 }}>4 members · 1.2 TB stored</div>
        </div>
        <div className="sidebar-body">
          <div className="sidebar-group" style={{ marginTop: 4 }}>
            {[
              ['dashboard', 'Overview', 'home'],
              ['upload', 'New analysis', 'upload'],
              ['history', 'All studies', 'database'],
            ].map(([id, label, icon]) => (
              <button key={id} className="side-item" aria-current={route === id ? 'page' : undefined} onClick={() => go(id)}>
                <Icon name={icon} />{label}
                {id === 'history' && <span className="count">142</span>}
              </button>
            ))}
          </div>

          <div className="sidebar-group">
            <span className="eyebrow">Pinned studies</span>
            {pinned.map((id) => {
              const s = STUDIES.find((x) => x.id === id);
              const active = route === 'workspace' && study === id;
              return (
                <button key={id} className={'side-item' + (active ? ' is-active' : '')} onClick={() => go('workspace', id)}>
                  <Icon name="pin" style={{ opacity: .7 }} />
                  <span className="truncate" style={{ flex: 1 }}>{s.diagnosis}</span>
                  {s.status === 'review' && <span className="dot" style={{ background: 'var(--warn)' }} />}
                </button>
              );
            })}
          </div>

          <div className="sidebar-group">
            <span className="eyebrow">Processing queue</span>
            <div style={{ padding: '2px 8px' }}>
              <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 6 }}>
                <span className="small" style={{ fontSize: 11.5 }}>NT-2026-0149</span>
                <span className="tiny mono">38%</span>
              </div>
              <div className="progress"><i style={{ width: '38%' }} /></div>
              <div className="tiny" style={{ marginTop: 7 }}>Segmentation · 1 of 2 in queue</div>
            </div>
          </div>
        </div>
        <div className="sidebar-foot">
          <div className="hrow" style={{ justifyContent: 'space-between' }}>
            <span className="tiny">Storage</span>
            <span className="tiny mono">61%</span>
          </div>
          <div className="progress" style={{ marginTop: 7 }}><i style={{ width: '61%' }} /></div>
        </div>
      </aside>
    );
  }

  if (route === 'workspace' || route === 'quant' || route === 'assistant') {
    const s = STUDIES.find((x) => x.id === study) || CURRENT;
    return (
      <aside className="sidebar" aria-label="Study context">
        <div className="sidebar-head">
          <div className="eyebrow">Active study</div>
          <div className="sidebar-title" style={{ fontFamily: 'var(--font-mono)', fontSize: 13, letterSpacing: 0 }}>{s.id}</div>
          <div className="small" style={{ marginTop: 4, fontSize: 11.5 }}>{s.diagnosis}</div>
        </div>
        <div className="sidebar-body">
          <div className="sidebar-group" style={{ marginTop: 0 }}>
            {[
              ['workspace', 'Viewer · 2D', 'grid'],
              ['workspace:3d', 'Viewer · 3D', 'cube'],
              ['quant', 'Quantitative', 'ruler'],
              ['assistant', 'Research assistant', 'chat'],
              ['reports', 'Report preview', 'report'],
            ].map(([id, label, icon]) => {
              const [r, tab] = id.split(':');
              const isActive = (r === route && !tab) || (route === 'workspace' && tab && false);
              return (
                <button key={id} className={'side-item' + (isActive ? ' is-active' : '')}
                  onClick={() => go(r, study, tab)}>
                  <Icon name={icon} />{label}
                </button>
              );
            })}
          </div>

          <div className="sidebar-group">
            <span className="eyebrow">Series</span>
            {[
              ['T1 + Gd', '176 slices', true],
              ['T1 pre-contrast', '176', false],
              ['FLAIR', '176', false],
              ['T2', '176', false],
            ].map(([n, c, on]) => (
              <button key={n} className={'side-item' + (on ? ' is-active' : '')} style={{ minHeight: 30 }}>
                <Icon name="layers" />{n}
                <span className="count">{c}</span>
              </button>
            ))}
          </div>

          <div className="sidebar-group">
            <span className="eyebrow">Study details</span>
            <div style={{ padding: '0 8px' }}>
              <dl style={{ margin: 0 }}>
                {[
                  ['Patient', s.patient],
                  ['Age / sex', `${s.age} / ${s.sex}`],
                  ['Acquired', s.acquired],
                  ['Field', s.field],
                  ['Matrix', s.matrix],
                ].map(([k, v]) => (
                  <div className="kv" key={k}><dt>{k}</dt><dd>{v}</dd></div>
                ))}
              </dl>
            </div>
          </div>
        </div>
        <div className="sidebar-foot">
          <button className="side-item" onClick={() => go('settings')} style={{ padding: '6px 4px' }}>
            <Icon name={theme === 'dark' ? 'moon' : 'sun'} />
            {theme === 'dark' ? 'Dark appearance' : 'Light appearance'}
            <span className="count">⌥T</span>
          </button>
        </div>
      </aside>
    );
  }

  if (route === 'reports') {
    return (
      <aside className="sidebar" aria-label="Reports">
        <div className="sidebar-head">
          <div className="eyebrow">Library</div>
          <div className="sidebar-title">Reports</div>
        </div>
        <div className="sidebar-body">
          <div className="sidebar-group" style={{ marginTop: 4 }}>
            {[
              ['All reports', 'report', '8'],
              ['Drafts', 'edit', '2'],
              ['Awaiting signature', 'clock', '1'],
              ['Shared with me', 'share', '3'],
              ['Templates', 'file', null],
            ].map(([l, ic, c], i) => (
              <button key={l} className={'side-item' + (i === 0 ? ' is-active' : '')}>
                <Icon name={ic} />{l}{c && <span className="count">{c}</span>}
              </button>
            ))}
          </div>
          <div className="sidebar-group">
            <span className="eyebrow">Recent</span>
            {STUDIES.slice(0, 4).map((s) => (
              <button key={s.id} className="side-item" onClick={() => go('workspace', s.id)} style={{ minHeight: 32 }}>
                <Icon name="file" style={{ opacity: .6 }} />
                <span className="truncate" style={{ flex: 1 }}>{s.diagnosis}</span>
              </button>
            ))}
          </div>
        </div>
      </aside>
    );
  }

  if (route === 'history') {
    return (
      <aside className="sidebar" aria-label="Study history">
        <div className="sidebar-head">
          <div className="eyebrow">Library</div>
          <div className="sidebar-title">Study history</div>
        </div>
        <div className="sidebar-body">
          <div className="sidebar-group" style={{ marginTop: 4 }}>
            <span className="eyebrow">Saved views</span>
            {[
              ['All studies', null, '142'],
              ['Needs review', 'warn', '3'],
              ['Completed', 'ok', '136'],
              ['Failed', 'danger', '3'],
            ].map(([l, tone, c], i) => (
              <button key={l} className={'side-item' + (i === 0 ? ' is-active' : '')}>
                {tone ? <i style={{ width: 6, height: 6, borderRadius: '50%', background: `var(--${tone})`, margin: '0 4px 0 2px' }} /> : <Icon name="database" />}
                {l}<span className="count">{c}</span>
              </button>
            ))}
          </div>
          <div className="sidebar-group">
            <span className="eyebrow">Collections</span>
            {['Longitudinal glioma', 'Meningioma cohort', 'Method validation', 'Teaching set'].map((c) => (
              <button key={c} className="side-item" style={{ minHeight: 30 }}>
                <Icon name="layers" />{c}
              </button>
            ))}
          </div>
        </div>
        <div className="sidebar-foot">
          <div className="small" style={{ lineHeight: 1.5, fontSize: 11 }}>Retention: 7 years per institutional policy. Audit log available.</div>
        </div>
      </aside>
    );
  }

  // settings
  return (
    <aside className="sidebar" aria-label="Settings">
      <div className="sidebar-head">
        <div className="eyebrow">Configuration</div>
        <div className="sidebar-title">Settings</div>
      </div>
      <div className="sidebar-body">
        <div className="sidebar-group" style={{ marginTop: 4 }}>
          {[
            ['Appearance', 'contrast'],
            ['Model configuration', 'cpu'],
            ['Privacy & data', 'shield'],
            ['Notifications', 'bell'],
            ['Workspace defaults', 'settings'],
            ['Keyboard', 'terminal'],
          ].map(([l, ic], i) => (
            <button key={l} className={'side-item' + (i === 0 ? ' is-active' : '')}>
              <Icon name={ic} />{l}
            </button>
          ))}
        </div>
        <div className="sidebar-group">
          <span className="eyebrow">Account</span>
          <div style={{ padding: '2px 8px' }}>
            <div className="hrow" style={{ gap: 9 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--accent-soft)', color: 'var(--accent-ink)', display: 'grid', placeItems: 'center', fontSize: 11, fontWeight: 600 }}>AK</div>
              <div style={{ minWidth: 0 }}>
                <div className="truncate" style={{ fontSize: 12 }}>Dr A. Kessler</div>
                <div className="tiny">Research lead</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

/* ---------- topbar ---------- */
function Topbar({ route, go, theme, setTheme, openNotes, study }) {
  const meta = ROUTE_META[route] || ROUTE_META.dashboard;
  const onWorkspace = route === 'workspace';
  return (
    <header className="topbar">
      <div className="crumbs">
        <span>{meta.section}</span>
        <span className="sep">/</span>
        <span className="cur">{route === 'workspace' ? (study || CURRENT.id) : meta.title}</span>
      </div>
      <div className="topbar-spacer" />
      <div className="topbar-actions">
        <button className="btn btn-ghost btn-sm" onClick={openNotes} title="Design notes for this screen">
          <Icon name="info" size={14} />Notes
        </button>
        <div style={{ width: 1, height: 18, background: 'var(--line)', margin: '0 4px' }} />
        <div className="hrow" style={{ gap: 2, padding: 2, border: '1px solid var(--line)', borderRadius: 4, background: 'var(--sunken)' }}>
          <button className="btn-icon" style={{ width: 26, height: 24, color: theme === 'light' ? 'var(--ink)' : 'var(--ink-3)', background: theme === 'light' ? 'var(--panel)' : 'transparent' }}
            onClick={() => setTheme('light')} aria-label="Light theme" aria-pressed={theme === 'light'} title="Light"><Icon name="sun" size={14} /></button>
          <button className="btn-icon" style={{ width: 26, height: 24, color: theme === 'dark' ? 'var(--ink)' : 'var(--ink-3)', background: theme === 'dark' ? 'var(--panel)' : 'transparent' }}
            onClick={() => setTheme('dark')} aria-label="Dark theme" aria-pressed={theme === 'dark'} title="Dark"><Icon name="moon" size={14} /></button>
        </div>
        <button className="btn-icon" aria-label="Search" title="Search (/)"><Icon name="search" /></button>
        <button className="btn-icon" aria-label="Notifications" title="Notifications" style={{ position: 'relative' }}>
          <Icon name="bell" />
          <i style={{ position: 'absolute', top: 7, right: 8, width: 4, height: 4, borderRadius: '50%', background: 'var(--accent)' }} />
        </button>
        <div style={{ width: 1, height: 18, background: 'var(--line)', margin: '0 4px' }} />
        <button className="hrow" style={{ gap: 8, padding: '3px 4px' }} onClick={() => go('settings')} aria-label="Account menu">
          <div style={{ width: 26, height: 26, borderRadius: '50%', background: 'var(--accent-soft)', color: 'var(--accent-ink)', display: 'grid', placeItems: 'center', fontSize: 10.5, fontWeight: 600 }}>AK</div>
          <Icon name="chevD" size={12} style={{ color: 'var(--ink-3)' }} />
        </button>
      </div>
    </header>
  );
}

Object.assign(window, { Rail, Sidebar, Topbar, RAIL_ITEMS, ROUTE_META });
