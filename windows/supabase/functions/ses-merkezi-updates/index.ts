import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const MANIFEST_URL = "https://raw.githubusercontent.com/ibrahimFOH/Stagepulse-Releases/main/latest.json";

type Platform = "windows" | "android";
type Channel = "stable";

function reply(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
      "Pragma": "no-cache",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Accept, apikey, authorization, x-client-info",
      "Vary": "Origin",
    },
  });
}

function parseVersion(value: unknown): { version: string; versionCode: number; tuple: number[] } | null {
  const match = String(value ?? "").match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!match) return null;
  const tuple = match.slice(1).map(Number);
  const versionCode = tuple[0] * 10000 + tuple[1] * 100 + tuple[2];
  if (!Number.isSafeInteger(versionCode)) return null;
  return { version: tuple.join("."), versionCode, tuple };
}

function validDownloadUrl(value: unknown, version: string, filename: string): string | null {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    const expectedPath = `/ibrahimFOH/Stagepulse-Releases/releases/download/v${version}/${filename}`;
    if (
      url.protocol !== "https:" ||
      url.hostname.toLowerCase() !== "github.com" ||
      url.pathname !== expectedPath ||
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      url.port
    ) return null;
    return url.toString();
  } catch {
    return null;
  }
}

function validSha256(value: unknown): string | null {
  return typeof value === "string" && /^[a-f0-9]{64}$/i.test(value)
    ? value.toLowerCase()
    : null;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return reply({ ok: true });
  if (req.method !== "GET") return reply({ ok: false, error: "Yalnızca GET desteklenir." }, 405);

  const params = new URL(req.url).searchParams;
  const platformValue = params.get("platform") ?? "windows";
  const channelValue = params.get("channel") ?? "stable";

  if (platformValue !== "windows" && platformValue !== "android") {
    return reply({ ok: false, error: "Platform değeri geçersiz." }, 400);
  }
  if (channelValue !== "stable") {
    return reply({ ok: false, error: "Güncelleme kanalı geçersiz." }, 400);
  }

  const platform = platformValue as Platform;
  const channel = channelValue as Channel;

  try {
    const response = await fetch(MANIFEST_URL, {
      headers: {
        "Accept": "application/json",
        "Cache-Control": "no-cache, no-store",
        "Pragma": "no-cache",
        "User-Agent": "Stagepulse-Ses-Merkezi-Updater",
      },
    });

    if (!response.ok) {
      console.error("Canonical update manifest returned", response.status, channel);
      return reply({ ok: false, error: "Güncelleme manifesti şu anda alınamıyor." }, 502);
    }

    const raw = await response.text();
    if (!raw || raw.length > 64 * 1024) {
      return reply({ ok: false, error: "Güncelleme manifesti boş veya beklenenden büyük." }, 502);
    }

    const manifest = JSON.parse(raw) as Record<string, unknown>;
    if (manifest.ok !== true || manifest.published !== true) {
      return reply({
        ok: true,
        published: false,
        channel,
        message: "Bu kanalda yayımlanmış bir güncelleme bulunmuyor.",
      });
    }

    const parsed = parseVersion(manifest.version);
    if (!parsed || manifest.versionName !== parsed.version ||
        Number(manifest.versionCode) !== parsed.versionCode ||
        manifest.channel !== "stable" ||
        manifest.prerelease !== false) {
      console.error("Canonical update manifest metadata is inconsistent", channel);
      return reply({ ok: false, error: "Güncelleme manifesti sürüm veya kanal doğrulamasından geçemedi." }, 502);
    }

    const windows = manifest.windows as Record<string, unknown> | undefined;
    const android = manifest.android as Record<string, unknown> | undefined;
    const windowsName = `Stagepulse-Ses-Merkezi-Windows-${parsed.version}.exe`;
    const androidName = `Stagepulse-Ses-Merkezi-Android-${parsed.version}.apk`;

    const windowsUrl = validDownloadUrl(windows?.url, parsed.version, windowsName);
    const windowsHash = validSha256(windows?.sha256);
    const androidUrl = validDownloadUrl(android?.url, parsed.version, androidName);
    const androidHash = validSha256(android?.sha256);

    if (!windowsUrl || !windowsHash || windows?.filename !== windowsName ||
        !androidUrl || !androidHash || android?.filename !== androidName ||
        manifest.url !== windowsUrl || manifest.sha256 !== windowsHash ||
        manifest.filename !== windowsName || manifest.apkUrl !== androidUrl ||
        manifest.apkSha256 !== androidHash) {
      console.error("Canonical update manifest asset metadata is invalid", channel, parsed.version);
      return reply({ ok: false, error: "Windows veya Android indirme kaydı doğrulanamadı." }, 502);
    }

    const common = {
      ok: true,
      published: true,
      channel,
      prerelease: false,
      version: parsed.version,
      versionName: parsed.version,
      versionCode: parsed.versionCode,
      notes: String(manifest.notes ?? "").slice(0, 2000),
      release_url: `https://github.com/ibrahimFOH/Stagepulse-Releases/releases/tag/v${parsed.version}`,
    };

    if (platform === "android") {
      return reply({ ...common, apkUrl: androidUrl, apkSha256: androidHash });
    }

    return reply({
      ...common,
      url: windowsUrl,
      sha256: windowsHash,
      filename: windowsName,
    });
  } catch (error) {
    console.error("Canonical Ses Merkezi update check failed:", error);
    return reply({ ok: false, error: "Güncelleme bilgisi şu anda alınamıyor." }, 502);
  }
});
