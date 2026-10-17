import { useEffect, useState, type FormEvent } from 'react';
import type { PatientRecord, SearchResponse, Session } from '../../../packages/shared-contracts/registry';
import { request, RequestError } from './api';
import { PatientForm } from './PatientForm';
import { PatientOverview } from './PatientOverview';
import { age, dateLabel, statusLabel } from './format';
export function App() {
  const [token, setToken] = useState(''); const [key, setKey] = useState(''); const [session, setSession] = useState<Session>();
  const [result, setResult] = useState<SearchResponse>({ items: [], total: 0, page: 1, page_size: 20 });
  const [query, setQuery] = useState(''); const [patient, setPatient] = useState<PatientRecord>();
  const [view, setView] = useState<'registry' | 'create' | 'record' | 'edit'>('registry');
  const [startVisit, setStartVisit] = useState(false);
  const [encounterDirty, setEncounterDirty] = useState(false);
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [loading, setLoading] = useState(false);
  function logout() { setToken(''); setKey(''); setSession(undefined); setPatient(undefined); setResult({ items: [], total: 0, page: 1, page_size: 20 }); setQuery(''); setError(''); setNotice(''); setView('registry'); }
  useEffect(() => {
    if (!session) return; let timeout: ReturnType<typeof setTimeout>;
    const reset = () => { clearTimeout(timeout); timeout = setTimeout(logout, 20 * 60 * 1000); };
    reset(); window.addEventListener('pointerdown', reset); window.addEventListener('keydown', reset);
    return () => { clearTimeout(timeout); window.removeEventListener('pointerdown', reset); window.removeEventListener('keydown', reset); };
  }, [session]);
  async function login(e: FormEvent) {
    e.preventDefault(); setLoading(true); setError('');
    try { const info = await request<Session>(key, '/v1/session');
      const first = await request<SearchResponse>(key, '/v1/patients/search', { method: 'POST', body: JSON.stringify({ query: '' }) });
      setToken(key); setKey(''); setSession(info); setResult(first);
    } catch (e) { setError(e instanceof RequestError ? e.message : 'Unable to connect.'); } finally { setLoading(false); }
  }
  async function search(e?: FormEvent, page = 1) {
    e?.preventDefault(); setLoading(true); setError(''); setNotice('');
    try { setResult(await request<SearchResponse>(token, '/v1/patients/search', { method: 'POST', body: JSON.stringify({ query, page }) })); }
    catch (e) { setError(e instanceof RequestError ? e.message : 'Search failed.'); } finally { setLoading(false); }
  }
  async function open(id: string) {
    setLoading(true); setError(''); setNotice('');
    try { const p = await request<PatientRecord>(token, `/v1/patients/${id}`); setPatient(p); setStartVisit(false); setView('record'); }
    catch (e) { setError(e instanceof RequestError ? e.message : 'Unable to open the record.'); } finally { setLoading(false); }
  }
  function saved(p: PatientRecord, startVisit = false) { setStartVisit(startVisit); setPatient(p); setView('record'); setNotice('Saved successfully.'); }
  async function back() { if (encounterDirty && !window.confirm('Discard unsaved record entries and return to the registry?')) return; setView('registry'); setPatient(undefined); await search(); }
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [view, patient?.patient_id]);
  const date = dateLabel(new Date().toISOString());
  if (!session) return <div className="login-shell"><section className="login-intro"><div className="brand"><span className="brand-mark">+</span> Pediatric Clinic</div>
    <p className="eyebrow">A CONTINUOUS RECORD OF CARE</p><h1>Every child's story,<br/>in one place.</h1><p>Patient identity, family context, and a foundation for longitudinal pediatric care.</p><div className="login-footnote">UNITS 01–04 · CLINIC FOUNDATIONS</div></section>
    <section className="login-panel"><p className="eyebrow">STAFF WORKSPACE</p><h2>Open the clinic registry</h2><p className="muted">Use the development access key supplied by your local setup.</p>
      <form onSubmit={login}>{error && <p role="alert" className="notice error">{error}</p>}<label>Development access key<input type="password" autoComplete="off" required value={key} onChange={e => setKey(e.target.value)} /></label><button className="primary" disabled={loading}>{loading ? 'Connecting…' : 'Open registry'}</button></form>
      <div className="notice demo"><strong>Synthetic data workspace</strong><p>Use fictional patient details only. Managed staff sign-in and production release checks are pending.</p></div></section></div>;
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><span className="brand-mark">+</span> Pediatric Clinic</div><p className="nav-caption">CLINIC WORKSPACE</p><button className="nav-item active" onClick={back}><span>▦</span> Patient registry</button>
    <div className="sidebar-plan"><p className="nav-caption">IN PATIENT RECORDS</p><p>Encounters & measurements</p><p>Documents & investigations</p><p>Medication history & catalog</p><p className="nav-caption">COMING NEXT</p><p>Growth & clinical follow-up</p></div>
    <div className="sidebar-bottom"><span className="staff-dot"/> Staff session <small>{session.environment === 'production' ? 'Managed identity' : 'Synthetic development'}</small><button className="text-button" onClick={logout}>Close session</button></div></aside>
    <div className="main-shell"><header className="topbar"><span>Clinic workspace <span className="breadcrumb">/ Patient registry</span></span><span>{date}<button className="mobile-logout text-button" onClick={logout}>Close session</button></span></header><div className="development-strip">Development workspace · Fictional patients only · No clinical calculations enabled</div>
      <main className="workspace">{error && <p role="alert" className="notice error">{error}</p>}{notice && <p role="status" className="notice success">{notice}</p>}{loading && <p role="status" className="loading">Loading clinic records…</p>}
        {view === 'registry' && <><div className="page-heading"><div><p className="eyebrow">UNIT 01 · REGISTRY</p><h1>Patients</h1><p className="muted">Find an existing record or register a new patient.</p></div><button className="primary" onClick={() => { setView('create'); setNotice(''); }}>+ Register patient</button></div>
          <section className="registry-summary"><div><span className="summary-icon">↗</span><div><strong>{result.total}</strong><span>{query ? 'matching records' : 'registered patients'}</span></div></div><p>Search first to keep each child's history together.</p></section>
          <section className="panel registry-panel"><form className="search-form" onSubmit={e => search(e)}><label className="search-label"><span className="sr-only">Search patients</span><input dir="auto" value={query} maxLength={160} onChange={e => setQuery(e.target.value)} placeholder="Search name, clinic code, guardian, or phone" /></label><button className="secondary" disabled={loading}>Search</button></form>
            <div className="table-scroll"><table><thead><tr><th>Patient</th><th>Clinic code</th><th>Age / birth date</th><th>Guardian</th><th>Allergy review</th></tr></thead><tbody>{result.items.map(p => <tr key={p.patient_id}>
              <td><button className="patient-link" dir="auto" onClick={() => open(p.patient_id)}>{p.name_en || p.name_ar}</button>{p.name_en && p.name_ar && <small dir="rtl" lang="ar">{p.name_ar}</small>}</td><td><span className="code">{p.clinic_code}</span></td><td>{age(p.dob, p.dob_precision)}<small>{p.dob}</small></td><td><span dir="auto">{p.guardian_name}</span><small>{p.masked_phone}</small></td><td><span className={`chip ${p.allergy_review_status === 'no_known' ? 'green' : 'amber'}`}>{statusLabel(p.allergy_review_status)}</span></td></tr>)}</tbody></table></div>
            {result.items.length === 0 && <div className="empty-state"><span className="empty-symbol">◎</span><h3>{query ? 'No matching patients' : 'Your patient registry starts here'}</h3><p>{query ? 'Try another name, alias, clinic code, or guardian phone.' : 'Register the first fictional patient to explore this unit.'}</p></div>}
            <div className="pagination"><span>{result.total} records · Page {result.page}</span><div className="actions"><button className="secondary" disabled={result.page <= 1 || loading} onClick={() => search(undefined, result.page - 1)}>Previous</button><button className="secondary" disabled={result.page * result.page_size >= result.total || loading} onClick={() => search(undefined, result.page + 1)}>Next</button></div></div>
          </section><p className="workspace-note">Search results mask phone numbers. Complete contact details are available inside an authorized patient record.</p></>}
        {(view === 'create' || view === 'edit') && <PatientForm key={view + (patient?.patient_id ?? '')} canStartVisit={session.roles.some(r => ['admin','clinician'].includes(r))} token={token} patient={view === 'edit' ? patient : undefined} saved={saved} cancel={() => setView(view === 'edit' ? 'record' : 'registry')} openCandidate={open} />}
        {view === 'record' && patient && <PatientOverview key={patient.patient_id} token={token} patient={patient} startVisit={startVisit} onDirty={setEncounterDirty} saved={saved} back={back} edit={() => { setView('edit'); setNotice(''); }} />}
      </main></div></div>;
}
