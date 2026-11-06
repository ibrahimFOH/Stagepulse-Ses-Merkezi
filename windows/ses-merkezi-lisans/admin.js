(() => {
  'use strict';
  const SUPABASE_URL = 'https://itasctyjzyewcykozuex.supabase.co';
  const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_tP3CMhVAjv6FNtrkYfVEOA_dbF9m8Jb';
  const EDGE_FUNCTION = 'ses-merkezi-desktop';
  const ADMIN_LOGIN_URL = SUPABASE_URL + '/functions/v1/admin-login';
  const EDUCATION_FUNCTION = 'sesm-education-admin';
  const EDUCATION_BUCKET = 'sesm-education-pdfs';
  let adminToken = sessionStorage.getItem('stagepulse_sesm_admin_token') || '';
  let adminRefreshToken = sessionStorage.getItem('stagepulse_sesm_refresh_token') || '';
  let adminUsername = sessionStorage.getItem('stagepulse_sesm_admin_username') || '';
  const el = (id) => document.getElementById(id);
  const loginView = el('loginView'), appView = el('appView'), loginForm = el('loginForm'), licenseForm = el('licenseForm');
  const loginMessage = el('loginMessage'), globalMessage = el('globalMessage'), licenseList = el('licenseList'), auditList = el('auditList');
  const issuedKeyPanel = el('issuedKeyPanel'), issuedKey = el('issuedKey'), activationDialog = el('activationDialog');
  let client = null, currentUser = null, licenses = [], auditEvents = [], busy = false;
  const errors = {
    UNAUTHENTICATED:'Oturumun süresi dolmuş. Yeniden giriş yap.', FORBIDDEN_OWNER_ONLY:'Bu hesap lisans yönetimi yetkisine sahip değil. Stagepulse sahibi hesabıyla giriş yap.',
    LICENSE_LIST_FAILED:'Lisans listesi alınamadı.', LICENSE_ACTIVATION_LIST_FAILED:'Cihaz listesi alınamadı.', LICENSE_CREATE_FAILED:'Lisans oluşturulamadı.',
    LICENSE_PAYMENT_DATA_INVALID:'Ödeme bilgileri geçersiz.', LICENSE_CUSTOMER_EMAIL_INVALID:'Müşteri e-posta adresi geçersiz.', LICENSE_NOT_FOUND:'Lisans bulunamadı veya yetkin yok.',
    LICENSE_DISABLED:'İptal edilmiş lisansın süresi uzatılamaz.', LICENSE_LIFETIME_CANNOT_EXTEND:'Süresiz lisans uzatılamaz.', LICENSE_EXTENSION_INVALID:'Uzatma 1 ile 3650 gün arasında olmalı.',
    ACTIVATION_NOT_FOUND:'Cihaz etkinleştirmesi bulunamadı.', ACTIVATION_REVOKE_FAILED:'Cihaz kaldırılamadı.', AUDIT_LIST_FAILED:'İşlem geçmişi alınamadı.', STUDENT_INPUT_INVALID:'Öğrenci adı, e-posta, parola ve lisansı kontrol et.', STUDENT_LICENSE_INVALID:'Öğrenci için ödenmiş, aktif ve süresi geçmemiş bir lisans gerekli.', STUDENT_EMAIL_EXISTS:'Bu e-posta ile bir hesap zaten var.', STUDENT_CREATE_FAILED:'Öğrenci hesabı oluşturulamadı.', STUDENT_PROFILE_CREATE_FAILED:'Öğrenci profili oluşturulamadı.', STUDENT_NOT_FOUND:'Öğrenci hesabı bulunamadı.', PASSWORD_POLICY_INVALID:'Parola en az 10 karakter, harf ve rakam içermeli.', STUDENT_PASSWORD_RESET_FAILED:'Öğrenci parolası yenilenemedi.', STUDENT_DELETE_FAILED:'Öğrenci hesabı silinemedi.', EXAM_INPUT_INVALID:'Sınav alanlarını kontrol et.', EXAM_CREATE_FAILED:'Sınav oluşturulamadı.', EXAM_NOT_FOUND:'Sınav bulunamadı.', QUESTION_INPUT_INVALID:'Soru alanlarını kontrol et.', QUESTION_ANSWER_INVALID:'Soru türüne uygun doğru cevap gir.', DOCUMENT_INPUT_INVALID:'PDF bilgilerini ve dosya boyutunu kontrol et.', DOCUMENT_FILE_NOT_FOUND:'Yüklenen PDF depoda bulunamadı.', DOCUMENT_REGISTER_FAILED:'PDF kaydı oluşturulamadı.', DOCUMENT_PUBLISH_FAILED:'PDF yayın durumu değiştirilemedi.', DOCUMENT_NOT_FOUND:'PDF kaydı bulunamadı.'
  };
  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const errorText = (e) => errors[e && e.code] || errors[e && e.message] || (e && e.message) || 'Beklenmeyen hata.';
  const showMessage = (node, message, type) => { node.textContent = message || ''; node.classList.remove('error','success'); if(type) node.classList.add(type); };
  const connection = (message, state) => { const n=el('connectionStatus'); n.lastElementChild.textContent=message; n.classList.toggle('connection-error',state==='bad'); const d=n.querySelector('.status-dot'); d.style.background=state==='bad'?'var(--red)':state==='busy'?'var(--amber)':'var(--green)'; };
  const date = v => { if(!v)return 'Süresiz'; const d=new Date(v); return Number.isNaN(d.getTime())?'Bilinmiyor':new Intl.DateTimeFormat('tr-TR',{dateStyle:'medium'}).format(d); };
  const dateTime = v => { if(!v)return 'Bilinmiyor'; const d=new Date(v); return Number.isNaN(d.getTime())?'Bilinmiyor':new Intl.DateTimeFormat('tr-TR',{dateStyle:'short',timeStyle:'short'}).format(d); };
  const money = (v,c='TRY') => { try{return new Intl.NumberFormat('tr-TR',{style:'currency',currency:c}).format(Number(v||0));}catch{return String(Number(v||0))+' '+esc(c);} };
  const planName = p => ({student:'Bireysel öğrenci',classroom:'Sınıf / kurum',lifetime:'Süresiz kullanım'}[p]||p||'Lisans');
  const methodName = p => ({cash:'Elden nakit',bank_transfer:'Havale / EFT',card:'Kart / POS',other:'Diğer'}[p]||p||'Belirtilmedi');
  const paymentName = p => ({paid:'Ödendi',unpaid:'Ödeme bekliyor',refunded:'İade edildi'}[p]||p||'Bilinmiyor');
  function status(l){ if(!l.is_active)return {key:'revoked',label:'İptal edildi',cls:'status-revoked'}; if(l.payment_status==='refunded')return {key:'refunded',label:'İade edildi',cls:'status-refunded'}; if(l.payment_status!=='paid')return {key:'unpaid',label:'Ödeme bekliyor',cls:'status-pending'}; if(l.expires_at&&Date.parse(l.expires_at)<=Date.now())return {key:'expired',label:'Süresi dolmuş',cls:'status-expired'}; return {key:'active',label:'Aktif',cls:'status-active'}; }
  function getClient(){
    if(!window.supabase||typeof window.supabase.createClient!=='function')throw new Error('Gerekli bağlantı bileşeni yüklenemedi. İnternet bağlantısını kontrol et.');
    if(!client){
      client=window.supabase.createClient(SUPABASE_URL,SUPABASE_PUBLISHABLE_KEY,{auth:{persistSession:false,autoRefreshToken:true,detectSessionInUrl:false}});
      client.auth.onAuthStateChange((_event,session)=>{
        if(session){adminToken=session.access_token||'';adminRefreshToken=session.refresh_token||'';sessionStorage.setItem('stagepulse_sesm_admin_token',adminToken);sessionStorage.setItem('stagepulse_sesm_refresh_token',adminRefreshToken);}
      });
    }
    return client;
  }
  async function invoke(action,payload){ const response=await fetch(SUPABASE_URL+'/functions/v1/'+EDGE_FUNCTION,{method:'POST',headers:{'Content-Type':'application/json','apikey':SUPABASE_PUBLISHABLE_KEY,'Authorization':'Bearer '+adminToken},body:JSON.stringify(Object.assign({action:action},payload||{}))}); const data=await response.json().catch(()=>({error:'Sunucudan geçersiz yanıt geldi.'})); if(!response.ok||data.ok!==true)throw new Error(errors[data.error]||data.error||'Sunucu isteği başarısız ('+response.status+').'); return data; }
  async function loginWithCustomCredentials(username,password){
    const response=await fetch(ADMIN_LOGIN_URL,{method:'POST',headers:{'Content-Type':'application/json','apikey':SUPABASE_PUBLISHABLE_KEY},body:JSON.stringify({username:username,password:password})});
    const data=await response.json().catch(()=>({error:'Sunucudan geçersiz yanıt geldi.'}));
    if(!response.ok||!data.session||!data.session.access_token||!data.session.refresh_token)throw new Error(data.error||'Kullanıcı adı veya şifre hatalı.');
    const sessionResult=await getClient().auth.setSession({access_token:data.session.access_token,refresh_token:data.session.refresh_token});
    if(sessionResult.error||!sessionResult.data.session)throw new Error('Yönetici oturumu başlatılamadı.');
    adminToken=sessionResult.data.session.access_token;adminRefreshToken=sessionResult.data.session.refresh_token;adminUsername=data.user&&data.user.username||username;
    sessionStorage.setItem('stagepulse_sesm_admin_token',adminToken);sessionStorage.setItem('stagepulse_sesm_refresh_token',adminRefreshToken);sessionStorage.setItem('stagepulse_sesm_admin_username',adminUsername);
    return data;
  }
  async function verifyOwner(){ if(!adminToken)return false; currentUser={email:adminUsername}; const c=await invoke('context',{device_hash:''}); if(c.role!=='owner'){logoutCustom();currentUser=null;throw new Error(errors.FORBIDDEN_OWNER_ONLY);} return true; }
  function logoutCustom(){adminToken='';adminRefreshToken='';adminUsername='';sessionStorage.removeItem('stagepulse_sesm_admin_token');sessionStorage.removeItem('stagepulse_sesm_refresh_token');sessionStorage.removeItem('stagepulse_sesm_admin_username');if(client)client.auth.signOut().catch(()=>{});}
  function showLogin(){appView.classList.add('hidden');loginView.classList.remove('hidden');el('signOutButton').classList.add('hidden');currentUser=null;licenses=[];auditEvents=[];}
  function showApp(){loginView.classList.add('hidden');appView.classList.remove('hidden');el('signOutButton').classList.remove('hidden');el('currentUser').textContent=currentUser&&currentUser.email||'';}
  function visible(){const q=el('licenseSearch').value.trim().toLocaleLowerCase('tr-TR'), f=el('licenseFilter').value;return licenses.filter(l=>{const s=status(l), text=[l.customer_name,l.customer_email,l.label,l.plan_code,l.id].join(' ').toLocaleLowerCase('tr-TR');return(!q||text.includes(q))&&(f==='all'||s.key===f);});}
  function renderStats(){el('statTotal').textContent=String(licenses.length);el('statActive').textContent=String(licenses.filter(l=>status(l).key==='active').length);el('statPending').textContent=String(licenses.filter(l=>status(l).key==='unpaid').length);el('statRevenue').textContent=money(licenses.filter(l=>l.payment_status==='paid').reduce((n,l)=>n+Number(l.amount||0),0));}
  function renderLicenses(){const rows=visible();if(!rows.length){licenseList.innerHTML='<div class="empty-state">'+(licenses.length?'Bu filtreyle eşleşen lisans yok.':'Henüz lisans kaydı yok. İlk kaydı yukarıdaki formdan oluştur.')+'</div>';return;} licenseList.innerHTML=rows.map(l=>{const s=status(l), active=Number(l.active_activations||0), max=Number(l.max_activations||1), a=[]; if(s.key==='unpaid')a.push('<button class="button button-success button-small" data-action="mark-paid" data-id="'+esc(l.id)+'" type="button">Ödeme alındı</button>'); if(s.key==='active'&&l.expires_at){a.push('<button class="button button-outline button-small" data-action="extend" data-days="30" data-id="'+esc(l.id)+'" type="button">+30 gün</button>','<button class="button button-outline button-small" data-action="extend" data-days="365" data-id="'+esc(l.id)+'" type="button">+1 yıl</button>');} if(s.key==='active'||s.key==='unpaid')a.push('<button class="button button-quiet button-small" data-action="activations" data-id="'+esc(l.id)+'" type="button">Cihazlar ('+active+')</button>'); if(s.key==='active')a.push('<button class="button button-danger button-small" data-action="refund" data-id="'+esc(l.id)+'" type="button">İade</button>','<button class="button button-danger button-small" data-action="revoke" data-id="'+esc(l.id)+'" type="button">İptal et</button>'); if(s.key==='unpaid')a.push('<button class="button button-danger button-small" data-action="revoke" data-id="'+esc(l.id)+'" type="button">İptal et</button>'); return '<article class="license-card"><div class="license-card-head"><div><h3>'+esc(l.customer_name||l.label||'İsimsiz müşteri')+'</h3><p class="customer-email">'+esc(l.customer_email||l.label||'E-posta belirtilmedi')+'</p></div><span class="status-badge '+s.cls+'">'+s.label+'</span></div><div class="license-meta"><div class="meta-item"><span>Lisans türü</span><strong>'+esc(planName(l.plan_code))+'</strong></div><div class="meta-item"><span>Ücret / kayıt</span><strong>'+money(l.amount,l.currency||'TRY')+'</strong></div><div class="meta-item"><span>Ödeme</span><strong>'+esc(paymentName(l.payment_status)+' · '+methodName(l.payment_method))+'</strong></div><div class="meta-item"><span>Bitiş tarihi</span><strong>'+esc(date(l.expires_at))+'</strong></div><div class="meta-item"><span>Etkin cihaz</span><strong>'+active+' / '+max+'</strong></div><div class="meta-item"><span>Satış tarihi</span><strong>'+esc(date(l.created_at))+'</strong></div></div>'+(l.payment_reference?'<p class="audit-detail">Satış notu: '+esc(l.payment_reference)+'</p>':'')+'<div class="license-actions">'+(a.join('')||'<span class="small-note">Bu kayıt için işlem yok.</span>')+'</div><div class="license-id">Kayıt: '+esc(l.id)+'</div></article>';}).join('');}
  const auditNames={license_created:'Lisans oluşturuldu',license_payment_updated:'Ödeme durumu değiştirildi',license_revoked:'Lisans iptal edildi',license_extended:'Lisans süresi uzatıldı',activation_revoked:'Cihaz etkinleştirmesi kaldırıldı',license_activated:'Lisans etkinleştirildi'};
  function renderAudit(){if(!auditEvents.length){auditList.innerHTML='<p class="empty-state">Henüz görüntülenecek yönetici işlemi yok.</p>';return;}auditList.innerHTML=auditEvents.slice(0,30).map(e=>{const d=e.details&&typeof e.details==='object'?e.details:{}, extra=[d.customer_name,d.payment_status?paymentName(d.payment_status):'',d.amount?money(d.amount,d.currency||'TRY'):''].filter(Boolean).join(' · ');return '<div class="audit-item"><div><div class="audit-action">'+esc(auditNames[e.action]||e.action||'Yönetici işlemi')+'</div><div class="audit-detail">'+esc(extra||(e.license_id?'Lisans: '+e.license_id:'İşlem kaydı'))+'</div></div><time class="audit-date">'+esc(dateTime(e.created_at))+'</time></div>';}).join('');}
  async function refreshAll(quiet){if(busy)return;busy=true;connection('Sunucuya bağlanıyor','busy');if(!quiet)showMessage(globalMessage,'Kayıtlar yenileniyor…');try{const r=await Promise.all([invoke('license_list'),invoke('audit_list').catch(()=>({events:[]}))]);licenses=Array.isArray(r[0].licenses)?r[0].licenses:[];auditEvents=Array.isArray(r[1].events)?r[1].events:[];renderStats();renderLicenses();renderAudit();connection('Çevrimiçi','good');showMessage(globalMessage,quiet?'':'Kayıtlar güncellendi · '+licenses.length+' lisans.','success');await refreshEducation();}catch(e){connection('Bağlantı hatası','bad');showMessage(globalMessage,errorText(e),'error');if(/oturum|giriş yap|UNAUTHENTICATED/i.test(errorText(e))){logoutCustom();showLogin();showMessage(loginMessage,errorText(e),'error');}}finally{busy=false;}}
  function payloadFromForm(){const p=el('licensePlan').value;let days=Number(el('expiresDays').value),amount=Number(el('paymentAmount').value),name=el('customerName').value.trim(),email=el('customerEmail').value.trim();if(p==='lifetime')days=0;if(!Number.isInteger(days)||days<0||days>3650)throw new Error('Lisans süresi 0 ile 3650 gün arasında tam sayı olmalı.');if(!Number.isFinite(amount)||amount<0||amount>999999999)throw new Error('Tutarı kontrol et.');if(!name)throw new Error('Müşteri / öğrenci adı gerekli.');if(email&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))throw new Error('Geçerli bir e-posta adresi gir.');return{label:el('licenseLabel').value.trim()||'Stagepulse Ses Mühendisliği Merkezi',plan_code:p,max_activations:Number(el('maxActivations').value),expires_days:days,customer_name:name,customer_email:email,payment_method:el('paymentMethod').value,payment_status:el('paymentStatus').value,amount:amount,currency:'TRY',payment_reference:el('paymentReference').value.trim(),notes:el('licenseNotes').value.trim()};}
  loginForm.addEventListener('submit',async ev=>{ev.preventDefault();const b=el('loginButton');b.disabled=true;showMessage(loginMessage,'Özel yönetici hesabı doğrulanıyor…');connection('Kimlik doğrulanıyor','busy');try{await loginWithCustomCredentials(el('loginEmail').value.trim(),el('loginPassword').value);if(!(await verifyOwner()))throw new Error('Oturum açılamadı.');el('loginPassword').value='';showMessage(loginMessage,'');showApp();await refreshAll(true);}catch(e){logoutCustom();showLogin();connection('Giriş yapılamadı','bad');showMessage(loginMessage,errorText(e),'error');}finally{b.disabled=false;}});
  licenseForm.addEventListener('submit',async ev=>{ev.preventDefault();const b=el('createLicenseButton');b.disabled=true;issuedKeyPanel.classList.add('hidden');issuedKey.textContent='';showMessage(globalMessage,'Lisans oluşturuluyor…');try{const p=payloadFromForm();if(p.payment_status==='paid'&&!confirm('Tahsilatı gerçekten aldığını onaylıyor musun? Bu seçim lisansı etkinleştirilebilir hâle getirir.'))return;const r=await invoke('license_create',p);if(!r.key||!r.license||!r.license.id)throw new Error('Sunucu lisans anahtarı döndürmedi. Listeyi kontrol et.');issuedKey.textContent=r.key;el('issuedKeyTitle').textContent=p.customer_name+' için lisans anahtarı hazır';issuedKeyPanel.classList.remove('hidden');showMessage(globalMessage,p.payment_status==='paid'?'Lisans ve tahsilat kaydı oluşturuldu.':'Lisans oluşturuldu. Ödeme onaylanana kadar etkinleştirilemez.','success');licenseForm.reset();el('licenseLabel').value='Stagepulse Ses Mühendisliği Merkezi';el('expiresDays').value='365';el('expiresDays').disabled=false;el('maxActivations').value='1';el('paymentStatus').value='unpaid';el('paymentAmount').value='0';await refreshAll(true);issuedKeyPanel.scrollIntoView({behavior:'smooth',block:'nearest'});}catch(e){showMessage(globalMessage,errorText(e),'error');}finally{b.disabled=false;}});
  el('licensePlan').addEventListener('change',()=>{const life=el('licensePlan').value==='lifetime';if(life)el('expiresDays').value='0';else if(el('expiresDays').value==='0')el('expiresDays').value='365';el('expiresDays').disabled=life;});
  el('copyKeyButton').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(issuedKey.textContent);el('copyKeyButton').textContent='Kopyalandı ✓';}catch{const r=document.createRange();r.selectNodeContents(issuedKey);const s=window.getSelection();s.removeAllRanges();s.addRange(r);showMessage(globalMessage,'Otomatik kopyalama kapalı. Anahtarı seçip kopyala.','');}});
  el('dismissKeyButton').addEventListener('click',()=>{issuedKey.textContent='';issuedKeyPanel.classList.add('hidden');});
  el('signOutButton').addEventListener('click',async()=>{logoutCustom();showLogin();showMessage(loginMessage,'Oturum kapatıldı.','success');showMessage(globalMessage,'');connection('Oturum kapalı','good');});
  el('refreshButton').addEventListener('click',()=>refreshAll(false));el('licenseSearch').addEventListener('input',renderLicenses);el('licenseFilter').addEventListener('change',renderLicenses);
  licenseList.addEventListener('click',async ev=>{const b=ev.target.closest('button[data-action]');if(!b||b.disabled)return;const l=licenses.find(x=>x.id===b.dataset.id);if(!l){showMessage(globalMessage,'Lisans listesi değişmiş olabilir. Yenile.','error');return;}const id=l.id,act=b.dataset.action;let msg='';try{b.disabled=true;if(act==='mark-paid'){if(!confirm((l.customer_name||l.label)+' için ödemeyi gerçekten aldın mı?'))return;await invoke('license_payment_update',{license_id:id,payment_status:'paid'});msg='Ödeme onaylandı.';}else if(act==='refund'){if(!confirm('İade kaydı oluşturulacak ve mevcut cihaz etkinleştirmeleri kapatılacak.'))return;await invoke('license_payment_update',{license_id:id,payment_status:'refunded'});msg='İade kaydedildi, cihaz etkinleştirmeleri kapatıldı.';}else if(act==='revoke'){if(!confirm('Bu lisans kalıcı olarak iptal edilecek. Devam edilsin mi?'))return;await invoke('license_revoke',{license_id:id});msg='Lisans iptal edildi.';}else if(act==='extend'){const days=Number(b.dataset.days);if(!confirm('Lisans süresine '+days+' gün eklenecek. Devam edilsin mi?'))return;await invoke('license_extend',{license_id:id,days_to_add:days});msg='Lisans '+days+' gün uzatıldı.';}else if(act==='activations'){await showActivations(l,b);return;}showMessage(globalMessage,msg,'success');await refreshAll(true);}catch(e){showMessage(globalMessage,errorText(e),'error');}finally{b.disabled=false;}});
  async function showActivations(l,b){if(b)b.disabled=true;el('activationHeading').textContent=(l.customer_name||l.label)+' · cihazlar';el('activationList').innerHTML='<div class="empty-state">Cihazlar yükleniyor…</div>';if(!activationDialog.open&&typeof activationDialog.showModal==='function')activationDialog.showModal();try{const r=await invoke('license_activations',{license_id:l.id}),rows=Array.isArray(r.activations)?r.activations:[];if(!rows.length){el('activationList').innerHTML='<div class="empty-state">Cihaz etkinleştirmesi yok.</div>';return;}el('activationList').innerHTML=rows.map(a=>'<article class="activation-card"><div><code>'+esc(a.device_hint||'Cihaz')+'</code><p>İlk etkinleştirme: '+esc(dateTime(a.activated_at))+'</p><p>Son kontrol: '+esc(dateTime(a.last_seen_at))+'</p></div><button class="button '+(a.is_active?'button-danger':'button-quiet')+' button-small" type="button" '+(a.is_active?'data-activation-revoke="'+esc(a.id)+'" data-license-id="'+esc(l.id)+'"':'disabled')+'>'+(a.is_active?'Cihazı kaldır':'Pasif')+'</button></article>').join('');}catch(e){el('activationList').innerHTML='<div class="empty-state">'+esc(errorText(e))+'</div>';}finally{if(b)b.disabled=false;}}
  el('activationList').addEventListener('click',async ev=>{const b=ev.target.closest('[data-activation-revoke]');if(!b)return;if(!confirm('Bu cihazın lisans aktivasyonunu kaldırmak istiyor musun?'))return;b.disabled=true;try{await invoke('activation_revoke',{license_id:b.dataset.licenseId,activation_id:b.dataset.activationRevoke});showMessage(globalMessage,'Cihaz aktivasyonu kaldırıldı.','success');const l=licenses.find(x=>x.id===b.dataset.licenseId);if(l)await showActivations(l,null);await refreshAll(true);}catch(e){showMessage(globalMessage,errorText(e),'error');b.disabled=false;}});
  el('closeActivationDialog').addEventListener('click',()=>activationDialog.close());activationDialog.addEventListener('click',ev=>{if(ev.target===activationDialog)activationDialog.close();});
  const csvSafe=v=>{let s=String(v==null?'':v);if(/^[=+\-@\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};
  el('exportButton').addEventListener('click',()=>{const fields=['customer_name','customer_email','label','plan_code','payment_method','payment_status','amount','currency','expires_at','is_active','active_activations','max_activations','created_at','payment_reference','id'],rows=[fields.join(';')].concat(visible().map(l=>fields.map(f=>csvSafe(l[f])).join(';'))),blob=new Blob(['\ufeff'+rows.join('\r\n')],{type:'text/csv;charset=utf-8;'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='stagepulse-lisanslar-'+new Date().toISOString().slice(0,10)+'.csv';a.click();URL.revokeObjectURL(url);});

  async function educationInvoke(action,payload){
    const response=await fetch(SUPABASE_URL+'/functions/v1/'+EDUCATION_FUNCTION,{method:'POST',headers:{'Content-Type':'application/json','apikey':SUPABASE_PUBLISHABLE_KEY,'Authorization':'Bearer '+adminToken},body:JSON.stringify(Object.assign({action},payload||{}))});
    const data=await response.json().catch(()=>({error:'Sunucudan geçersiz yanıt geldi.'}));
    if(!response.ok||data.ok!==true)throw new Error(data.error||'Eğitim yönetimi isteği başarısız ('+response.status+').');
    return data;
  }
  function renderStudentLicenseOptions(){
    const select=el('studentLicense');if(!select)return;
    const valid=licenses.filter(l=>l.is_active&&l.payment_status==='paid'&&(!l.expires_at||Date.parse(l.expires_at)>Date.now()));
    select.innerHTML='<option value="">Ödenmiş aktif lisans seç</option>'+valid.map(l=>'<option value="'+esc(l.id)+'">'+esc(l.customer_name||l.label)+' · '+esc(l.customer_email||'')+' · '+esc(date(l.expires_at))+'</option>').join('');
    if(!valid.length)select.innerHTML='<option value="">Öğrenci oluşturmak için önce ödenmiş aktif lisans oluştur</option>';
  }
  let educationStudents=[], educationExams=[], educationDocuments=[];
  function renderStudents(){
    const node=el('studentList');if(!node)return;
    if(!educationStudents.length){node.innerHTML='<div class="empty-state">Henüz öğrenci hesabı yok.</div>';return;}
    node.innerHTML=educationStudents.map(s=>'<article class="education-card"><div class="education-card-head"><div><h3>'+esc(s.display_name||'İsimsiz öğrenci')+'</h3><p class="customer-email">'+esc(s.email)+'</p></div><span class="status-badge '+(s.is_active?'status-active':'status-revoked')+'">'+(s.is_active?'Aktif':'Pasif')+'</span></div><div class="education-meta"><span>Lisans: '+esc(s.license&&s.license.label||'Bilinmiyor')+'</span><span>İlerleme: '+Number(s.progress.done||0)+' / '+Number(s.progress.total||0)+' modül</span><span>Kayıt: '+esc(date(s.created_at))+'</span></div><div class="education-actions"><button class="button button-outline button-small" data-student-action="password" data-id="'+esc(s.user_id)+'">Parola sıfırla</button><button class="button button-danger button-small" data-student-action="delete" data-id="'+esc(s.user_id)+'">Hesabı sil</button></div></article>').join('');
  }
  function renderExams(){
    const node=el('examList'),select=el('questionExam');if(!node||!select)return;
    select.innerHTML='<option value="">Sınav seç</option>'+educationExams.map(x=>'<option value="'+esc(x.id)+'">'+esc(x.title)+'</option>').join('');
    if(!educationExams.length){node.innerHTML='<div class="empty-state">Henüz sınav oluşturulmadı.</div>';return;}
    node.innerHTML=educationExams.map(x=>'<article class="education-card"><div class="education-card-head"><div><h3>'+esc(x.title)+'</h3><p class="customer-email">'+esc(x.description||'Açıklama yok')+'</p></div><span class="status-badge '+(x.is_published?'status-active':'status-pending')+'">'+(x.is_published?'Yayında':'Taslak')+'</span></div><div class="education-meta"><span>Geçme: '+Number(x.pass_percent)+'%</span><span>Deneme: '+Number(x.attempts_allowed)+'</span><span>Süre: '+(x.duration_minutes?Number(x.duration_minutes)+' dk':'Sınırsız')+'</span></div><div class="education-actions"><button class="button button-outline button-small" data-exam-action="questions" data-id="'+esc(x.id)+'">Soruları yönet</button><button class="button button-outline button-small" data-exam-action="attempts" data-id="'+esc(x.id)+'">Sonuçlar</button><button class="button button-success button-small" data-exam-action="publish" data-published="'+(!x.is_published)+'" data-id="'+esc(x.id)+'">'+(x.is_published?'Yayından kaldır':'Yayınla')+'</button><button class="button button-danger button-small" data-exam-action="delete" data-id="'+esc(x.id)+'">Sil</button></div></article>').join('');
  }
  function renderQuestions(rows){
    const node=el('questionList');if(!node)return;
    if(!rows.length){node.innerHTML='<div class="empty-state">Bu sınavda henüz soru yok.</div>';return;}
    node.innerHTML=rows.map((q,i)=>'<article class="education-card"><div class="education-card-head"><h3>'+(i+1)+'. '+esc(q.question_text)+'</h3><span class="status-badge status-active">'+esc(q.question_type)+'</span></div><div class="education-meta"><span>Puan: '+Number(q.points)+'</span><span>Doğru cevap: '+esc(Array.isArray(q.correct_answer)?q.correct_answer.join(', '):String(q.correct_answer))+'</span></div><div class="education-actions"><button class="button button-danger button-small" data-question-delete="'+esc(q.id)+'" data-exam-id="'+esc(q.exam_id)+'">Soruyu sil</button></div></article>').join('');
  }
  function renderAttempts(rows){
    const node=el('examAttemptsList');if(!node)return;
    if(!rows.length){node.innerHTML='<p class="empty-state">Bu sınav için henüz sonuç yok.</p>';return;}
    node.innerHTML=rows.map(a=>'<div class="audit-item"><div><div class="audit-action">'+esc(a.student&&a.student.display_name||a.student&&a.student.email||'Öğrenci')+' · '+Number(a.percent||0).toFixed(1)+'%</div><div class="audit-detail">'+Number(a.correct_count||0)+' / '+Number(a.question_count||0)+' doğru · '+(a.passed?'Başarılı':'Başarısız')+' · '+esc(a.status)+'</div></div><time class="audit-date">'+esc(dateTime(a.submitted_at||a.started_at))+'</time></div>').join('');
  }
  function renderDocuments(){
    const node=el('documentList');if(!node)return;
    if(!educationDocuments.length){node.innerHTML='<div class="empty-state">Henüz PDF yüklenmedi.</div>';return;}
    node.innerHTML=educationDocuments.map(d=>'<article class="education-card"><div class="education-card-head"><div><h3>'+esc(d.title)+'</h3><p class="customer-email">'+esc(d.description||d.file_name)+'</p></div><span class="status-badge '+(d.is_published?'status-active':'status-pending')+'">'+(d.is_published?'Yayında':'Taslak')+'</span></div><div class="education-meta"><span>'+esc(d.category)+'</span><span>'+Number(d.file_size/1024/1024).toFixed(2)+' MB</span><span>Sürüm '+Number(d.version||1)+'</span><span>'+esc(date(d.updated_at))+'</span></div><div class="education-actions"><button class="button button-outline button-small" data-document-action="edit" data-id="'+esc(d.id)+'">Bilgileri düzenle</button><button class="button button-outline button-small" data-document-action="replace" data-id="'+esc(d.id)+'">Yeni PDF sürümü</button><button class="button button-outline button-small" data-document-action="preview" data-id="'+esc(d.id)+'">Önizle</button><button class="button button-success button-small" data-document-action="publish" data-published="'+(!d.is_published)+'" data-id="'+esc(d.id)+'">'+(d.is_published?'Yayından kaldır':'Yayınla')+'</button><button class="button button-outline button-small" data-document-action="analytics" data-id="'+esc(d.id)+'">Analiz</button><button class="button button-danger button-small" data-document-action="delete" data-id="'+esc(d.id)+'">Sil</button></div></article>').join('');
  }
  async function refreshEducation(){
    try{
      const [students,exams,documents,analytics]=await Promise.all([
        educationInvoke('students_list'),educationInvoke('exams_list'),educationInvoke('documents_list'),educationInvoke('document_analytics')
      ]);
      educationStudents=students.students||[];educationExams=exams.exams||[];educationDocuments=documents.documents||[];
      renderStudentLicenseOptions();renderStudents();renderExams();renderDocuments();
      const summary=analytics.summary||[];
      const node=el('documentAnalytics');
      if(node)node.innerHTML=summary.length?summary.map(x=>{const d=educationDocuments.find(v=>v.id===x.document_id);return '<div class="audit-item"><div><div class="audit-action">'+esc(d&&d.title||'Eğitim PDF')+'</div><div class="audit-detail">'+Number(x.views)+' görüntüleme · '+Number(x.downloads)+' indirme · '+Number(x.unique_users)+' tekil öğrenci</div></div><time class="audit-date">'+esc(dateTime(x.last_event))+'</time></div>';}).join(''):'<p class="empty-state">Henüz görüntüleme veya indirme kaydı yok. Öğrenci uygulaması yayınlanan belgeyi açtığında analiz kaydı oluşur.</p>';
    }catch(e){showMessage(globalMessage,'Eğitim yönetimi verileri yüklenemedi: '+errorText(e),'error');}
  }
  el('studentForm').addEventListener('submit',async ev=>{
    ev.preventDefault();const b=el('studentCreateButton');b.disabled=true;
    try{await educationInvoke('student_create',{display_name:el('studentName').value.trim(),email:el('studentEmail').value.trim(),password:el('studentPassword').value,license_id:el('studentLicense').value});el('studentForm').reset();showMessage(globalMessage,'Öğrenci hesabı oluşturuldu. İlk parolayı güvenli şekilde öğrenciye ilet.','success');await refreshEducation();}
    catch(e){showMessage(globalMessage,errorText(e),'error');}finally{b.disabled=false;}
  });
  el('studentList').addEventListener('click',async ev=>{
    const b=ev.target.closest('button[data-student-action]');if(!b)return;const id=b.dataset.id;
    try{b.disabled=true;if(b.dataset.studentAction==='password'){const password=prompt('Yeni parola gir (en az 10 karakter, harf ve rakam):');if(password===null)return;await educationInvoke('student_password_reset',{student_user_id:id,new_password:password});showMessage(globalMessage,'Öğrenci parolası yenilendi.','success');}
      else{const s=educationStudents.find(x=>x.user_id===id);if(!confirm((s&&s.display_name||'Öğrenci')+' hesabı ve ilerleme kayıtları kalıcı olarak silinecek. Devam edilsin mi?'))return;await educationInvoke('student_delete',{student_user_id:id});showMessage(globalMessage,'Öğrenci hesabı silindi.','success');await refreshEducation();}}
    catch(e){showMessage(globalMessage,errorText(e),'error');}finally{b.disabled=false;}
  });
  el('examForm').addEventListener('submit',async ev=>{
    ev.preventDefault();try{await educationInvoke('exam_save',{title:el('examTitle').value.trim(),description:el('examDescription').value.trim(),module_id:el('examModule').value.trim(),duration_minutes:el('examDuration').value?Number(el('examDuration').value):null,pass_percent:Number(el('examPass').value),attempts_allowed:Number(el('examAttempts').value)});el('examForm').reset();el('examPass').value='70';el('examAttempts').value='1';showMessage(globalMessage,'Sınav taslağı oluşturuldu. Soruları ekleyip yayınlayabilirsin.','success');await refreshEducation();}
    catch(e){showMessage(globalMessage,errorText(e),'error');}
  });
  el('examList').addEventListener('click',async ev=>{
    const b=ev.target.closest('button[data-exam-action]');if(!b)return;const id=b.dataset.id,x=educationExams.find(v=>v.id===id);if(!x)return;
    try{b.disabled=true;const action=b.dataset.examAction;
      if(action==='questions'){el('questionExam').value=id;const r=await educationInvoke('questions_list',{exam_id:id});renderQuestions(r.questions||[]);el('questionForm').scrollIntoView({behavior:'smooth',block:'center'});}
      else if(action==='attempts'){const r=await educationInvoke('exam_attempts',{exam_id:id});renderAttempts(r.attempts||[]);el('examAttemptsList').scrollIntoView({behavior:'smooth',block:'center'});}
      else if(action==='publish'){await educationInvoke('exam_publish',{exam_id:id,published:b.dataset.published==='true'});await refreshEducation();}
      else if(action==='delete'){if(!confirm('Sınav, soruları ve sonuçları kalıcı olarak silinecek. Devam edilsin mi?'))return;await educationInvoke('exam_delete',{exam_id:id});await refreshEducation();}
    }catch(e){showMessage(globalMessage,errorText(e),'error');}finally{b.disabled=false;}
  });
  el('questionExam').addEventListener('change',async()=>{
    if(!el('questionExam').value){renderQuestions([]);return;}
    try{const r=await educationInvoke('questions_list',{exam_id:el('questionExam').value});renderQuestions(r.questions||[]);}catch(e){showMessage(globalMessage,errorText(e),'error');}
  });
  el('questionForm').addEventListener('submit',async ev=>{
    ev.preventDefault();const type=el('questionType').value,raw=el('questionCorrect').value.trim();let correct=raw;
    if(type==='true_false'){if(!['true','false'].includes(raw.toLowerCase())){showMessage(globalMessage,'Doğru/yanlış cevabı true veya false olmalı.','error');return;}correct=raw.toLowerCase()==='true';}
    if(type==='multiple_choice')correct=raw.split(',').map(x=>x.trim()).filter(Boolean);
    const options=type==='true_false'||type==='short_answer'?[]:el('questionOptions').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
    try{await educationInvoke('question_save',{exam_id:el('questionExam').value,question_text:el('questionText').value.trim(),question_type:type,options,correct_answer:correct,points:Number(el('questionPoints').value),position:el('questionList').children.length,explanation:el('questionExplanation').value.trim()});el('questionText').value='';el('questionOptions').value='';el('questionCorrect').value='';el('questionExplanation').value='';const r=await educationInvoke('questions_list',{exam_id:el('questionExam').value});renderQuestions(r.questions||[]);await refreshEducation();showMessage(globalMessage,'Soru kaydedildi. Sınav değiştiği için yeniden yayınlaman gerekir.','success');}
    catch(e){showMessage(globalMessage,errorText(e),'error');}
  });
  el('questionList').addEventListener('click',async ev=>{
    const b=ev.target.closest('button[data-question-delete]');if(!b)return;if(!confirm('Bu soru silinsin mi?'))return;
    try{await educationInvoke('question_delete',{question_id:b.dataset.questionDelete,exam_id:b.dataset.examId});const r=await educationInvoke('questions_list',{exam_id:b.dataset.examId});renderQuestions(r.questions||[]);await refreshEducation();}catch(e){showMessage(globalMessage,errorText(e),'error');}
  });
  el('documentForm').addEventListener('submit',async ev=>{
    ev.preventDefault();const button=el('documentUploadButton'),file=el('documentFile').files[0];if(!file)return;
    if(file.type!=='application/pdf'&&!file.name.toLowerCase().endsWith('.pdf')){showMessage(globalMessage,'Yalnızca PDF dosyası yüklenebilir.','error');return;}
    if(file.size<1||file.size>52428800){showMessage(globalMessage,'PDF boyutu 50 MB sınırını aşmamalı.','error');return;}
    button.disabled=true;let path='';
    try{const auth=await getClient().auth.getUser();if(!auth.data.user)throw new Error('Yönetici oturumu gerekli.');const safeName=file.name.replace(/[^a-zA-Z0-9._-]/g,'_');path=auth.data.user.id+'/'+Date.now()+'-'+safeName;
      const upload=await getClient().storage.from(EDUCATION_BUCKET).upload(path,file,{contentType:'application/pdf',upsert:false});if(upload.error)throw upload.error;
      await educationInvoke('document_register',{title:el('documentTitle').value.trim(),description:el('documentDescription').value.trim(),category:el('documentCategory').value.trim(),storage_path:path,file_name:file.name,file_size:file.size});
      el('documentForm').reset();el('documentCategory').value='genel';showMessage(globalMessage,'PDF güvenli depoya yüklendi. Yayına almak için belge kartındaki Yayınla düğmesini kullan.','success');await refreshEducation();
    }catch(e){if(path)await getClient().storage.from(EDUCATION_BUCKET).remove([path]);showMessage(globalMessage,errorText(e),'error');}finally{button.disabled=false;}
  });
  el('documentList').addEventListener('click',async ev=>{
    const b=ev.target.closest('button[data-document-action]');if(!b)return;const id=b.dataset.id,d=educationDocuments.find(x=>x.id===id);if(!d)return;
    try{b.disabled=true;const action=b.dataset.documentAction;
      if(action==='publish'){await educationInvoke('document_publish',{document_id:id,published:b.dataset.published==='true'});await refreshEducation();}
      else if(action==='replace'){
        const picker=document.createElement('input');picker.type='file';picker.accept='application/pdf,.pdf';
        picker.onchange=async()=>{
          const file=picker.files&&picker.files[0];if(!file)return;
          if((file.type!=='application/pdf'&&!file.name.toLowerCase().endsWith('.pdf'))||file.size<1||file.size>52428800){showMessage(globalMessage,'Yeni PDF dosyası geçerli olmalı ve 50 MB sınırını aşmamalı.','error');return;}
          let path='';
          try{const auth=await getClient().auth.getUser();if(!auth.data.user)throw new Error('Yönetici oturumu gerekli.');
            path=auth.data.user.id+'/'+Date.now()+'-'+file.name.replace(/[^a-zA-Z0-9._-]/g,'_');
            const up=await getClient().storage.from(EDUCATION_BUCKET).upload(path,file,{contentType:'application/pdf',upsert:false});if(up.error)throw up.error;
            await educationInvoke('document_replace',{document_id:id,storage_path:path,file_name:file.name,file_size:file.size});
            await refreshEducation();showMessage(globalMessage,'PDF yeni sürümle değiştirildi. Yeniden yayınlaman gerekir.','success');
          }catch(e){if(path)await getClient().storage.from(EDUCATION_BUCKET).remove([path]);showMessage(globalMessage,errorText(e),'error');}
        };
        picker.click();
      }
      else if(action==='preview'){const r=await educationInvoke('document_signed_url',{document_id:id});window.open(r.url,'_blank','noopener');}
      else if(action==='analytics'){const r=await educationInvoke('document_analytics',{document_id:id});const x=(r.summary||[])[0];showMessage(globalMessage,x?('PDF analizi: '+x.views+' görüntüleme, '+x.downloads+' indirme, '+x.unique_users+' tekil öğrenci.'):'Bu PDF için henüz kullanım kaydı yok.','success');}
      else if(action==='edit'){const title=prompt('Belge başlığı:',d.title);if(title===null)return;const description=prompt('Belge açıklaması:',d.description||'');if(description===null)return;const category=prompt('Kategori:',d.category||'genel');if(category===null)return;await educationInvoke('document_update',{document_id:id,title,description,category});await refreshEducation();showMessage(globalMessage,'Belge bilgileri güncellendi. Yayın durumu taslağa alındı.','success');}
      else if(action==='delete'){if(!confirm('PDF dosyası ve kayıtları kalıcı olarak silinsin mi?'))return;await educationInvoke('document_delete',{document_id:id});await refreshEducation();}
    }catch(e){showMessage(globalMessage,errorText(e),'error');}finally{b.disabled=false;}
  });

  async function init(){if(location.protocol==='file:'){showMessage(loginMessage,'Bu panel dosyadan değil, HTTPS adresinden açılmalı: stagepulse.com.tr/ses-merkezi-lisans/','error');connection('HTTPS gerekli','bad');return;}try{getClient();if(adminToken&&adminRefreshToken){const restored=await getClient().auth.setSession({access_token:adminToken,refresh_token:adminRefreshToken});if(restored.error){logoutCustom();}}else if(adminToken){logoutCustom();}if(!(await verifyOwner())){connection('Oturum kapalı','good');return;}showApp();await refreshAll(true);}catch(e){logoutCustom();showLogin();connection('Oturum doğrulanamadı','bad');showMessage(loginMessage,errorText(e),'error');}}
  window.addEventListener('online',()=>connection('Çevrimiçi','good'));window.addEventListener('offline',()=>connection('İnternet yok','bad'));init();
})();
