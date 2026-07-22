/**
 * Source-neutral React helpers for at most six meaningful design decisions.
 * The host project supplies React and its own visual tokens.
 */
const DesignTweaks = (() => {
  function validSchema(schema) {
    if (!Array.isArray(schema) || schema.length === 0 || schema.length > 6) {
      throw new Error('Tweak schema must contain between one and six controls');
    }
    const ids = new Set();
    for (const control of schema) {
      if (!control.id || ids.has(control.id)) throw new Error(`Invalid or duplicate tweak id: ${control.id}`);
      if (!['range', 'select', 'toggle', 'color'].includes(control.type)) throw new Error(`Unsupported tweak type: ${control.type}`);
      ids.add(control.id);
    }
    return schema;
  }

  function sanitize(schema, candidate, defaults) {
    const result = { ...defaults };
    for (const control of schema) {
      const value = candidate?.[control.id];
      if (control.type === 'toggle' && typeof value === 'boolean') result[control.id] = value;
      if (control.type === 'color' && /^#[0-9a-f]{6}$/i.test(String(value))) result[control.id] = value;
      if (control.type === 'select' && control.options?.some((option) => option.value === value)) result[control.id] = value;
      if (control.type === 'range' && Number.isFinite(Number(value))) {
        const numeric = Number(value);
        result[control.id] = Math.min(control.max, Math.max(control.min, numeric));
      }
    }
    return result;
  }

  function useTakes({ storageKey, schema, defaults }) {
    const controls = React.useMemo(() => validSchema(schema), [schema]);
    const [values, setValues] = React.useState(() => {
      if (typeof localStorage === 'undefined') return { ...defaults };
      try {
        const stored = JSON.parse(localStorage.getItem(storageKey) || 'null');
        return sanitize(controls, stored, defaults);
      } catch {
        return { ...defaults };
      }
    });

    React.useEffect(() => {
      if (typeof localStorage === 'undefined') return;
      localStorage.setItem(storageKey, JSON.stringify(values));
    }, [storageKey, values]);

    const update = React.useCallback((id, value) => {
      setValues((current) => sanitize(controls, { ...current, [id]: value }, defaults));
    }, [controls, defaults]);
    const reset = React.useCallback(() => setValues({ ...defaults }), [defaults]);
    const exportState = React.useCallback(() => JSON.stringify(values, null, 2), [values]);
    return { values, update, reset, exportState };
  }

  function TweakPanel({ schema, values, onChange, onReset, onExport, title = 'Design decisions' }) {
    const controls = validSchema(schema);
    return (
      <aside aria-label={title} className="design-tweak-panel">
        <header className="design-tweak-panel__header">
          <h2>{title}</h2>
          <button type="button" onClick={onReset}>Reset</button>
        </header>
        {controls.map((control) => (
          <label className="design-tweak-panel__control" key={control.id}>
            <span>{control.label}</span>
            {control.type === 'range' && (
              <span className="design-tweak-panel__range">
                <input
                  type="range"
                  min={control.min}
                  max={control.max}
                  step={control.step ?? 1}
                  value={values[control.id]}
                  onChange={(event) => onChange(control.id, Number(event.target.value))}
                />
                <output>{values[control.id]}</output>
              </span>
            )}
            {control.type === 'select' && (
              <select value={values[control.id]} onChange={(event) => onChange(control.id, event.target.value)}>
                {control.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            )}
            {control.type === 'toggle' && (
              <input type="checkbox" checked={Boolean(values[control.id])} onChange={(event) => onChange(control.id, event.target.checked)} />
            )}
            {control.type === 'color' && (
              <input type="color" value={values[control.id]} onChange={(event) => onChange(control.id, event.target.value)} />
            )}
          </label>
        ))}
        {onExport && <button type="button" onClick={() => onExport(JSON.stringify(values, null, 2))}>Export selection</button>}
      </aside>
    );
  }

  return { useTakes, TweakPanel, sanitize };
})();
