package com.stagepulse.sesmerkezi

import android.Manifest
import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.media.AudioDeviceInfo
import android.media.AudioManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.provider.Settings
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import android.util.Log
import android.view.WindowInsets
import android.webkit.ConsoleMessage
import android.webkit.JavascriptInterface
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.widget.Toast
import androidx.core.content.FileProvider
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewClientCompat
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL
import java.security.KeyStore
import java.security.MessageDigest
import java.util.concurrent.Executors
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null
    private var pendingMediaPermission: PermissionRequest? = null
    private var pendingRuntimePermission: String? = null
    private var pendingRuntimePermissionCallbackId: String? = null
    private val bridgeExecutor = Executors.newSingleThreadExecutor()
    private val bridgeHandler = Handler(Looper.getMainLooper())
    private data class MobileUpdateManifest(
        val versionCode: Int,
        val versionName: String,
        val apkUrl: String,
        val apkSha256: String
    )
    @Volatile private var updateDownloadInProgress = false
    private var pendingInstallerPermissionRequest = false
    private var pendingUpdateManifest: MobileUpdateManifest? = null
    private fun deliverRuntimePermissionResult(callbackId: String, granted: Boolean, message: String = "") {
        if (!callbackId.matches(Regex("[A-Za-z0-9_-]{1,64}"))) return
        val script = "window.__stagepulseResolveMediaPermission && window.__stagepulseResolveMediaPermission(" +
            "${JSONObject.quote(callbackId)}, ${granted}, ${JSONObject.quote(message)});"
        runOnUiThread { if (::webView.isInitialized) webView.evaluateJavascript(script, null) }
    }

    /**
     * WebView/WebRTC mikrofon yakalaması için Android ses modunu hazırlar.
     * Mikrofon izni verilmeden önce çağrılır. İletişim cihazı zorla seçilmez;
     * Android'in varsayılan giriş/çıkış eşlemesi korunur.
     */
    private fun configureAudioForCapture() {
        try {
            val am = getSystemService(Context.AUDIO_SERVICE) as? AudioManager ?: return
            am.mode = AudioManager.MODE_IN_COMMUNICATION
            Log.d("StagepulseAudio", "Ses yakalama modu etkinleştirildi")
        } catch (e: Exception) {
            Log.w("StagepulseAudio", "Ses yakalama modu ayarlanamadı", e)
        }
    }

    private fun restoreAudioMode() {
        try {
            val am = getSystemService(Context.AUDIO_SERVICE) as? AudioManager ?: return
            am.mode = AudioManager.MODE_NORMAL
        } catch (_: Exception) { }
    }

    private val secureSessionPrefs by lazy { getSharedPreferences("stagepulse_ses_secure_v1", MODE_PRIVATE) }

    private val allowedStudentPdfs = setOf(
        "00_Uygulama_Kullanimi_Ogrenci.pdf",
        "01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf",
        "02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf",
        "03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf",
        "04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf",
        "05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf",
        "06_Ogrenci_Uygulama_Formlari.pdf",
        "07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf",
        "08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf",
        "09_SPL_dB_3D_Gorsel_Atlasi.pdf",
        "10_Midas_M32_Live_Uygulamali_Egitim.pdf",
        "11_Yamaha_CL5_Uygulamali_Egitim.pdf",
        "12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(10, 12, 16)
        window.navigationBarColor = Color.rgb(10, 12, 16)
        window.decorView.systemUiVisibility = 0

        webView = WebView(this)
        webView.setBackgroundColor(Color.rgb(10, 12, 16))
        setContentView(webView)

        // Respect Android 15+ system-bar insets; keep the title below the status bar.
        webView.setOnApplyWindowInsetsListener { view, insets ->
            val left: Int
            val top: Int
            val right: Int
            val bottom: Int
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                left = bars.left; top = bars.top; right = bars.right; bottom = bars.bottom
            } else {
                @Suppress("DEPRECATION")
                run {
                    left = insets.systemWindowInsetLeft
                    top = insets.systemWindowInsetTop
                    right = insets.systemWindowInsetRight
                    bottom = insets.systemWindowInsetBottom
                }
            }
            view.setPadding(left, top, right, bottom)
            insets
        }
        webView.requestApplyInsets()

        assetLoader = WebViewAssetLoader.Builder()
            .setDomain("appassets.androidplatform.net")
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            javaScriptCanOpenWindowsAutomatically = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            mediaPlaybackRequiresUserGesture = false
            setSupportMultipleWindows(false)
        }
        webView.addJavascriptInterface(AndroidBridge(), "StagepulseAndroid")
        webView.webViewClient = object : WebViewClientCompat() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                return assetLoader.shouldInterceptRequest(request.url)
                    ?: super.shouldInterceptRequest(view, request)
            }

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val uri = request.url
                if (uri.scheme == "https" && uri.host == "appassets.androidplatform.net") return false
                if (uri.scheme == "https" || uri.scheme == "http") {
                    return try {
                        startActivity(Intent(Intent.ACTION_VIEW, uri))
                        true
                    } catch (_: ActivityNotFoundException) {
                        Toast.makeText(this@MainActivity, "Bağlantı açılamadı.", Toast.LENGTH_SHORT).show()
                        true
                    }
                }
                return true
            }
        }
        webView.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(message: ConsoleMessage): Boolean {
                android.util.Log.d("StagepulseWeb", "${message.message()} (${message.lineNumber()})")
                return true
            }

            override fun onPermissionRequest(request: PermissionRequest) {
                runOnUiThread {
                    val trustedOrigin = request.origin.scheme == "https" &&
                        request.origin.host == "appassets.androidplatform.net"
                    val requestedResources = request.resources.toSet()
                    val supportedResources = setOf(
                        PermissionRequest.RESOURCE_AUDIO_CAPTURE
                    )
                    if (!trustedOrigin || requestedResources.isEmpty() ||
                        requestedResources.any { it !in supportedResources }) {
                        request.deny()
                        return@runOnUiThread
                    }

                    val requiredPermissions = buildList {
                        if (PermissionRequest.RESOURCE_AUDIO_CAPTURE in requestedResources) {
                            add(Manifest.permission.RECORD_AUDIO)
                        }
                    }
                    val missingPermissions = requiredPermissions.filter {
                        checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED
                    }
                    if (missingPermissions.isEmpty()) {
                        configureAudioForCapture()
                        request.grant(requestedResources.toTypedArray())
                    } else {
                        pendingMediaPermission?.let { pending ->
                            if (pending !== request) pending.deny()
                        }
                        pendingMediaPermission = request
                        requestPermissions(missingPermissions.toTypedArray(), REQUEST_MEDIA_PERMISSION)
                    }
                }
            }

            override fun onPermissionRequestCanceled(request: PermissionRequest) {
                runOnUiThread {
                    if (pendingMediaPermission === request) pendingMediaPermission = null
                }
            }

            override fun onShowFileChooser(
                webView: WebView,
                filePathCallback: ValueCallback<Array<Uri>>,
                fileChooserParams: FileChooserParams
            ): Boolean {
                fileChooserCallback?.onReceiveValue(null)
                fileChooserCallback = filePathCallback
                val accepted = fileChooserParams.acceptTypes.filter { it.isNotBlank() }
                val mime = when {
                    accepted.any { it.contains("audio", ignoreCase = true) } -> "audio/*"
                    accepted.any { it.contains("video", ignoreCase = true) } -> "video/*"
                    accepted.size == 1 && accepted[0].contains("/") -> accepted[0]
                    else -> "*/*"
                }
                val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = mime
                    putExtra(Intent.EXTRA_ALLOW_MULTIPLE, fileChooserParams.mode == FileChooserParams.MODE_OPEN_MULTIPLE)
                }
                return try {
                    startActivityForResult(Intent.createChooser(intent, "Dosya seç"), REQUEST_FILE_CHOOSER)
                    true
                } catch (_: ActivityNotFoundException) {
                    fileChooserCallback?.onReceiveValue(null)
                    fileChooserCallback = null
                    Toast.makeText(this@MainActivity, "Dosya seçici açılamadı.", Toast.LENGTH_SHORT).show()
                    false
                }
            }
        }

        webView.loadUrl("https://appassets.androidplatform.net/assets/ui/index.html")
    }


    // Mobile account and licence bridge. Tokens are encrypted with a non-exportable
    // Android Keystore AES-GCM key. The app only contains a publishable API key.
    private fun mobileDeviceHash(): String {
        val raw = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
            ?: throw IllegalStateException("Cihaz kimliği okunamadı.")
        val digest = MessageDigest.getInstance("SHA-256").digest(raw.toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }
    }

    private fun sessionKey(): SecretKey {
        val alias = "stagepulse.ses.mobile.session.v1"
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        if (store.containsAlias(alias)) return store.getKey(alias, null) as SecretKey
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(
            KeyGenParameterSpec.Builder(
                alias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }

    private fun storeSecret(name: String, value: String) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, sessionKey())
        val encrypted = cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        val packed = ByteArray(cipher.iv.size + encrypted.size)
        System.arraycopy(cipher.iv, 0, packed, 0, cipher.iv.size)
        System.arraycopy(encrypted, 0, packed, cipher.iv.size, encrypted.size)
        secureSessionPrefs.edit()
            .putString(name, Base64.encodeToString(packed, Base64.NO_WRAP))
            .apply()
    }

    private fun readSecret(name: String): String? {
        val encoded = secureSessionPrefs.getString(name, null) ?: return null
        return try {
            val packed = Base64.decode(encoded, Base64.DEFAULT)
            if (packed.size <= 12) return null
            val iv = packed.copyOfRange(0, 12)
            val encrypted = packed.copyOfRange(12, packed.size)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, sessionKey(), GCMParameterSpec(128, iv))
            String(cipher.doFinal(encrypted), Charsets.UTF_8)
        } catch (e: Exception) {
            android.util.Log.w("StagepulseMobileAuth", "Şifreli oturum okunamadı; oturum temizlendi.", e)
            secureSessionPrefs.edit().clear().apply()
            null
        }
    }

    private fun saveAuthSession(session: JSONObject) {
        val access = session.optString("access_token")
        val refresh = session.optString("refresh_token")
        if (access.isBlank() || refresh.isBlank()) {
            throw IllegalStateException("Supabase oturum belirteci döndürmedi.")
        }
        storeSecret("session", session.toString())
    }

    private fun requestSupabase(
        method: String,
        path: String,
        body: JSONObject? = null,
        bearer: String? = null
    ): JSONObject {
        val connection = (URL(SUPABASE_URL + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 12000
            readTimeout = 18000
            useCaches = false
            setRequestProperty("apikey", SUPABASE_PUBLISHABLE_KEY)
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Cache-Control", "no-store")
            if (!bearer.isNullOrBlank()) setRequestProperty("Authorization", "Bearer $bearer")
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
            }
        }
        try {
            if (body != null) {
                connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
            val statusCode = connection.responseCode
            val stream = if (statusCode in 200..299) connection.inputStream else connection.errorStream
            val response = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (statusCode !in 200..299) {
                val detail = try {
                    val error = JSONObject(response)
                    error.optString("msg").ifBlank {
                        error.optString("message").ifBlank {
                            error.optString("error_description").ifBlank { error.optString("error") }
                        }
                    }
                } catch (_: Exception) { "" }
                throw MobileApiException(statusCode, detail.ifBlank { "Sunucu isteği reddetti ($statusCode)." })
            }
            return if (response.isBlank()) JSONObject() else JSONObject(response)
        } finally {
            connection.disconnect()
        }
    }

    private class MobileApiException(val statusCode: Int, message: String) : Exception(message)

    private fun requireMobileAccessToken(): String {
        val stored = readSecret("session")?.let { JSONObject(it) }
            ?: throw IllegalStateException("Önce Stagepulse hesabına giriş yap.")
        val access = stored.optString("access_token")
        if (access.isBlank()) throw IllegalStateException("Oturum geçersiz. Yeniden giriş yap.")
        try {
            requestSupabase("GET", "/auth/v1/user", bearer = access)
            return access
        } catch (e: MobileApiException) {
            if (e.statusCode != 401 && e.statusCode != 403) throw e
        }

        val refresh = stored.optString("refresh_token")
        if (refresh.isBlank()) throw IllegalStateException("Oturum süresi doldu. Yeniden giriş yap.")
        val refreshed = requestSupabase(
            "POST",
            "/auth/v1/token?grant_type=refresh_token",
            JSONObject().put("refresh_token", refresh)
        )
        saveAuthSession(refreshed)
        return refreshed.getString("access_token")
    }

    private fun callSesEdge(action: String, fields: JSONObject = JSONObject()): JSONObject {
        val token = requireMobileAccessToken()
        val body = JSONObject(fields.toString())
            .put("action", action)
            .put("app_id", "ses-merkezi-android")
            .put("platform", "android")
            .put("device_hash", mobileDeviceHash())
        val response = requestSupabase("POST", "/functions/v1/ses-merkezi-desktop", body, token)
        if (!response.optBoolean("ok", false)) {
            throw IllegalStateException(response.optString("error").ifBlank { "Lisans sunucusu isteği tamamlayamadı." })
        }
        return response
    }

    private fun fetchMobileContext(): JSONObject {
        val context = callSesEdge("context")
        storeSecret("account_context", context.toString())
        storeSecret("validated_at", System.currentTimeMillis().toString())
        return context
    }

    private fun clearMobileAuthSession() {
        secureSessionPrefs.edit()
            .remove("session")
            .remove("account_context")
            .remove("validated_at")
            .apply()
    }

    private fun restoreMobileAuthSession(): JSONObject {
        if (readSecret("session").isNullOrBlank()) {
            return JSONObject().put("authenticated", false)
        }
        return try {
            // Validate the access token, rotate an expired refresh token, then reload
            // the current server-side role and license context.
            requireMobileAccessToken()
            val context = fetchMobileContext()
            JSONObject().put("authenticated", true).put("context", context)
        } catch (e: MobileApiException) {
            if (e.statusCode in 400..403) {
                clearMobileAuthSession()
                JSONObject().put("authenticated", false)
            } else {
                throw e
            }
        }
    }

    private fun readLimitedAiText(stream: InputStream, maxBytes: Int): String {
        val output = ByteArrayOutputStream()
        val buffer = ByteArray(8192)
        var total = 0
        while (true) {
            val count = stream.read(buffer)
            if (count < 0) break
            total += count
            if (total > maxBytes) throw IllegalStateException("AI yanıtı 2 MB sınırını aştı.")
            output.write(buffer, 0, count)
        }
        return output.toString("UTF-8")
    }

    private fun requestMobileAi(payload: JSONObject): JSONObject {
        val provider = payload.optString("provider").trim().lowercase()
        if (!payload.optBoolean("consent", false)) {
            throw IllegalStateException("AI sağlayıcısına istem gönderme onayı gerekli.")
        }
        if (provider == "ollama") {
            throw IllegalArgumentException("Ollama yalnızca Windows Ses Merkezi uygulamasında yerel çalışır.")
        }
        if (provider != "groq") {
            throw IllegalArgumentException("Android uygulamasında yalnızca Groq kullanılabilir.")
        }

        val model = payload.optString("model").trim().take(160)
        val prompt = payload.optString("prompt").trim()
        val apiKey = payload.optString("api_key").trim()
        val endpoint = payload.optString("endpoint").trim()
            .ifBlank { "https://api.groq.com/openai/v1/chat/completions" }

        if (model.isBlank() || prompt.isBlank()) {
            throw IllegalArgumentException("Model adı ve istem zorunlu.")
        }
        if (prompt.length > 12000) throw IllegalArgumentException("İstem 12.000 karakter sınırını aşıyor.")
        if (apiKey.isBlank() || apiKey.length > 2048) {
            throw IllegalArgumentException("Geçerli bir Groq API anahtarı gerekli.")
        }
        if (endpoint.length > 2048) throw IllegalArgumentException("Groq endpoint adresi çok uzun.")

        val uri = try { URI(endpoint) } catch (_: Exception) {
            throw IllegalArgumentException("Groq endpoint adresi geçersiz.")
        }
        if (uri.scheme != "https" || uri.host?.lowercase() != "api.groq.com" ||
            uri.path != "/openai/v1/chat/completions" || uri.rawUserInfo != null ||
            uri.rawQuery != null || uri.rawFragment != null || uri.port !in listOf(-1, 443)) {
            throw IllegalArgumentException("Android yalnızca resmi Groq HTTPS API endpoint'ini kabul eder.")
        }

        val context = fetchMobileContext()
        val licensed = context.optJSONObject("licensed")?.optBoolean("active", false) == true
        if (context.optString("role") != "owner" && !licensed) {
            throw IllegalStateException("Bulut AI kullanımı için etkin Stagepulse lisansı gerekli.")
        }

        val systemPrompt = "Türkçe yanıt ver. Ses mühendisliği eğitiminde teknik doğruluğu gözet; ölçülmemiş SPL, true-peak, faz veya akustik değerleri uydurma. Varsayım ile ölçüm sonucunu ayır. Tehlikeli ses seviyesi, elektrik, rigging ve işitme maruziyetinde güvenlik uyarısı ver. API anahtarını veya özel bilgileri yanıta koyma."
        val body = JSONObject()
            .put("model", model)
            .put("messages", org.json.JSONArray()
                .put(JSONObject().put("role", "system").put("content", systemPrompt))
                .put(JSONObject().put("role", "user").put("content", prompt)))
            .put("temperature", 0.2)
            .put("stream", false)

        val connection = (URL(endpoint).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 15000
            readTimeout = 75000
            useCaches = false
            instanceFollowRedirects = false
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Cache-Control", "no-store")
            setRequestProperty("User-Agent", "StagepulseSesMerkezi-Android/" + BuildConfig.VERSION_NAME)
            setRequestProperty("Authorization", "Bearer " + apiKey)
        }
        try {
            connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val raw = stream?.use { readLimitedAiText(it, 2_000_000) }.orEmpty()
            if (status !in 200..299) {
                val detail = try {
                    val error = JSONObject(raw)
                    error.optJSONObject("error")?.optString("message")
                        ?.takeIf { it.isNotBlank() } ?: error.optString("message")
                } catch (_: Exception) { "" }
                throw IllegalStateException("Groq HTTP " + status + ": " + detail.ifBlank { "İstek reddedildi." })
            }

            val data = JSONObject(raw)
            val message = data.optJSONArray("choices")?.optJSONObject(0)?.optJSONObject("message")
            val value = message?.opt("content")
            val content = if (value is org.json.JSONArray) {
                (0 until value.length())
                    .mapNotNull { value.optJSONObject(it)?.optString("text") }
                    .filter { it.isNotBlank() }
                    .joinToString("\n")
                    .trim()
            } else {
                value?.toString()?.trim().orEmpty()
            }
            if (content.isBlank()) throw IllegalStateException("Groq yanıtında metin bulunamadı.")

            return JSONObject()
                .put("ok", true)
                .put("provider", "groq")
                .put("provider_name", "GroqCloud")
                .put("model", model)
                .put("content", content)
        } finally {
            connection.disconnect()
        }
    }

    private fun parseMobileUpdateManifest(json: JSONObject): MobileUpdateManifest {
        if (!json.optBoolean("published", false)) {
            throw IllegalStateException("Henüz yayımlanmış kararlı Android sürümü yok.")
        }
        val versionName = json.optString("versionName", json.optString("version")).trim()
        val parts = Regex("^([0-9]+)\\.([0-9]+)\\.([0-9]+)$").matchEntire(versionName)
            ?: throw IllegalArgumentException("Android sürüm numarası geçersiz.")
        val major = parts.groupValues[1].toIntOrNull()
            ?: throw IllegalArgumentException("Android sürüm ana numarası geçersiz.")
        val minor = parts.groupValues[2].toIntOrNull()
            ?: throw IllegalArgumentException("Android sürüm ara numarası geçersiz.")
        val patch = parts.groupValues[3].toIntOrNull()
            ?: throw IllegalArgumentException("Android sürüm yama numarası geçersiz.")
        val expectedCode = major.toLong() * 10000L + minor.toLong() * 100L + patch.toLong()
        if (expectedCode > Int.MAX_VALUE || json.optInt("versionCode", 0) != expectedCode.toInt()) {
            throw IllegalArgumentException("Android sürüm kodu sürüm numarasıyla eşleşmiyor.")
        }

        val apkUrl = json.optString("apkUrl").trim()
        val apkSha256 = json.optString("apkSha256").trim().lowercase()
        val uri = runCatching { URI(apkUrl) }.getOrNull()
            ?: throw IllegalArgumentException("Android paket adresi geçersiz.")
        val expectedPath = "/ibrahimFOH/Stagepulse-Releases/releases/download/v" + versionName +
            "/Stagepulse-Ses-Merkezi-Android-" + versionName + ".apk"
        if (uri.scheme != "https" || uri.host?.lowercase() != "github.com" ||
            uri.path != expectedPath || uri.rawUserInfo != null || uri.rawQuery != null ||
            uri.rawFragment != null || uri.port != -1) {
            throw IllegalArgumentException("Android paket adresi güvenilir Stagepulse yayın deposuna ait değil.")
        }
        if (!apkSha256.matches(Regex("[a-f0-9]{64}"))) {
            throw IllegalArgumentException("Android paket SHA-256 bilgisi geçersiz.")
        }
        return MobileUpdateManifest(json.optInt("versionCode"), versionName, apkUrl, apkSha256)
    }

    private fun checkMobileAppUpdates(): JSONObject {
        var connection: HttpURLConnection? = null
        try {
            connection = (URL(SUPABASE_URL + "/functions/v1/ses-merkezi-updates?platform=android&channel=" + BuildConfig.UPDATE_CHANNEL).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 8000
                readTimeout = 10000
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Cache-Control", "no-cache")
                setRequestProperty("User-Agent", "StagepulseSesMerkezi-Android/" + BuildConfig.VERSION_NAME)
            }
            if (connection.responseCode !in 200..299) {
                throw IllegalStateException("Güncelleme servisi HTTP " + connection.responseCode + " döndürdü.")
            }
            val raw = connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            if (raw.isBlank() || raw.length > 64 * 1024) {
                throw IllegalStateException("Güncelleme bildirimi boş veya izin verilen boyutu aşıyor.")
            }
            val manifest = JSONObject(raw)
            if (!manifest.optBoolean("ok", false)) {
                throw IllegalStateException(manifest.optString("error").ifBlank { "Güncelleme bildirimi doğrulanamadı." })
            }
            if (!manifest.optBoolean("published", false)) {
                return JSONObject()
                    .put("ok", true)
                    .put("published", false)
                    .put("available", false)
                    .put("current_version", BuildConfig.VERSION_NAME)
                    .put("version", "")
                    .put("message", manifest.optString("message", "Henüz yayımlanmış kararlı Android sürümü yok."))
            }

            val update = parseMobileUpdateManifest(manifest)
            val available = update.versionCode > BuildConfig.VERSION_CODE
            return JSONObject()
                .put("ok", true)
                .put("published", true)
                .put("available", available)
                .put("current_version", BuildConfig.VERSION_NAME)
                .put("version", update.versionName)
                .put("versionName", update.versionName)
                .put("versionCode", update.versionCode)
                .put("apkUrl", update.apkUrl)
                .put("apkSha256", update.apkSha256)
                .put("notes", manifest.optString("notes", ""))
                .put("message", if (available) "Yeni Android sürümü bulundu." else "Android uygulaması güncel.")
        } finally {
            connection?.disconnect()
        }
    }

    private fun queueMobileAppUpdate(manifestText: String): JSONObject {
        if (manifestText.isBlank() || manifestText.length > 64 * 1024) {
            throw IllegalArgumentException("Güncelleme bildirimi geçersiz veya çok büyük.")
        }
        val update = parseMobileUpdateManifest(JSONObject(manifestText))
        if (update.versionCode <= BuildConfig.VERSION_CODE) {
            throw IllegalStateException("Kurulabilir daha yeni bir Android sürümü bulunamadı.")
        }
        bridgeHandler.post { beginMobileUpdateInstall(update) }
        return JSONObject().put("ok", true)
            .put("message", "Güncelleme indirilmeye hazırlanıyor. Gerekirse Android yükleme izni ekranı açılacak.")
    }

    private fun beginMobileUpdateInstall(update: MobileUpdateManifest) {
        if (updateDownloadInProgress) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !packageManager.canRequestPackageInstalls()) {
            pendingUpdateManifest = update
            pendingInstallerPermissionRequest = true
            try {
                startActivity(Intent(
                    Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + packageName)
                ))
            } catch (error: Exception) {
                pendingUpdateManifest = null
                pendingInstallerPermissionRequest = false
                Toast.makeText(this, "Android yükleme izni ayarları açılamadı: " + error.message, Toast.LENGTH_LONG).show()
            }
            return
        }
        downloadAndInstallMobileUpdate(update)
    }

    private fun downloadAndInstallMobileUpdate(update: MobileUpdateManifest) {
        if (updateDownloadInProgress) return
        updateDownloadInProgress = true
        Toast.makeText(this, "Stagepulse güncellemesi indiriliyor ve doğrulanıyor…", Toast.LENGTH_LONG).show()
        Thread {
            var connection: HttpURLConnection? = null
            var downloadedApk: File? = null
            var failure: String? = null
            val updatesDir = File(cacheDir, "updates").apply { mkdirs() }
            val safeVersion = update.versionName.replace(Regex("[^0-9.]"), "_")
            val partial = File(updatesDir, "Stagepulse-" + safeVersion + ".apk.part")
            val target = File(updatesDir, "Stagepulse-" + safeVersion + ".apk")
            try {
                partial.delete()
                connection = (URL(update.apkUrl).openConnection() as HttpURLConnection).apply {
                    connectTimeout = 15000
                    readTimeout = 60000
                    instanceFollowRedirects = true
                    setRequestProperty("Accept", "application/vnd.android.package-archive")
                    setRequestProperty("User-Agent", "StagepulseSesMerkezi-Android/" + BuildConfig.VERSION_NAME)
                }
                val responseCode = connection.responseCode
                val finalHost = connection.url.host.lowercase()
                if (responseCode !in 200..299 ||
                    finalHost !in setOf("github.com", "release-assets.githubusercontent.com")) {
                    throw IllegalStateException("Güncelleme indirme adresi veya sunucu yanıtı geçersiz.")
                }
                if (connection.contentLengthLong > 512L * 1024L * 1024L) {
                    throw IllegalStateException("Android güncelleme paketi izin verilen boyutu aşıyor.")
                }

                val digest = MessageDigest.getInstance("SHA-256")
                var total = 0L
                connection.inputStream.use { input ->
                    FileOutputStream(partial).use { output ->
                        val buffer = ByteArray(64 * 1024)
                        while (true) {
                            val count = input.read(buffer)
                            if (count < 0) break
                            total += count
                            if (total > 512L * 1024L * 1024L) {
                                throw IllegalStateException("Android güncelleme paketi 512 MiB sınırını aşıyor.")
                            }
                            digest.update(buffer, 0, count)
                            output.write(buffer, 0, count)
                        }
                        output.fd.sync()
                    }
                }
                val actualHash = digest.digest().joinToString("") {
                    (it.toInt() and 0xff).toString(16).padStart(2, '0')
                }
                if (total < 1024L * 1024L || actualHash != update.apkSha256) {
                    throw IllegalStateException("APK SHA-256 doğrulaması başarısız. Paket kurulmayacak.")
                }

                val signatureFlags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    PackageManager.GET_SIGNING_CERTIFICATES
                } else {
                    @Suppress("DEPRECATION")
                    PackageManager.GET_SIGNATURES
                }
                val candidateInfo = packageManager.getPackageArchiveInfo(partial.absolutePath, signatureFlags)
                    ?: throw SecurityException("İndirilen APK okunamadı.")
                if (candidateInfo.packageName != packageName) {
                    throw SecurityException("Güncelleme paketi farklı bir uygulamaya ait.")
                }
                @Suppress("DEPRECATION")
                val installedInfo = packageManager.getPackageInfo(packageName, signatureFlags)
                val candidateSigners = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    val signing = candidateInfo.signingInfo ?: throw SecurityException("APK imza bilgisi yok.")
                    if (signing.hasMultipleSigners()) throw SecurityException("Çok imzalı güncelleme paketi reddedildi.")
                    signing.apkContentsSigners
                } else candidateInfo.signatures ?: emptyArray()
                val installedSigners = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    val signing = installedInfo.signingInfo ?: throw SecurityException("Kurulu uygulamanın imzası okunamadı.")
                    if (signing.hasMultipleSigners()) throw SecurityException("Kurulu uygulama çoklu imzalı.")
                    signing.apkContentsSigners
                } else installedInfo.signatures ?: emptyArray()
                fun signerFingerprints(signers: Array<android.content.pm.Signature>) =
                    signers.map { signer ->
                        MessageDigest.getInstance("SHA-256").digest(signer.toByteArray())
                            .joinToString("") { byte -> (byte.toInt() and 0xff).toString(16).padStart(2, '0') }
                    }.toSet()
                if (candidateSigners.isEmpty() || signerFingerprints(candidateSigners) != signerFingerprints(installedSigners)) {
                    throw SecurityException("Güncelleme imzası kurulu Stagepulse uygulamasıyla eşleşmiyor.")
                }
                target.delete()
                if (!partial.renameTo(target)) {
                    throw IllegalStateException("Doğrulanan Android APK dosyası hazırlanamadı.")
                }
                downloadedApk = target
            } catch (error: Exception) {
                failure = error.message ?: "Android güncellemesi indirilemedi."
                android.util.Log.e("StagepulseUpdate", "Android güncellemesi indirilemedi veya doğrulanamadı", error)
            } finally {
                connection?.disconnect()
                partial.delete()
            }

            val apk = downloadedApk
            val error = failure
            runOnUiThread {
                updateDownloadInProgress = false
                if (apk != null) openMobileUpdateInstaller(apk)
                else Toast.makeText(this, error ?: "Android güncellemesi kurulamadı.", Toast.LENGTH_LONG).show()
            }
        }.start()
    }

    private fun openMobileUpdateInstaller(apk: File) {
        try {
            val uri = FileProvider.getUriForFile(this, packageName + ".fileprovider", apk)
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, "application/vnd.android.package-archive")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(intent)
        } catch (error: Exception) {
            android.util.Log.e("StagepulseUpdate", "Android paket kurucusu açılamadı", error)
            Toast.makeText(this, "Android kurulum ekranı açılamadı: " + error.message, Toast.LENGTH_LONG).show()
        }
    }

    private fun performMobileRequest(action: String, payload: JSONObject): JSONObject {
        when (action) {
            "check_updates" -> return checkMobileAppUpdates()
            "install_update" -> return queueMobileAppUpdate(payload.optString("manifest"))
            "ai_chat" -> return requestMobileAi(payload)
            "app_info" -> {
                val cached = readSecret("account_context")?.let { JSONObject(it) }
                val validatedAt = readSecret("validated_at")?.toLongOrNull() ?: 0L
                val licensed = cached?.optJSONObject("licensed")
                val cachedUserId = cached?.optJSONObject("user")?.optString("id").orEmpty()
                val storedSession = readSecret("session")?.let { JSONObject(it) }
                val sessionUserId = storedSession?.optJSONObject("user")?.optString("id").orEmpty()
                val sameUser = sessionUserId.isBlank() || cachedUserId == sessionUserId
                val expiresAt = licensed?.optString("expires_at").orEmpty()
                val notExpired = expiresAt.isBlank() || runCatching {
                    java.time.Instant.parse(expiresAt).toEpochMilli() > System.currentTimeMillis()
                }.getOrDefault(false)
                val now = System.currentTimeMillis()
                val validCache = licensed?.optBoolean("active", false) == true && sameUser
                    && validatedAt > 0L && validatedAt <= now + 5L * 60L * 1000L
                    && now - validatedAt <= 7L * 24L * 60L * 60L * 1000L && notExpired
                return JSONObject()
                    .put("platform", "android")
                    .put("version", BuildConfig.VERSION_NAME)
                    .put("cached_license", if (validCache) licensed ?: JSONObject() else JSONObject().put("active", false))
                    .put("offline_cache", validCache)
            }
            "auth_login" -> {
                val email = payload.optString("email").trim()
                val password = payload.optString("password")
                if (email.isBlank() || password.isBlank()) throw IllegalArgumentException("E-posta ve şifre gerekli.")
                val session = requestSupabase(
                    "POST", "/auth/v1/token?grant_type=password",
                    JSONObject().put("email", email).put("password", password)
                )
                saveAuthSession(session)
                return JSONObject().put("context", fetchMobileContext())
            }
            "auth_signup" -> {
                val email = payload.optString("email").trim()
                val password = payload.optString("password")
                val displayName = payload.optString("display_name").trim().take(120)
                if (email.isBlank() || password.length < 8) throw IllegalArgumentException("Geçerli e-posta ve en az 8 karakterli şifre gerekli.")
                val signUp = requestSupabase(
                    "POST", "/auth/v1/signup",
                    JSONObject()
                        .put("email", email)
                        .put("password", password)
                        .put("data", JSONObject().put("display_name", displayName))
                )
                val hasSession = signUp.optJSONObject("session")?.optString("access_token").orEmpty().isNotBlank()
                    || signUp.optString("access_token").isNotBlank()
                val session = signUp.optJSONObject("session") ?: signUp
                if (hasSession) saveAuthSession(session)
                return JSONObject()
                    .put("ok", true)
                    .put("session_created", hasSession)
                    .put("message", if (hasSession) "Öğrenci hesabı oluşturuldu." else "Hesap oluşturuldu. E-posta doğrulamasını tamamla, ardından giriş yap.")
            }
            "auth_context" -> return JSONObject().put("context", fetchMobileContext())
            "auth_restore" -> return restoreMobileAuthSession()
            "auth_logout" -> {
                try {
                    val token = readSecret("session")?.let { JSONObject(it).optString("access_token") }
                    if (!token.isNullOrBlank()) requestSupabase("POST", "/auth/v1/logout", bearer = token)
                } catch (_: Exception) { }
                secureSessionPrefs.edit().clear().apply()
                return JSONObject().put("ok", true)
            }
            "license_activate" -> {
                val key = payload.optString("key").trim()
                if (key.isBlank()) throw IllegalArgumentException("Lisans anahtarı gerekli.")
                val result = callSesEdge("license_activate", JSONObject().put("key", key))
                val context = fetchMobileContext()
                return JSONObject().put("context", context).put("activation", JSONObject().put("result", result.optJSONObject("result") ?: JSONObject()))
            }
            "license_create" -> {
                val body = JSONObject()
                    .put("label", payload.optString("label"))
                    .put("plan_code", payload.optString("plan_code", "student"))
                    .put("max_activations", payload.optInt("max_activations", 1))
                    .put("expires_days", payload.optInt("expires_days", 365))
                    .put("customer_name", payload.optString("customer_name"))
                    .put("customer_email", payload.optString("customer_email"))
                    .put("payment_method", payload.optString("payment_method", "cash"))
                    .put("payment_status", payload.optString("payment_status", "unpaid"))
                    .put("amount", payload.optDouble("amount", 0.0))
                    .put("currency", payload.optString("currency", "TRY"))
                    .put("payment_reference", payload.optString("payment_reference"))
                    .put("bundle_code", payload.optString("bundle_code", "start"))
                return callSesEdge("license_create", body)
            }
            "store_get" -> return callSesEdge("store_get")
            "store_update" -> return callSesEdge("store_update", JSONObject()
                .put("price", payload.optDouble("price", 2500.0))
                .put("bank_name", payload.optString("bank_name"))
                .put("account_holder", payload.optString("account_holder"))
                .put("iban", payload.optString("iban"))
                .put("payment_instructions", payload.optString("payment_instructions"))
                .put("contact_phone", payload.optString("contact_phone"))
            )
            "purchase_submit" -> return callSesEdge("purchase_submit", JSONObject()
                .put("customer_name", payload.optString("customer_name"))
                .put("customer_phone", payload.optString("customer_phone"))
                .put("transfer_reference", payload.optString("transfer_reference"))
                .put("customer_note", payload.optString("customer_note"))
            )
            "purchase_list" -> return callSesEdge("purchase_list")
            "purchase_review" -> return callSesEdge("purchase_review", JSONObject()
                .put("purchase_id", payload.optString("purchase_id"))
                .put("decision", payload.optString("decision"))
                .put("admin_note", payload.optString("admin_note"))
            )
            "license_list" -> return callSesEdge("license_list")
            "license_payment_update" -> return callSesEdge(
                "license_payment_update",
                JSONObject().put("license_id", payload.optString("license_id")).put("payment_status", payload.optString("payment_status"))
            )
            "license_revoke" -> return callSesEdge("license_revoke", JSONObject().put("license_id", payload.optString("license_id")))
            "teacher_students" -> return callSesEdge("teacher_students")
            "progress_get" -> return callSesEdge("progress_get", JSONObject().put("student_user_id", payload.optString("student_user_id")))
            "progress_mark" -> return callSesEdge(
                "progress_mark",
                JSONObject()
                    .put("student_user_id", payload.optString("student_user_id"))
                    .put("module_id", payload.optString("module_id"))
                    .put("completed", payload.optBoolean("completed"))
                    .put("teacher_note", payload.optString("teacher_note"))
            )
            else -> throw IllegalArgumentException("Android hesap köprüsünde desteklenmeyen işlem: $action")
        }
    }

    private fun deliverMobileResponse(callbackId: String, result: JSONObject) {
        if (!callbackId.matches(Regex("[A-Za-z0-9_-]{1,64}"))) return
        val script = "window.__stagepulseAndroidResolve && window.__stagepulseAndroidResolve(" +
            JSONObject.quote(callbackId) + "," + JSONObject.quote(result.toString()) + ");"
        webView.evaluateJavascript(script, null)
    }

    private inner class AndroidBridge {
        @JavascriptInterface
        fun requestRuntimePermission(permission: String, callbackId: String) {
            val allowed = setOf(Manifest.permission.RECORD_AUDIO)
            if (!callbackId.matches(Regex("[A-Za-z0-9_-]{1,64}")) || permission !in allowed) return
            runOnUiThread {
                if (checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED) {
                    deliverRuntimePermissionResult(callbackId, true)
                    return@runOnUiThread
                }
                pendingRuntimePermissionCallbackId?.let { previous ->
                    deliverRuntimePermissionResult(previous, false, "Önceki izin isteği iptal edildi.")
                }
                pendingRuntimePermission = permission
                pendingRuntimePermissionCallbackId = callbackId
                requestPermissions(arrayOf(permission), REQUEST_NATIVE_MEDIA_PERMISSION)
            }
        }

        @JavascriptInterface
        fun request(action: String, payloadJson: String, callbackId: String) {
            if (!callbackId.matches(Regex("[A-Za-z0-9_-]{1,64}"))) return
            bridgeExecutor.execute {
                val result = try {
                    performMobileRequest(action.take(40), JSONObject(payloadJson.take(20000)))
                } catch (e: Exception) {
                    JSONObject().put("__error", e.message ?: "Mobil istek başarısız.")
                }
                bridgeHandler.post { deliverMobileResponse(callbackId, result) }
            }
        }


        @JavascriptInterface
        fun saveBase64File(fileName: String, mimeType: String, encoded: String): Boolean {
            if (encoded.length > 24 * 1024 * 1024) return false
            val safeExtensions = mapOf(
                "application/pdf" to ".pdf",
                "application/json" to ".json",
                "text/plain" to ".txt",
                "text/csv" to ".csv",
                "audio/wav" to ".wav",
                "audio/x-wav" to ".wav"
            )
            val safeExt = safeExtensions[mimeType] ?: return false
            val safeName = "Stagepulse_export" + safeExt
            return try {
                val bytes = Base64.decode(encoded, Base64.DEFAULT)
                val values = ContentValues().apply {
                    put("_display_name", safeName)
                    put("mime_type", mimeType)
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        put("relative_path", "Download/Stagepulse")
                        put("is_pending", 1)
                    }
                }
                val collection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI
                } else {
                    MediaStore.Files.getContentUri("external")
                }
                val uri = contentResolver.insert(collection, values) ?: return false
                try {
                    contentResolver.openOutputStream(uri, "w")?.use { it.write(bytes) }
                        ?: throw IllegalStateException("Dosya akışı açılamadı.")
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        val ready = ContentValues().apply { put("is_pending", 0) }
                        contentResolver.update(uri, ready, null, null)
                    }
                    runOnUiThread {
                        Toast.makeText(this@MainActivity, "Dosya İndirilenler/Stagepulse klasörüne kaydedildi.", Toast.LENGTH_LONG).show()
                    }
                    true
                } catch (e: Exception) {
                    contentResolver.delete(uri, null, null)
                    throw e
                }
            } catch (e: Exception) {
                android.util.Log.e("StagepulseExport", "Dışa aktarma kaydedilemedi", e)
                runOnUiThread {
                    Toast.makeText(this@MainActivity, "Dosya kaydedilemedi: ${e.message}", Toast.LENGTH_LONG).show()
                }
                false
            }
        }

        @JavascriptInterface
        fun openPdf(fileName: String): Boolean {
            if (!allowedStudentPdfs.contains(fileName)) return false
            return try {
                val folder = File(cacheDir, "pdfs").apply { mkdirs() }
                val target = File(folder, fileName)
                if (!target.isFile || target.length() == 0L) {
                    assets.open("egitim_paketleri/$fileName").use { input ->
                        FileOutputStream(target).use { output -> input.copyTo(output) }
                    }
                }
                val uri = FileProvider.getUriForFile(
                    this@MainActivity, "${packageName}.fileprovider", target
                )
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "application/pdf")
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                runOnUiThread {
                    try {
                        startActivity(Intent.createChooser(intent, "PDF görüntüleyici seç"))
                    } catch (_: ActivityNotFoundException) {
                        Toast.makeText(this@MainActivity, "Cihazda PDF görüntüleyici bulunamadı.", Toast.LENGTH_LONG).show()
                    }
                }
                true
            } catch (e: Exception) {
                android.util.Log.e("StagepulsePDF", "PDF açılamadı: $fileName", e)
                runOnUiThread { Toast.makeText(this@MainActivity, "PDF açılamadı: ${e.message}", Toast.LENGTH_LONG).show() }
                false
            }
        }
    }


    @Deprecated("Required for WebView file chooser compatibility.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_FILE_CHOOSER) {
            val callback = fileChooserCallback ?: return
            fileChooserCallback = null
            val uris = if (resultCode == RESULT_OK && data != null) {
                val clip = data.clipData
                when {
                    clip != null -> Array(clip.itemCount) { i -> clip.getItemAt(i).uri }
                    data.data != null -> arrayOf(data.data!!)
                    else -> null
                }
            } else null
            callback.onReceiveValue(uris)
        }
    }

    @Deprecated("Required for WebView media permission compatibility.")
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_NATIVE_MEDIA_PERMISSION) {
            val permission = pendingRuntimePermission
            val callbackId = pendingRuntimePermissionCallbackId
            pendingRuntimePermission = null
            pendingRuntimePermissionCallbackId = null
            val granted = permission != null &&
                checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED
            if (callbackId != null) {
                deliverRuntimePermissionResult(
                    callbackId,
                    granted,
                    if (granted) "" else "Android mikrofon izni verilmedi. Uygulama ayarlarından mikrofon iznini verip yeniden dene."
                )
            }
            return
        }
        if (requestCode != REQUEST_MEDIA_PERMISSION) return

        val request = pendingMediaPermission
        pendingMediaPermission = null
        if (request == null) return

        val grantedResources = buildList {
            if (request.resources.contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE) &&
                checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                add(PermissionRequest.RESOURCE_AUDIO_CAPTURE)
            }
        }
        if (grantedResources.isNotEmpty()) {
            configureAudioForCapture()
            request.grant(grantedResources.toTypedArray())
            if (grantedResources.size < request.resources.distinct().size) {
                Toast.makeText(this, "İstenen medya izinlerinden bazıları verilmedi.", Toast.LENGTH_SHORT).show()
            }
        } else {
            request.deny()
            Toast.makeText(this, "Mikrofon izni verilmedi.", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onPause() {
        if (::webView.isInitialized) webView.onPause()
        super.onPause()
    }

    override fun onResume() {
        super.onResume()
        if (::webView.isInitialized) webView.onResume()
        if (pendingInstallerPermissionRequest) {
            pendingInstallerPermissionRequest = false
            val update = pendingUpdateManifest
            pendingUpdateManifest = null
            if (update != null && (Build.VERSION.SDK_INT < Build.VERSION_CODES.O ||
                packageManager.canRequestPackageInstalls())) {
                downloadAndInstallMobileUpdate(update)
            } else {
                Toast.makeText(this, "Güncelleme kurulumu için izin verilmedi.", Toast.LENGTH_LONG).show()
            }
        }
    }

    override fun onDestroy() {
        pendingMediaPermission?.deny()
        pendingMediaPermission = null
        bridgeExecutor.shutdownNow()
        restoreAudioMode()
        super.onDestroy()
    }

    @Deprecated("Android back callback is preferred on newer APIs.")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    companion object {
        private const val REQUEST_FILE_CHOOSER = 8101
        private const val REQUEST_MEDIA_PERMISSION = 8102
        private const val REQUEST_NATIVE_MEDIA_PERMISSION = 8103
        private const val SUPABASE_URL = "https://itasctyjzyewcykozuex.supabase.co"
        private const val SUPABASE_PUBLISHABLE_KEY = "sb_publishable_tP3CMhVAjv6FNtrkYfVEOA_dbF9m8Jb"
    }
}
