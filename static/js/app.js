// CINEFORGE AI - Client Application Controller
document.addEventListener("DOMContentLoaded", () => {
  // DOM References
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const filePreviewCard = document.getElementById("filePreviewCard");
  const fileNameLabel = document.getElementById("fileNameLabel");
  const fileMetaLabel = document.getElementById("fileMetaLabel");
  const changeFileBtn = document.getElementById("changeFileBtn");
  
  const presetPills = document.querySelectorAll(".preset-pill");
  const promptInput = document.getElementById("promptInput");
  const startProcessBtn = document.getElementById("startProcessBtn");
  
  const terminalHud = document.getElementById("terminalHud");
  const hudPct = document.getElementById("hudPct");
  const engineStatus = document.getElementById("engineStatus");
  
  const videoPlayer = document.getElementById("mainVideoPlayer") || document.getElementById("videoPlayer");
  const playerOverlayTag = document.getElementById("playerOverlayTag");
  const videoBadge = document.getElementById("videoBadge");
  const tabEdited = document.getElementById("tabEdited");
  const tabRaw = document.getElementById("tabRaw");
  const downloadBtn = document.getElementById("downloadMasterBtn") || document.getElementById("downloadBtn");
  
  const statTimeSaved = document.getElementById("statTimeSaved");
  const statCuts = document.getElementById("statCuts");
  const statZooms = document.getElementById("statZooms");
  
  // Precision Controls
  const aspectRatioSelect = document.getElementById("aspectRatioSelect");
  const musicModeSelect = document.getElementById("musicModeSelect");
  const cutModeSelect = document.getElementById("cutModeSelect");
  const subtitleLangSelect = document.getElementById("subtitleLangSelect");
  const subtitleStyleSelect = document.getElementById("subtitleStyleSelect");
  const progressBarToggle = document.getElementById("progressBarToggle");
  const hookFlashToggle = document.getElementById("hookFlashToggle");

  // Viral Kit Elements
  const viralKitPanel = document.getElementById("viralKitPanel");
  const viralTitlesList = document.getElementById("viralTitlesList");
  const ytDescOutput = document.getElementById("ytDescOutput");
  const copyYtDescBtn = document.getElementById("copyYtDescBtn");
  const linkedinPostOutput = document.getElementById("linkedinPostOutput");
  const copyLinkedInBtn = document.getElementById("copyLinkedInBtn");

  // Settings Modal
  const openSettingsBtn = document.getElementById("openSettingsBtn");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const settingsModal = document.getElementById("settingsModal");
  const proxyUrlInput = document.getElementById("proxyUrlInput");
  const apiKeyInput = document.getElementById("apiKeyInput");
  const modelSelect = document.getElementById("modelSelect");
  const saveSettingsBtn = document.getElementById("saveSettingsBtn");
  const testProxyBtn = document.getElementById("testProxyBtn");
  const proxyBadge = document.getElementById("proxyBadge");

  // State
  let uploadedFilename = null;
  let activePreset = "viral_short";
  let activeJobId = null;
  let pollInterval = null;
  let lastLogCount = 0;
  let rawStreamUrl = null;
  let editedStreamUrl = null;
  let masterDownloadUrl = null;

  // Restore Settings from LocalStorage
  proxyUrlInput.value = localStorage.getItem("cineforge_proxy_url") || "http://127.0.0.1:8081/v1/chat/completions";
  apiKeyInput.value = localStorage.getItem("cineforge_api_key") || "";
  if (localStorage.getItem("cineforge_model")) {
    modelSelect.value = localStorage.getItem("cineforge_model");
  }

  // Check Proxy Heartbeat
  checkProxyHeartbeat();
  async function checkProxyHeartbeat() {
    try {
      const resp = await fetch("/api/proxy/status");
      const data = await resp.json();
      if (data.online) {
        proxyBadge.style.display = "flex";
        proxyBadge.innerHTML = `<span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--accent-cyan);"></span> B1 PROXY: 8081 ACTIVE`;
      } else {
        proxyBadge.innerHTML = `<span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#FF453A;"></span> B1 PROXY: OFFLINE`;
      }
    } catch {
      proxyBadge.innerHTML = `<span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#FF453A;"></span> B1 PROXY: UNREACHABLE`;
    }
  }

  // Modal Controls
  openSettingsBtn.addEventListener("click", () => settingsModal.classList.add("active"));
  closeSettingsBtn.addEventListener("click", () => settingsModal.classList.remove("active"));
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) settingsModal.classList.remove("active");
  });

  saveSettingsBtn.addEventListener("click", () => {
    localStorage.setItem("cineforge_proxy_url", proxyUrlInput.value.trim());
    localStorage.setItem("cineforge_api_key", apiKeyInput.value.trim());
    localStorage.setItem("cineforge_model", modelSelect.value);
    settingsModal.classList.remove("active");
    appendLog(100, `Settings updated: Using model "${modelSelect.value}" via proxy`);
    checkProxyHeartbeat();
  });

  if (testProxyBtn) {
    testProxyBtn.addEventListener("click", async () => {
      testProxyBtn.textContent = "Testing...";
      try {
        const resp = await fetch("/api/proxy/status");
        const data = await resp.json();
        if (data.online) {
          alert(`Proxy Connection OK! Models available: ${data.models.join(", ")}`);
        } else {
          alert(`Proxy offline or error: ${data.error}`);
        }
      } catch (e) {
        alert(`Test failed: ${e.message}`);
      } finally {
        testProxyBtn.textContent = "Test Proxy Connection";
      }
    });
  }

  // Preset Selection
  presetPills.forEach(pill => {
    pill.addEventListener("click", () => {
      presetPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activePreset = pill.getAttribute("data-preset");
      appendLog(0, `Preset loaded: ${pill.querySelector(".preset-name").textContent.trim()}`);
    });
  });

  // Drag and Drop Ingestion
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("drag-active");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-active"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-active");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  changeFileBtn.addEventListener("click", () => {
    fileInput.click();
  });

  async function handleFileUpload(file) {
    appendLog(1, `Ingesting raw footage: "${file.name}" (${(file.size / (1024 * 1024)).toFixed(1)} MB)...`);
    const formData = new FormData();
    formData.append("file", file);

    try {
      dropzone.style.opacity = "0.5";
      const resp = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      uploadedFilename = data.filename;
      rawStreamUrl = `/api/stream/upload/${uploadedFilename}`;

      // Update UI
      dropzone.style.display = "none";
      filePreviewCard.style.display = "flex";
      fileNameLabel.textContent = data.original_name;
      fileMetaLabel.textContent = `${data.size_mb} MB • Ready for AI Director`;
      dropzone.style.opacity = "1";

      appendLog(3, `Raw footage ingested successfully into studio repository. File ID: ${uploadedFilename}`);

      // Auto load raw in player preview
      loadVideoPlayer(rawStreamUrl, "RAW INGESTION");
      tabRaw.click();

      // Highlight the Action Button
      startProcessBtn.style.boxShadow = "0 0 25px rgba(0, 240, 255, 0.6)";
      startProcessBtn.textContent = "⚡ CLICK HERE TO INITIALIZE AI EDITING AGENT";
      setTimeout(() => {
        startProcessBtn.textContent = "INITIALIZE AI EDITING AGENT";
      }, 5000);

    } catch (err) {
      dropzone.style.opacity = "1";
      appendLog(0, `ERROR: ${err.message}`);
      alert(`Upload error: ${err.message}`);
    }
  }

  // Copy Buttons for Social Kit
  if (copyYtDescBtn) {
    copyYtDescBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(ytDescOutput.value);
      copyYtDescBtn.textContent = "Copied!";
      setTimeout(() => copyYtDescBtn.textContent = "Copy Description", 2000);
    });
  }

  if (copyLinkedInBtn) {
    copyLinkedInBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(linkedinPostOutput.value);
      copyLinkedInBtn.textContent = "Copied!";
      setTimeout(() => copyLinkedInBtn.textContent = "Copy LinkedIn Post", 2000);
    });
  }

  // Start Autonomous Process
  startProcessBtn.addEventListener("click", async () => {
    if (!uploadedFilename) {
      alert("Please upload raw footage first.");
      return;
    }

    startProcessBtn.disabled = true;
    startProcessBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
        <line x1="12" y1="2" x2="12" y2="6"></line>
        <line x1="12" y1="18" x2="12" y2="22"></line>
        <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
        <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
        <line x1="2" y1="12" x2="6" y2="12"></line>
        <line x1="18" y1="12" x2="22" y2="12"></line>
        <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
        <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
      </svg>
      AI AGENT EDITING IN PROGRESS...
    `;

    hudPct.textContent = "INITIALIZING";
    engineStatus.textContent = "AGENT EXECUTING EDL...";

    const subLang = subtitleLangSelect ? subtitleLangSelect.value : "auto_en_hi";
    const subStyle = subtitleStyleSelect ? subtitleStyleSelect.value : "hormozi";
    const progBar = progressBarToggle ? progressBarToggle.checked : true;
    const hookFl = hookFlashToggle ? hookFlashToggle.checked : true;

    const payload = {
      raw_video_filename: uploadedFilename,
      prompt: promptInput.value.trim(),
      preset: activePreset,
      aspect_ratio: aspectRatioSelect ? aspectRatioSelect.value : "auto",
      music_mode: musicModeSelect ? musicModeSelect.value : "auto",
      cut_mode: cutModeSelect ? cutModeSelect.value : "ai_smart",
      captions_enabled: subLang !== "none",
      subtitle_lang: subLang,
      subtitle_style: subStyle,
      progress_bar: progBar,
      hook_flash: hookFl,
      gemini_api_key: localStorage.getItem("cineforge_api_key") || "",
      gemini_proxy: localStorage.getItem("cineforge_proxy_url") || "http://127.0.0.1:8081/v1/chat/completions"
    };

    try {
      const resp = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || "Processing trigger failed");
      }

      activeJobId = data.job_id;
      lastLogCount = 0;
      appendLog(5, `Job dispatched to AI Director: ${activeJobId}`);

      // Start Polling
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(pollJobStatus, 800);

    } catch (err) {
      startProcessBtn.disabled = false;
      startProcessBtn.innerHTML = `INITIALIZE AI EDITING AGENT`;
      appendLog(0, `ERROR: ${err.message}`);
      alert(`Error starting pipeline: ${err.message}`);
    }
  });

  async function pollJobStatus() {
    if (!activeJobId) return;

    try {
      const resp = await fetch(`/api/status/${activeJobId}`);
      if (!resp.ok) return;
      const job = await resp.json();

      // Update Percentage
      hudPct.textContent = `${job.progress}%`;

      // Append new logs
      if (job.logs && job.logs.length > lastLogCount) {
        for (let i = lastLogCount; i < job.logs.length; i++) {
          const l = job.logs[i];
          appendLog(l.pct, l.msg, l.time);
        }
        lastLogCount = job.logs.length;
      }

      // Check Completion
      if (job.status === "completed") {
        clearInterval(pollInterval);
        startProcessBtn.disabled = false;
        startProcessBtn.innerHTML = `INITIALIZE AI EDITING AGENT`;
        engineStatus.textContent = "RENDER FINISHED";
        hudPct.textContent = "100%";

        const res = job.result;
        editedStreamUrl = `/api/stream/export/${res.output_filename}`;
        masterDownloadUrl = `/api/download/${res.output_filename}`;

        // Update Stats
        statTimeSaved.textContent = `${res.time_saved_seconds}s`;
        statCuts.textContent = `${res.total_cuts}`;
        statZooms.textContent = `${res.total_zooms}`;

        // Enable download button
        downloadBtn.style.display = "inline-flex";
        downloadBtn.onclick = () => {
          window.location.href = masterDownloadUrl;
        };

        // Populate Viral Distribution Kit
        if (res.social_package && viralKitPanel) {
          viralKitPanel.style.display = "block";
          viralTitlesList.innerHTML = "";
          const titles = res.social_package.youtube_titles || [];
          titles.forEach(t => {
            const btn = document.createElement("button");
            btn.className = "btn-secondary";
            btn.style.cssText = "text-align: left; padding: 6px 10px; font-size: 11px; display: flex; justify-content: space-between; align-items: center; background: var(--surface-2); border-color: var(--hairline); width: 100%; cursor: pointer;";
            btn.innerHTML = `<span style="font-weight: 500;">${escapeHtml(t)}</span><span style="color: var(--accent-cyan); font-size: 10px; font-family: var(--font-mono); font-weight: 600;">COPY</span>`;
            btn.onclick = () => {
              navigator.clipboard.writeText(t);
              btn.querySelector("span:last-child").textContent = "COPIED!";
              setTimeout(() => btn.querySelector("span:last-child").textContent = "COPY", 2000);
            };
            viralTitlesList.appendChild(btn);
          });

          if (ytDescOutput) ytDescOutput.value = res.social_package.youtube_description || "";
          if (linkedinPostOutput) linkedinPostOutput.value = res.social_package.linkedin_post || "";
        }

        // Switch player to edited video
        tabEdited.click();
        appendLog(100, `🎬 MASTER VIDEO COMPLETE! Ready for preview and export.`);

      } else if (job.status === "failed") {
        clearInterval(pollInterval);
        startProcessBtn.disabled = false;
        startProcessBtn.innerHTML = `INITIALIZE AI EDITING AGENT`;
        engineStatus.textContent = "ERROR";
        appendLog(job.progress, `❌ FAILED: ${job.error}`);
        alert(`Editing failed: ${job.error}`);
      }

    } catch (err) {
      console.error("Poll error:", err);
    }
  }

  // Terminal Log Appender
  function appendLog(pct, msg, timeVal = null) {
    const entry = document.createElement("div");
    entry.className = "log-entry";
    
    const now = timeVal !== null ? `${timeVal}s` : `${(Date.now() / 1000 % 100).toFixed(1)}s`;
    
    const isHighlight = msg.includes("Master") || msg.includes("complete") || msg.includes("EDL") || msg.includes("Cuts") || msg.includes("Viral");
    
    entry.innerHTML = `
      <span class="log-time">[${now}]</span>
      <span class="log-pct">${pct}%</span>
      <span class="log-msg ${isHighlight ? 'highlight' : ''}">${escapeHtml(msg)}</span>
    `;
    terminalHud.appendChild(entry);
    terminalHud.scrollTop = terminalHud.scrollHeight;
  }

  function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // Video Player View Toggles
  tabEdited.addEventListener("click", () => {
    tabEdited.classList.add("active");
    tabRaw.classList.remove("active");
    if (editedStreamUrl) {
      loadVideoPlayer(editedStreamUrl, "AI MASTERED (1080P)");
    }
  });

  tabRaw.addEventListener("click", () => {
    tabRaw.classList.add("active");
    tabEdited.classList.remove("active");
    if (rawStreamUrl) {
      loadVideoPlayer(rawStreamUrl, "RAW FOOTAGE");
    }
  });

  function loadVideoPlayer(url, badgeText) {
    if (playerOverlayTag) playerOverlayTag.style.display = "none";
    videoPlayer.style.display = "block";
    videoBadge.style.display = "inline-block";
    videoBadge.textContent = badgeText;
    
    videoPlayer.src = url;
    videoPlayer.load();
    videoPlayer.play().catch(() => {});
  }
});
