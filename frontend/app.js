const questionInput = document.getElementById("questionInput");
const topKInput = document.getElementById("topKInput");
const fileInput = document.getElementById("fileInput");
const categoryInput = document.getElementById("categoryInput");
const sourceInput = document.getElementById("sourceInput");
const askBtn = document.getElementById("askBtn");
const searchBtn = document.getElementById("searchBtn");
const statsBtn = document.getElementById("statsBtn");
const ingestBtn = document.getElementById("ingestBtn");
const healthBtn = document.getElementById("healthBtn");
const answerOutput = document.getElementById("answerOutput");
const referencesOutput = document.getElementById("referencesOutput");
const diagnosticsOutput = document.getElementById("diagnosticsOutput");
const statusText = document.getElementById("statusText");
const backendBadge = document.getElementById("backendBadge");
const navItems = document.querySelectorAll(".nav-item");

function pretty(data) {
  return JSON.stringify(data, null, 2);
}

function setStatus(text) {
  statusText.textContent = text;
}

function setNavActive(targetId) {
  navItems.forEach((item) => {
    item.classList.toggle("active", item.dataset.target === targetId);
  });
}

function scrollToPanel(targetId) {
  const target = document.getElementById(targetId);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    setNavActive(targetId);
  }
}

function renderReferences(references = []) {
  if (!references.length) {
    referencesOutput.textContent = "暂无引用内容";
    return;
  }

  referencesOutput.innerHTML = references.map((item) => `
    <article class="reference-item">
      <strong>${item.title}</strong>
      <div class="reference-meta">分类：${item.category} | 相关度：${item.score}</div>
      <div class="reference-text">${item.excerpt}</div>
    </article>
  `).join("");
}

function renderAnswer(text) {
  answerOutput.textContent = text || "暂无回答结果";
}

function renderDiagnostics(data) {
  diagnosticsOutput.textContent = pretty(data);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

async function loadHealth() {
  const data = await fetchJson("/health");
  backendBadge.innerHTML = `模型：${data.llm_backend}<br>检索：${data.retrieval_backend}`;
  return data;
}

async function askQuestion() {
  try {
    setStatus("正在调用问答链路...");
    const payload = {
      question: questionInput.value.trim(),
      top_k: Number(topKInput.value || 4),
    };
    const data = await fetchJson("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderAnswer(data.answer);
    renderReferences(data.references || []);
    renderDiagnostics(data);
    setStatus("问答完成");
    await loadHealth();
    scrollToPanel("resultPanel");
  } catch (error) {
    renderAnswer("请求失败，请检查服务状态或输入内容。");
    renderReferences([]);
    renderDiagnostics({ error: String(error) });
    setStatus("问答失败");
  }
}

async function searchKnowledge() {
  try {
    setStatus("正在执行知识检索...");
    const query = encodeURIComponent(questionInput.value.trim());
    const topK = Number(topKInput.value || 4);
    const data = await fetchJson(`/search?query=${query}&top_k=${topK}`);
    renderAnswer("已完成知识检索，可根据右侧引用内容判断当前召回效果。");
    renderReferences(data.results || []);
    renderDiagnostics(data);
    setStatus("检索完成");
    scrollToPanel("resultPanel");
  } catch (error) {
    renderAnswer("知识检索失败。");
    renderReferences([]);
    renderDiagnostics({ error: String(error) });
    setStatus("检索失败");
  }
}

async function loadStats() {
  try {
    setStatus("正在读取知识统计...");
    const data = await fetchJson("/stats");
    renderAnswer(`当前知识库共有 ${data.total_documents} 条知识片段，已按分类完成索引。`);
    renderReferences([]);
    renderDiagnostics(data);
    setStatus("统计读取完成");
    scrollToPanel("resultPanel");
  } catch (error) {
    renderAnswer("读取知识统计失败。");
    renderReferences([]);
    renderDiagnostics({ error: String(error) });
    setStatus("统计读取失败");
  }
}

async function ingestDocument() {
  try {
    if (!fileInput.files.length) {
      throw new Error("请先选择要导入的文档");
    }
    setStatus("正在导入知识文档...");
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    form.append("category", categoryInput.value.trim() || "general");
    form.append("source", sourceInput.value.trim() || "企业内部资料");
    const data = await fetchJson("/ingest", { method: "POST", body: form });
    renderAnswer(`文档已导入知识库，共新增 ${data.imported_count} 条知识片段。`);
    renderReferences((data.titles || []).map((title, index) => ({
      title,
      category: categoryInput.value.trim() || "general",
      score: index + 1,
      excerpt: `导入来源类型：${data.source_type}`,
    })));
    renderDiagnostics(data);
    setStatus("导入完成");
    await loadHealth();
    scrollToPanel("resultPanel");
  } catch (error) {
    renderAnswer("知识文档导入失败。");
    renderReferences([]);
    renderDiagnostics({ error: String(error) });
    setStatus("导入失败");
  }
}

async function showDiagnostics() {
  try {
    setStatus("正在读取系统诊断...");
    const data = await loadHealth();
    renderAnswer("系统诊断已更新，可查看当前模型接入状态、检索后端和可用能力。 ");
    renderReferences([]);
    renderDiagnostics(data);
    setStatus("诊断读取完成");
    scrollToPanel("resultPanel");
  } catch (error) {
    renderAnswer("读取系统诊断失败。");
    renderReferences([]);
    renderDiagnostics({ error: String(error) });
    setStatus("诊断读取失败");
  }
}

navItems.forEach((item) => {
  item.addEventListener("click", () => scrollToPanel(item.dataset.target));
});

askBtn.addEventListener("click", askQuestion);
searchBtn.addEventListener("click", searchKnowledge);
statsBtn.addEventListener("click", loadStats);
ingestBtn.addEventListener("click", ingestDocument);
healthBtn.addEventListener("click", showDiagnostics);

questionInput.value = "本地模型部署需要做什么？";
loadHealth().catch((error) => {
  backendBadge.textContent = `系统连接失败：${error}`;
});
