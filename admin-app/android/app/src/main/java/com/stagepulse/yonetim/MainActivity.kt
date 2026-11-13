package com.stagepulse.yonetim

import android.app.Activity
import android.app.AlertDialog
import android.app.DownloadManager
import android.content.Intent
import android.net.Uri
import android.os.Environment
import android.graphics.Color
import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.JsPromptResult
import android.webkit.JsResult
import android.webkit.ValueCallback
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.text.InputType
import android.widget.EditText
import android.webkit.WebResourceRequest
import androidx.webkit.WebViewAssetLoader

class MainActivity : Activity() {
    private lateinit var web: WebView
    private lateinit var assetLoader: WebViewAssetLoader
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private val fileChooserRequestCode = 4107

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(11, 11, 12)
        window.navigationBarColor = Color.rgb(11, 11, 12)

        web = WebView(this)
        web.setBackgroundColor(Color.rgb(11, 11, 12))
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = true
        web.settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        web.settings.javaScriptCanOpenWindowsAutomatically = false
        web.settings.setSupportMultipleWindows(false)
        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest) =
                assetLoader.shouldInterceptRequest(request.url)

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val uri = request.url
                if (uri.scheme == "https" && uri.host == "appassets.androidplatform.net") return false
                if (uri.scheme == "https" && uri.host == "itasctyjzyewcykozuex.supabase.co"
                    && uri.path?.startsWith("/storage/v1/object/sign/sesm-education-pdfs/") == true) {
                    try {
                        val filename = android.webkit.URLUtil.guessFileName(uri.toString(), null, "application/pdf")
                        val download = DownloadManager.Request(uri)
                            .setTitle(filename)
                            .setMimeType("application/pdf")
                            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                            .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename)
                        (getSystemService(DOWNLOAD_SERVICE) as DownloadManager).enqueue(download)
                    } catch (_: Exception) { }
                }
                return true
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onJsConfirm(view: WebView?, url: String?, message: String?, result: JsResult?): Boolean {
                AlertDialog.Builder(this@MainActivity)
                    .setMessage(message ?: "Bu işlemi onaylıyor musun?")
                    .setPositiveButton("Onayla") { _, _ -> result?.confirm() }
                    .setNegativeButton("İptal") { _, _ -> result?.cancel() }
                    .setOnCancelListener { result?.cancel() }
                    .show()
                return true
            }

            override fun onJsPrompt(view: WebView?, url: String?, message: String?, defaultValue: String?, result: JsPromptResult?): Boolean {
                val input = EditText(this@MainActivity).apply {
                    setText(defaultValue ?: "")
                    inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
                    minLines = 2
                }
                AlertDialog.Builder(this@MainActivity)
                    .setTitle(message ?: "Bilgi düzenle")
                    .setView(input)
                    .setPositiveButton("Kaydet") { _, _ -> result?.confirm(input.text.toString()) }
                    .setNegativeButton("İptal") { _, _ -> result?.cancel() }
                    .setOnCancelListener { result?.cancel() }
                    .show()
                return true
            }

            override fun onShowFileChooser(view: WebView?, callback: ValueCallback<Array<Uri>>?, params: FileChooserParams?): Boolean {
                filePathCallback?.onReceiveValue(null)
                filePathCallback = callback
                return try {
                    val intent = params?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT)
                    intent.type = "application/pdf"
                    intent.addCategory(Intent.CATEGORY_OPENABLE)
                    intent.putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("application/pdf"))
                    startActivityForResult(intent, fileChooserRequestCode)
                    true
                } catch (_: Exception) {
                    filePathCallback?.onReceiveValue(null)
                    filePathCallback = null
                    false
                }
            }
        }
        web.setDownloadListener { url, _, contentDisposition, mimeType, _ ->
            try {
                val filename = android.webkit.URLUtil.guessFileName(url, contentDisposition, mimeType)
                val request = DownloadManager.Request(Uri.parse(url))
                    .setTitle(filename)
                    .setMimeType(mimeType ?: "application/pdf")
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                    .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename)
                (getSystemService(DOWNLOAD_SERVICE) as DownloadManager).enqueue(request)
            } catch (_: Exception) { }
        }
        setContentView(web)
        if (savedInstanceState == null) {
            web.loadUrl("https://appassets.androidplatform.net/assets/index.html")
        } else {
            web.restoreState(savedInstanceState)
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == fileChooserRequestCode) {
            val uri = if (resultCode == RESULT_OK) data?.data else null
            filePathCallback?.onReceiveValue(uri?.let { arrayOf(it) })
            filePathCallback = null
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        web.saveState(outState)
        super.onSaveInstanceState(outState)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (::web.isInitialized && web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        filePathCallback?.onReceiveValue(null)
        filePathCallback = null
        if (::web.isInitialized) web.destroy()
        super.onDestroy()
    }
}
