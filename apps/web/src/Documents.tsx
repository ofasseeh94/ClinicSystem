import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { DocumentPage, DocumentRecord } from '../../../packages/shared-contracts/records';
import type { EncounterPage } from '../../../packages/shared-contracts/encounters';
import { request, RequestError } from './api';
import { dateLabel, statusLabel } from './format';

export function localDateTime(value = new Date().toISOString()) { const d = new Date(value); return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16); }
export async function attachmentBlob(token: string, patientId: string, id: string) {
  const base = `/v1/patients/${patientId}/documents/${id}`;
  const ticket = await request<{ticket:string}>(token,`${base}/ticket`,{method:'POST'});
  const response = await fetch(`/api${base}/download`,{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify({ticket:ticket.ticket})});
  if (!response.ok) { let detail = 'Unable to retrieve attachment.'; try {detail = (await response.json()).detail ?? detail;} catch { /* Safe message */ } throw new Error(detail); }
  return response.blob();
}
interface Props { token:string; patientId:string; onDirty:(dirty:boolean)=>void }
export function Documents({token,patientId,onDirty}:Props) {
  const base = `/v1/patients/${patientId}`;
  const [list,setList] = useState<DocumentPage>(); const [page,setPage] = useState(1);
  const [encounters,setEncounters] = useState<EncounterPage>(); const [canWrite,setCanWrite] = useState(false);
  const [adding,setAdding] = useState(false); const [file,setFile] = useState<File>();
  const [title,setTitle] = useState(''); const [category,setCategory] = useState('lab');
  const [date,setDate] = useState(localDateTime()); const [source,setSource] = useState(''); const [encounter,setEncounter] = useState('');
  const [key,setKey] = useState(crypto.randomUUID()); const [error,setError] = useState(''); const [busy,setBusy] = useState(false);
  const [preview,setPreview] = useState<{url:string;doc:DocumentRecord}>();
  const previewRef = useRef<string | undefined>(undefined);
  const dirty = busy || (adding && !!(file || title || source));
  useEffect(()=>{onDirty(dirty);return()=>onDirty(false);},[dirty,onDirty]);
  useEffect(()=>{function warn(e:BeforeUnloadEvent){if(dirty){e.preventDefault();e.returnValue='';}}window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn);},[dirty]);
  useEffect(()=>()=>{if(previewRef.current)URL.revokeObjectURL(previewRef.current);},[]);
  async function refresh(){setList(await request<DocumentPage>(token,`${base}/documents?page=${page}`));}
  useEffect(()=>{let active=true;
    request<DocumentPage>(token,`${base}/documents?page=${page}`).then(r=>{if(active)setList(r);}).catch(e=>{if(active)setError(e.message);});
    request<EncounterPage>(token,`${base}/encounters`).then(r=>{if(active)setEncounters(r);}).catch(e=>{if(active)setError(e.message);});
    request<{roles:string[]}>(token,'/v1/session').then(r=>{if(active)setCanWrite(r.roles.some(s=>['admin','clinician','registrar'].includes(s)));}).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;};
  },[token,base,page]);
  async function upload(e:FormEvent){e.preventDefault();if(!file)return;setBusy(true);setError('');
    try {if(file.size>10*1024*1024)throw new Error('Maximum attachment size is 10 MiB.');
      const doc=await request<DocumentRecord>(token,`${base}/documents`,{method:'POST',body:JSON.stringify({request_id:key,title,category,captured_at:new Date(date).toISOString(),source,encounter_id:encounter||null})});
      await request<DocumentRecord>(token,`${base}/documents/${doc.id}/content`,{method:'PUT',headers:{'Content-Type':file.type||'application/octet-stream'},body:file});
      setAdding(false);setFile(undefined);setTitle('');setSource('');setKey(crypto.randomUUID());await refresh();
    }catch(e){setError(e instanceof Error?e.message:'Upload failed. Retry with the same fields/file.');}finally{setBusy(false);}}
  async function open(doc:DocumentRecord,download=false){setBusy(true);setError('');try{const blob=await attachmentBlob(token,patientId,doc.id);const url=URL.createObjectURL(blob);
    if(download){const a=document.createElement('a');a.href=url;a.download=`attachment-${doc.id}.${doc.mime_type==='application/pdf'?'pdf':doc.mime_type==='image/png'?'png':'jpg'}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
    else {if(previewRef.current)URL.revokeObjectURL(previewRef.current);previewRef.current=url;setPreview({url,doc});}
  }catch(e){setError(e instanceof Error?e.message:'Unable to open attachment.');}finally{setBusy(false);}}
  async function change(doc:DocumentRecord,action:'withdraw'|'rescan'){const reason=window.prompt(action==='withdraw'?'Reason for withdrawing this attachment (at least 5 characters)':'Reason for rescanning (at least 5 characters)');if(!reason||reason.trim().length<5)return;
    setBusy(true);setError('');try{await request<DocumentRecord>(token,`${base}/documents/${doc.id}/${action}`,{method:'POST',headers:{'If-Match':`"${doc.version}"`},body:JSON.stringify({reason})});if(preview?.doc.id===doc.id){if(previewRef.current)URL.revokeObjectURL(previewRef.current);previewRef.current=undefined;setPreview(undefined);}await refresh();}catch(e){setError(e instanceof RequestError?e.message:'Unable to change attachment.');await refresh();}finally{setBusy(false);}}
  return <section className="panel records-panel"><div className="panel-heading compact"><div><h3>Patient documents</h3><p className="muted">Source files linked to this patient or a dated encounter.</p></div><button className="primary" disabled={!canWrite||busy||adding} onClick={()=>{setAdding(true);setDate(localDateTime());setKey(crypto.randomUUID());}}>Upload document</button></div>
    {error&&<p role="alert" className="notice error">{error}</p>}
    {list?.scan_mode==='synthetic'&&<div className="notice"><strong>Synthetic development mode — no malware scan</strong><p>Use fictional files only. They are format-validated and encrypted; this mode cannot be enabled in production.</p><a href="/synthetic-document.png" download>Download a fictional sample attachment</a></div>}
    {adding&&<form onSubmit={upload} className="background-add"><fieldset disabled={busy}><legend>Upload PDF, PNG or JPEG (maximum 10 MiB)</legend><div className="field-grid">
      <label>Document title<input required maxLength={160} value={title} onChange={e=>{setTitle(e.target.value);setKey(crypto.randomUUID());}}/></label>
      <label>Document category<select aria-label="Document category" value={category} onChange={e=>{setCategory(e.target.value);setKey(crypto.randomUUID());}}>{['lab','imaging','letter','other'].map(s=><option key={s}>{s}</option>)}</select></label>
      <label>Document date (device local time)<input type="datetime-local" required value={date} onChange={e=>{setDate(e.target.value);setKey(crypto.randomUUID());}}/></label>
      <label>Document source<input required maxLength={500} value={source} onChange={e=>{setSource(e.target.value);setKey(crypto.randomUUID());}}/></label>
      <label>Link to encounter (recent 20)<select aria-label="Link to encounter" value={encounter} onChange={e=>{setEncounter(e.target.value);setKey(crypto.randomUUID());}}><option value="">Patient-level document</option>{encounters?.items.filter(v=>v.status!=='cancelled').map(v=><option key={v.id} value={v.id}>{dateLabel(v.occurred_at)} · {v.reason}</option>)}</select></label>
      <label>Attachment file<input type="file" required accept="application/pdf,image/png,image/jpeg" onChange={e=>{setFile(e.target.files?.[0]);setKey(crypto.randomUUID());}}/></label></div>
      <p className="hint">Original bytes are retained. Replacing a file requires a new document; withdraw incorrect records with a reason.</p><div className="actions"><button className="primary">Save attachment</button><button type="button" className="secondary" onClick={()=>{setAdding(false);setFile(undefined);setTitle('');setSource('');}}>Discard upload</button></div></fieldset></form>}
    {!list&&!error&&<p>Loading documents…</p>}{list?.total===0&&<p className="muted">No attachments recorded.</p>}
    {list?.items.map(doc=><article key={doc.id} className="history-entry document-entry"><div className="panel-heading compact"><h3 dir="auto">{doc.title}</h3><span className="chip">{statusLabel(doc.state)}</span></div><p className="muted">{dateLabel(doc.captured_at)} · {doc.category} · {doc.source} · {doc.created_by}</p><p className="hint">{doc.scan_detail}</p>{doc.withdrawal_reason&&<p>Withdrawal reason: {doc.withdrawal_reason}</p>}
      {doc.sha256&&<details><summary>File integrity and attribution</summary><p className="hash-text">SHA-256: {doc.sha256}</p><p>{doc.byte_size} bytes · {doc.mime_type} · Linked encounter: {doc.encounter_id||'None'} · v{doc.version}</p></details>}
      <div className="actions">{['ready','synthetic_ready'].includes(doc.state)&&<><button className="secondary" disabled={busy} onClick={()=>void open(doc)}>View attachment</button><button className="secondary" disabled={busy} onClick={()=>void open(doc,true)}>Download attachment</button></>}{canWrite&&['quarantined','synthetic_ready'].includes(doc.state)&&<button className="secondary" disabled={busy} onClick={()=>void change(doc,'rescan')}>Retry scan</button>}{canWrite&&doc.state!=='withdrawn'&&<button className="text-button" disabled={busy} onClick={()=>void change(doc,'withdraw')}>Withdraw document</button>}</div></article>)}
    {list&&list.total>20&&<div className="actions"><button disabled={page===1||busy||dirty} onClick={()=>setPage(page-1)}>Previous</button><span>Page {page}</span><button disabled={page*20>=list.total||busy||dirty} onClick={()=>setPage(page+1)}>Next</button></div>}
    {preview&&<section className="attachment-viewer"><div className="panel-heading"><h3>{preview.doc.title}</h3><button className="secondary" onClick={()=>{if(previewRef.current)URL.revokeObjectURL(previewRef.current);previewRef.current=undefined;setPreview(undefined);}}>Close viewer</button></div>{preview.doc.mime_type==='application/pdf'?<iframe title="Attachment PDF viewer" sandbox="" src={preview.url}/>:<img alt={`Attachment: ${preview.doc.title}`} src={preview.url}/>}</section>}
  </section>;
}
