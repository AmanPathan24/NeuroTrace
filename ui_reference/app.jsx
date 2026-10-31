/* NeuroTrace — application root */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#2C6E68",
  "typeScale": 1,
  "density": "balanced",
  "theme": "light"
}/*EDITMODE-END*/;

const ACCENTS = [
  { name: 'Teal (default)', value: '#2C6E68' },
  { name: 'Slate blue', value: '#2F5D7C' },
  { name: 'Oxblood', value: '#7A3B3B' },
  { name: 'Graphite', value: '#4A5356' },
];

const ACCENTS_DARK = {
  '#2C6E68': '#6FB2A9',
  '#2F5D7C': '#7EADC9',
  '#7A3B3B': '#C79A96',
  '#4A5356': '#A6B0B2',
};

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [theme, setTheme] = React.useState(() => localStorage.getItem(THEME_KEY) || t.theme || 'light');
  const [route, setRoute] = React.useState(() => localStorage.getItem(NAV_KEY) || 'landing');
  const [study, setStudy] = React.useState(CURRENT.id);
  const [wsTab, setWsTab] = React.useState('2d');
  const [assistantOpen, setAssistantOpen] = React.useState(false);
  const [notes, setNotes] = React.useState(false);

  /* theme */
  React.useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  /* accent + type scale + density */
  React.useEffect(() => {
    const root = document.documentElement;
    const dark = theme === 'dark';
    root.style.setProperty('--accent', dark ? (ACCENTS_DARK[t.accent] || '#6FB2A9') : t.accent);
    root.style.setProperty('--accent-ink', dark ? '#9FD3CB' : t.accent);
    root.style.setProperty('--accent-soft', dark ? 'color-mix(in oklab, ' + (ACCENTS_DARK[t.accent] || '#6FB2A9') + ' 16%, #0C1011)' : 'color-mix(in oklab, ' + t.accent + ' 8%, #FFFFFF)');
    root.style.setProperty('--step', t.typeScale);
    root.style.setProperty('--density', t.density === 'compact' ? .84 : t.density === 'comfy' ? 1.22 : 1);
  }, [t.accent, t.typeScale, t.density, theme]);

  /* keyboard shortcuts */
  React.useEffect(() => {
    const onKey = (e) => {
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if (e.altKey && (e.key === 't' || e.key === 'T')) { setTheme((th) => th === 'light' ? 'dark' : 'light'); }
      if (e.key === '?' && e.shiftKey) { setNotes((n) => !n); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const go = React.useCallback((next, studyId, tab) => {
    if (studyId) setStudy(studyId);
    if (tab) setWsTab(tab);
    if (next === 'workspace' && !tab) setWsTab((prev) => prev);
    setRoute(next);
    if (next !== 'landing') localStorage.setItem(NAV_KEY, next);
    const sc = document.querySelector('.scroll');
    if (sc) sc.scrollTop = 0;
  }, []);

  const screenKey = route === 'workspace' ? (wsTab === '3d' ? 'workspace3d' : wsTab === 'quant' ? 'quant' : 'workspace2d') : (ROUTE_META[route]?.screen || 'dashboard');

  if (route === 'landing') {
    return (
      <ToastProvider>
        <Landing go={go} theme={theme} setTheme={setTheme} />
        {notes && <NotesDrawer screenKey="landing" onClose={() => setNotes(false)} />}
        <TweaksPanel title="Tweaks">
          <TweakSection label="Colour" />
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {ACCENTS.map((a) => (
              <button key={a.value} onClick={() => setTweak('accent', a.value)} title={a.name}
                aria-label={a.name} aria-pressed={t.accent === a.value}
                style={{
                  width: 34, height: 26, borderRadius: 4, background: a.value, cursor: 'pointer',
                  border: t.accent === a.value ? '2px solid var(--ink)' : '1px solid rgba(0,0,0,.12)',
                  boxShadow: t.accent === a.value ? '0 0 0 2px rgba(255,255,255,.9) inset' : 'none',
                }} />
            ))}
          </div>
          <TweakSection label="Type scale" />
          <TweakSlider label="Scale" value={t.typeScale} min={0.9} max={1.15} step={0.05}
            onChange={(v) => setTweak('typeScale', v)} format={(v) => `${Math.round(v * 100)}%`} />
          <TweakRadio label="Density" value={t.density} options={['compact', 'balanced', 'comfy']}
            onChange={(v) => setTweak('density', v)} />
          <TweakSection label="Theme" />
          <TweakToggle label="Dark mode" value={theme === 'dark'} onChange={(v) => setTheme(v ? 'dark' : 'light')} />
          <TweakSection label="Open" />
          <TweakButton label="Enter application" onClick={() => go('dashboard')} />
        </TweaksPanel>
      </ToastProvider>
    );
  }

  return (
    <ToastProvider>
      <div className="app">
        <Rail route={route} go={go} />
        <Sidebar route={route} go={go} theme={theme} setTheme={setTheme} study={study} />
        <div className="main">
          <Topbar route={route} go={go} theme={theme} setTheme={setTheme} openNotes={() => setNotes(true)} study={study} />
          <div className="scroll">
            {route === 'dashboard' && <Dashboard go={go} study={study} setStudy={setStudy} />}
            {route === 'upload' && <Upload go={go} />}
            {route === 'workspace' && (
              <Workspace study={study} tab={wsTab} setTab={setWsTab} go={go}
                assistantOpen={assistantOpen} setAssistantOpen={setAssistantOpen} />
            )}
            {route === 'quant' && <ViewQuant study={STUDIES.find((x) => x.id === study)} />}
            {route === 'assistant' && <AssistantPage study={study} go={go} />}
            {route === 'reports' && <Reports study={study} go={go} />}
            {route === 'history' && <History go={go} setStudy={setStudy} />}
            {route === 'settings' && <Settings theme={theme} setTheme={setTheme} density={t.density} setDensity={(d) => setTweak('density', d)} />}
          </div>
        </div>
      </div>
      {notes && <NotesDrawer screenKey={screenKey} onClose={() => setNotes(false)} />}
      <TweaksPanel title="Tweaks">
        <TweakSection label="Colour" />
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {ACCENTS.map((a) => (
            <button key={a.value} onClick={() => setTweak('accent', a.value)} title={a.name}
              aria-label={a.name} aria-pressed={t.accent === a.value}
              style={{
                width: 34, height: 26, borderRadius: 4, background: a.value, cursor: 'pointer',
                border: t.accent === a.value ? '2px solid var(--ink)' : '1px solid rgba(0,0,0,.12)',
              }} />
          ))}
        </div>
        <TweakSection label="Type scale" />
        <TweakSlider label="Scale" value={t.typeScale} min={0.9} max={1.15} step={0.05}
          onChange={(v) => setTweak('typeScale', v)} format={(v) => `${Math.round(v * 100)}%`} />
        <TweakRadio label="Density" value={t.density} options={['compact', 'balanced', 'comfy']}
          onChange={(v) => setTweak('density', v)} />
        <TweakSection label="Theme" />
        <TweakToggle label="Dark mode" value={theme === 'dark'} onChange={(v) => setTheme(v ? 'dark' : 'light')} />
        <TweakSection label="Navigate" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {['dashboard', 'workspace', 'assistant', 'reports', 'landing'].map((r) => (
            <TweakButton key={r} label={r} secondary onClick={() => go(r)} />
          ))}
        </div>
        <TweakSection label="Notes" />
        <TweakButton label="Open design notes" onClick={() => setNotes(true)} />
      </TweaksPanel>
    </ToastProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
