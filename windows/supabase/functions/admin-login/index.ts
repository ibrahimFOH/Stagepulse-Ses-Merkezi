import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";
const ALLOWED_ORIGINS = new Set(["https://stagepulse.com.tr","https://www.stagepulse.com.tr","https://appassets.androidplatform.net","null","http://localhost:5173","http://127.0.0.1:5173"]);
function corsHeadersFor(req:Request):Record<string,string>{const origin=req.headers.get("origin")||"";return {"Access-Control-Allow-Origin":ALLOWED_ORIGINS.has(origin)?origin:"https://stagepulse.com.tr","Vary":"Origin","Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type","Access-Control-Allow-Methods":"POST, OPTIONS"};}
function handleOptions(req:Request):Response|null{return req.method==="OPTIONS"?new Response("ok",{headers:corsHeadersFor(req)}):null;}
function getClientIp(req:Request):string{return req.headers.get("x-forwarded-for")?.split(",")[0]?.trim()||req.headers.get("cf-connecting-ip")||req.headers.get("x-real-ip")||"unknown";}
async function isDistributedRateLimited(db:{rpc:(fn:string,args:Record<string,unknown>)=>PromiseLike<{data:unknown;error:unknown}>},key:string,max=10):Promise<boolean>{try{const result=await db.rpc("check_login_rate_limit",{p_key:key,p_max:max});if(!result||typeof result!=="object")return true;const data=(result as {data?:unknown}).data,error=(result as {error?:unknown}).error;if(error)return true;return data!==true;}catch{return true;}}
const GENERIC_LOGIN_ERROR="Geçersiz kullanıcı adı veya şifre.";
function jsonError(message:string,status:number,headers:Record<string,string>):Response{return Response.json({error:message},{status,headers});}
Deno.serve(async (req) => {
  const opt=handleOptions(req); if(opt)return opt;
  const headers=corsHeadersFor(req);
  if(req.method!=="POST")return jsonError("Method Not Allowed",405,headers);
  try {
    const body=await req.json().catch(()=>null);
    const login=typeof body?.username==="string"?body.username.trim():"";
    const password=typeof body?.password==="string"?body.password:"";
    if(!login||!password)return jsonError("Kullanıcı adı ve şifre zorunludur.",400,headers);
    const url=Deno.env.get("SUPABASE_URL")!;
    const service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const anon=Deno.env.get("SUPABASE_ANON_KEY")!;
    const admin=createClient(url,service,{auth:{persistSession:false}});
    if(await isDistributedRateLimited(admin,`admin-login:ip:${getClientIp(req)}`,10)||
       await isDistributedRateLimited(admin,`admin-login:account:${login.toLowerCase().slice(0,120)}`,10))
      return jsonError("Çok fazla deneme yapıldı. Lütfen daha sonra tekrar deneyin.",429,headers);
    let email=login.toLowerCase();
    if(!login.includes("@")){
      if(!/^[a-z0-9._-]{3,64}$/i.test(login))return jsonError(GENERIC_LOGIN_ERROR,401,headers);
      const users=await admin.auth.admin.listUsers({page:1,perPage:1000});
      if(users.error)return jsonError("İşlem başarısız.",500,headers);
      const found=(users.data.users||[]).find(u=>String(u.user_metadata?.username||"").toLowerCase()===email);
      if(!found?.email)return jsonError(GENERIC_LOGIN_ERROR,401,headers);
      email=found.email.toLowerCase();
    }
    const auth=createClient(url,anon,{auth:{persistSession:false}});
    const {data,error}=await auth.auth.signInWithPassword({email,password});
    if(error||!data.session||!data.user)return jsonError(GENERIC_LOGIN_ERROR,401,headers);
    const {data:membership,error:me}=await admin.from("org_memberships")
      .select("active,role:role_id(code,name,tier,is_admin_role)")
      .eq("user_id",data.user.id).eq("active",true).maybeSingle();
    const role=Array.isArray((membership as any)?.role)?(membership as any)?.role?.[0]:(membership as any)?.role;
    if(me||!membership||role?.is_admin_role!==true||role?.active===false)
      return jsonError(GENERIC_LOGIN_ERROR,401,headers);
    return Response.json({session:data.session,user:{
      id:data.user.id,
      username:data.user.user_metadata?.username||login,
      display_name:data.user.user_metadata?.display_name||data.user.user_metadata?.full_name||"",
      role:role.code
    }},{headers});
  } catch(_) { return jsonError("İşlem başarısız.",500,headers); }
});
