const pptxgen = require('pptxgenjs');

// ===== Claude Code 色調 =====
// 主橘 (signature coral/clay)
const C_PRIMARY    = "D97757";
// 深墨黑
const C_INK        = "1A1A1A";
// 奶油白背景
const C_CREAM      = "F5F0EB";
// 純白
const C_WHITE      = "FFFFFF";
// 中性暖灰
const C_WARM_GRAY  = "9C8B7A";
// 表頭深背景
const C_HEADER_BG  = "2D2A26";
// 隔行底色
const C_ZEBRA      = "EBE3D9";

const FONT_TITLE = "Georgia";
const FONT_BODY  = "Helvetica";

// ===== 內容資料 =====
const sections = [
  { id: 1, en: "Core Models", zh: "核心模型", rows: [
    ["LLM / Large Language Model", "大型語言模型", "Agent 的核心「大腦」，負責理解語言、生成內容、推理、規劃與決策。"],
    ["Foundation Model", "基礎模型", "可支援多種任務的大型通用模型，LLM 是其中一種。Agent 通常會把基礎模型包裝成可行動的系統。"],
    ["Chat Model", "對話模型", "以多輪訊息方式運作的模型，通常包含 system、user、assistant、tool 等角色訊息。"],
    ["Multimodal Model", "多模態模型", "可同時處理文字、圖片、音訊、影片、檔案等資料型態的模型。"],
    ["Reasoning Model", "推理模型", "較擅長多步驟分析、邏輯推導、數學、程式碼、規劃與複雜問題解決的模型。"],
    ["Token", "詞元", "模型處理文字的基本單位。輸入、輸出、上下文長度與費用通常都以 token 計算。"],
    ["Context Window", "上下文視窗", "模型一次可讀取的最大資訊量，包含指令、對話歷史、工具結果、文件內容等。"],
    ["Temperature", "溫度", "控制模型輸出的隨機性。溫度越高，回答越發散；越低，回答越穩定。"],
    ["Top-p", "核取樣", "控制模型從多大範圍的候選 token 中抽樣，用於調整輸出多樣性。"],
    ["Model Settings", "模型設定", "控制模型行為的參數，例如 temperature、max tokens、tool choice、response format 等。"],
  ]},
  { id: 2, en: "Prompt", zh: "提示詞", rows: [
    ["Prompt", "提示", "給模型的任務描述、資料、限制與輸出要求。"],
    ["System Prompt", "系統提示", "高優先級指令，用來定義 agent 的角色、規則、安全限制與行為模式。"],
    ["Developer Instructions", "開發者指令", "開發者提供的產品邏輯與執行規範，例如工具使用規則、輸出格式、禁止行為等。"],
    ["User Prompt", "使用者提示", "使用者在當前回合提出的問題、要求、資料或命令。"],
    ["Prompt Template", "提示模板", "可重複使用的提示格式，通常含有變數，例如 {task}、{context}、{format}。"],
    ["Assistant Prompt", "助理提示", "LLM 的回答。"],
    ["Dynamic Instructions", "動態指令", "根據使用者、任務、資料或 runtime 狀態即時產生的指令。"],
  ]},
  { id: 3, en: "Agent", zh: "代理", rows: [
    ["Agent", "AI 代理／智能代理", "能接收目標、理解上下文、推理、使用工具並完成多步驟任務的 AI 系統。"],
    ["AI Agent", "人工智慧代理", "泛指具備自主判斷與行動能力的 AI 程式，不只是回答問題，也能執行任務。"],
    ["LLM Agent", "大型語言模型代理", "以 LLM 為核心，搭配工具、記憶、規劃與外部系統的 agent。"],
    ["Agentic System", "代理式系統", "由一個或多個 agent、工具、資料源、記憶、流程與安全機制組成的完整系統。"],
    ["Agent Loop", "代理迴圈", "Agent 反覆進行「觀察 → 推理 → 行動 → 取得結果 → 再判斷」的流程。"],
    ["Run", "執行回合", "一次 agent 任務執行，可能包含多次模型呼叫、工具呼叫與中間狀態更新。"],
    ["Turn", "對話輪次", "使用者與 agent 的一次互動，例如使用者問一句、agent 回一句。"],
    ["Runner", "執行器", "負責執行 agent loop 的元件，管理模型呼叫、工具呼叫、錯誤處理與最終輸出。"],
    ["Orchestration", "編排", "安排多個 agent、工具、流程、狀態與資料來源如何協同工作。"],
    ["Workflow", "工作流", "一組明確步驟，例如「讀檔 → 分析 → 查資料 → 寫報告 → 驗證」。"],
    ["Single-Agent System", "單代理系統", "由一個 agent 負責整個任務，可能搭配多個工具。"],
    ["Multi-Agent System", "多代理系統", "多個 agent 分工合作，例如研究代理、程式代理、審查代理、客服代理。"],
    ["Supervisor Agent", "監督代理", "負責分派任務、協調其他 agent、整合結果與控制流程。"],
    ["Worker Agent", "工作代理", "負責執行具體子任務的 agent，例如查資料、寫程式、整理表格。"],
    ["Subagent", "子代理", "被主 agent 呼叫的次級 agent，通常專精於某個特定任務。"],
    ["Handoff", "交接", "一個 agent 將任務轉交給另一個更適合的 agent，例如客服代理轉給退款代理。"],
    ["Routing", "路由", "根據任務類型、使用者意圖、資料來源或風險等級，把請求導向合適的 agent 或工具。"],
    ["Agent as Tool", "代理作為工具", "將一個 agent 包裝成另一個 agent 可以呼叫的工具。"],
  ]},
  { id: 4, en: "Reasoning", zh: "推理", rows: [
    ["Reasoning", "推理", "Agent 分析問題、拆解任務、判斷下一步、整合資訊並產生答案的過程。"],
    ["Planning", "規劃", "Agent 在行動前安排步驟、工具、順序與停止條件。"],
    ["Task Decomposition", "任務分解", "將複雜任務拆成較小子任務，例如研究、計算、撰寫、驗證。"],
    ["Chain-of-Thought / CoT", "思維鏈", "多步驟推理的形式。實務上可幫助模型解決複雜問題，但不一定需要完整展示給使用者。"],
    ["ReAct", "推理與行動", "Reasoning + Acting 的模式，agent 一邊推理，一邊呼叫工具取得新資訊。"],
    ["Reflection", "反思", "Agent 檢查自己的中間結果或最終答案，並嘗試修正錯誤。"],
    ["Critic", "評審器", "專門檢查答案品質、邏輯、格式、安全性或事實正確性的模型或 agent。"],
    ["Verifier", "驗證器", "用來確認結果是否符合條件、資料是否正確、格式是否合格。"],
    ["Self-Consistency", "自洽性檢查", "透過多個推理路徑或候選答案，檢查結果是否一致。"],
    ["Grounding", "根據化", "要求回答必須基於文件、資料庫、工具結果或明確來源，而不是憑空生成。"],
    ["Hallucination", "幻覺", "模型產生看似合理但其實錯誤、無根據或捏造的內容。"],
  ]},
  { id: 5, en: "Tools", zh: "工具", rows: [
    ["Tool", "工具", "Agent 可呼叫的外部能力，例如搜尋、資料庫、API、計算器、程式執行、檔案處理等。"],
    ["Tool Use", "工具使用", "Agent 判斷何時需要使用外部工具，而不是只靠模型本身回答。"],
    ["Tool Calling", "工具呼叫", "模型輸出工具名稱與參數，由系統實際執行工具，再把結果回傳給模型。"],
    ["Function Calling", "函式呼叫", "Tool calling 的常見形式，模型根據函式 schema 產生參數，後端執行該函式。"],
    ["Function Tool", "函式工具", "以函式形式暴露給 agent 使用的工具，例如 get_weather(city)、query_database(sql)。"],
    ["Built-in Tool", "內建工具", "平台預先提供的工具，例如網頁搜尋、檔案搜尋、程式執行、圖片生成等。"],
    ["Hosted Tool", "託管工具", "由 AI 平台代管的工具，agent 可直接呼叫，不需要開發者自行部署。"],
    ["Tool Schema", "工具結構描述", "定義工具名稱、用途、輸入參數、型別、必填欄位與輸出格式。"],
    ["Tool Description", "工具說明", "告訴模型這個工具能做什麼、何時該用、限制是什麼。"],
    ["Tool Choice", "工具選擇", "控制模型是否可以自動選工具、必須用工具、不能用工具，或強制使用特定工具。"],
    ["Tool Result", "工具結果", "工具執行後回傳給模型的資料，例如查詢結果、搜尋結果、計算結果。"],
    ["Tool Error", "工具錯誤", "工具執行失敗時的錯誤，例如參數錯誤、權限不足、API 逾時。"],
    ["Tool Guardrail", "工具護欄", "在工具呼叫前後檢查輸入輸出，避免危險操作、越權或錯誤結果。"],
    ["Code Interpreter", "程式碼解譯器", "讓 agent 執行程式碼，常用於資料分析、圖表產生、檔案處理與數學計算。"],
    ["Computer Use", "電腦操作", "讓 agent 操作瀏覽器、GUI 或作業系統介面，例如點擊、輸入、讀取畫面。"],
    ["Sandbox", "沙盒", "隔離的執行環境，用來安全執行程式、操作檔案或測試流程。"],
  ]},
  { id: 6, en: "MCP", zh: "模型上下文協定", rows: [
    ["MCP / Model Context Protocol", "模型上下文協定", "一種開放協定，用來標準化 AI 應用如何連接外部工具、資料來源與工作流。"],
    ["MCP Host", "MCP 主機", "發起 MCP 連線的 AI 應用，例如聊天介面、IDE、桌面助理或 agent runtime。"],
    ["MCP Client", "MCP 客戶端", "Host 內部負責與 MCP server 溝通的連接元件。"],
    ["MCP Server", "MCP 伺服器", "提供工具、資料、提示或能力給 AI 應用使用的服務。"],
    ["MCP Tool", "MCP 工具", "MCP server 暴露給 AI 使用的可執行功能，例如查資料庫、呼叫 API、操作檔案。"],
    ["MCP Resource", "MCP 資源", "MCP server 提供的資料或上下文，例如檔案、文件、資料庫記錄、設定檔。"],
    ["MCP Prompt", "MCP 提示", "MCP server 提供的提示模板或工作流模板，可供 host 或 agent 使用。"],
    ["JSON-RPC", "JSON 遠端程序呼叫", "MCP 常用的訊息交換格式，用於 client 和 server 之間的請求、回應與通知。"],
    ["Capability Negotiation", "能力協商", "MCP client 與 server 連線時確認雙方支援哪些功能，例如 tools、resources、prompts。"],
    ["Sampling", "取樣", "MCP 中 server 可請求 host 使用模型生成內容的能力，適合更複雜的互動式流程。"],
    ["Roots", "根目錄／邊界", "MCP client 告訴 server 可存取的檔案或 URI 範圍，用來限制權限。"],
    ["Elicitation", "資訊引出／追問", "MCP server 向使用者請求額外資訊，例如缺少參數、確認或授權。"],
    ["Transport", "傳輸層", "MCP client 與 server 溝通的方式，例如 stdio、HTTP 等。"],
    ["Stdio Transport", "標準輸入輸出傳輸", "本機 MCP server 常見的傳輸方式，透過標準輸入與輸出溝通。"],
    ["Remote MCP Server", "遠端 MCP 伺服器", "部署在網路上的 MCP server，常用於 SaaS、企業系統或雲端資料源。"],
    ["MCP Registry", "MCP 登錄庫", "用來發現、發布或管理 MCP server 的目錄或生態系元件。"],
  ]},
  { id: 7, en: "Agent Skills", zh: "代理技能", rows: [
    ["Agent Skills", "代理技能", "可攜式能力包，通常包含指令、資源、腳本與範例，讓 agent 執行特定類型任務。"],
    ["Skill", "技能", "一個可重複使用的專門能力，例如 PDF 處理、Excel 報表、簡報製作、資料清理。"],
    ["SKILL.md", "技能說明檔", "Agent skill 的核心說明文件，通常定義技能名稱、用途、觸發條件與操作步驟。"],
    ["Skill Metadata", "技能中繼資料", "描述 skill 的名稱、用途、適用情境、限制與相關資源，幫助 agent 判斷是否使用。"],
    ["Skill Invocation", "技能調用", "Agent 根據使用者要求或任務需求，自動或明確啟用某個 skill。"],
    ["Progressive Disclosure", "漸進式揭露", "先只載入 skill 的簡短描述，等需要時再讀取完整內容，以節省 context。"],
  ]},
  { id: 8, en: "Memory", zh: "記憶", rows: [
    ["Context", "上下文", "Agent 當前可用的所有資訊，包括指令、對話、工具結果、文件、使用者狀態等。"],
    ["Local Context", "本地上下文", "程式端可用但不一定給模型看的資訊，例如 user id、資料庫連線、權限設定。"],
    ["LLM Context", "模型上下文", "實際放進模型輸入中的資訊，例如對話歷史、檢索內容、工具結果。"],
    ["Conversation History", "對話歷史", "先前多輪對話中的訊息，幫助 agent 理解任務延續性。"],
    ["Session", "會話", "用來保存某個使用者或任務的互動狀態。"],
    ["Short-Term Memory", "短期記憶", "當前任務或當前對話中暫時保留的資訊。"],
    ["Long-Term Memory", "長期記憶", "跨會話保存的使用者偏好、歷史決策、專案資訊或學習結果。"],
    ["Agent Memory", "代理記憶", "Agent 從過往任務中保留可重用經驗，用於改善未來表現。"],
    ["Memory Consolidation", "記憶整合", "將零散資訊整理成穩定、可重用的記憶。"],
    ["Compaction", "上下文壓縮", "當對話或資料太長時，把內容摘要化或壓縮，以保留重點並降低 token 成本。"],
  ]},
  { id: 9, en: "RAG", zh: "檢索增強生成", rows: [
    ["RAG / Retrieval-Augmented Generation", "檢索增強生成", "先從外部知識庫檢索資料，再讓模型基於資料回答，降低幻覺。"],
    ["Retriever", "檢索器", "根據查詢找出相關文件、段落、資料列或向量的元件。"],
    ["Embedding", "嵌入向量", "將文字、圖片或資料轉成向量，用於語意搜尋、相似度比較與聚類。"],
    ["Vector Database", "向量資料庫", "儲存 embedding 並支援相似度搜尋的資料庫。"],
    ["Knowledge Base", "知識庫", "Agent 可查詢的文件、FAQ、wiki、資料庫或企業知識集合。"],
  ]},
  { id: 10, en: "Hooks", zh: "鉤子", rows: [
    ["Hook", "鉤子／生命週期回呼", "在 agent 執行特定時間點插入自訂邏輯，例如 logging、監控、審計、修改流程。"],
    ["Lifecycle Event", "生命週期事件", "Agent 執行過程中的事件，例如開始、結束、工具呼叫、模型呼叫、handoff。"],
    ["Callback", "回呼函式", "某個事件發生時自動執行的函式。hook 通常是 callback 的一種。"],
    ["RunHooks", "執行層鉤子", "觀察或處理整個 run 的生命週期，可能跨多個 agent。"],
    ["AgentHooks", "代理層鉤子", "綁定在特定 agent 上，只處理該 agent 的生命週期事件。"],
    ["on_agent_start", "代理開始事件", "Agent 開始處理任務時觸發。"],
    ["on_agent_end", "代理結束事件", "Agent 完成任務或產生最終輸出時觸發。"],
    ["on_llm_start", "模型呼叫開始事件", "每次呼叫模型前觸發，可用於記錄 prompt、成本預估或權限檢查。"],
    ["on_llm_end", "模型呼叫結束事件", "模型回應後觸發，可用於記錄 token、latency、輸出內容。"],
    ["on_tool_start", "工具開始事件", "工具執行前觸發，可用於審計、權限檢查、參數驗證。"],
    ["on_tool_end", "工具結束事件", "工具執行後觸發，可用於記錄結果、清理狀態、錯誤處理。"],
    ["on_handoff", "交接事件", "一個 agent 將任務交給另一個 agent 時觸發。"],
    ["Middleware", "中介層", "插在請求、模型、工具或回應流程中的處理層，例如 logging、retry、error handling。"],
  ]},
  { id: 11, en: "Observability", zh: "可觀測性", rows: [
    ["Tracing", "追蹤", "記錄 agent 執行過程中的模型呼叫、工具呼叫、handoff、錯誤與耗時。"],
    ["Trace", "追蹤紀錄", "一次完整 workflow 的執行紀錄。"],
    ["Span", "區段", "Trace 中的一段具開始與結束時間的操作，例如一次工具呼叫或模型呼叫。"],
    ["Logging", "日誌", "記錄事件、錯誤、工具輸入輸出、系統狀態與審計資訊。"],
    ["Metrics", "指標", "衡量 latency、token 使用量、成本、成功率、錯誤率、工具呼叫次數等。"],
    ["Evaluation / Evals", "評估", "測試 agent 的正確性、安全性、穩定性、任務成功率與使用者體驗。"],
  ]},
  { id: 12, en: "Safety", zh: "安全", rows: [
    ["Guardrails", "護欄", "對輸入、輸出與工具呼叫做安全、格式、品質或權限檢查。"],
    ["Input Guardrail", "輸入護欄", "在 agent 處理前檢查使用者輸入是否安全、合規或超出範圍。"],
    ["Output Guardrail", "輸出護欄", "在 agent 回答前檢查輸出是否符合安全、格式與品質要求。"],
    ["Tripwire", "觸發線", "當 guardrail 判定高風險或不合格時觸發中止、阻擋或人工審核。"],
    ["Human-in-the-loop / HITL", "人在迴路", "在高風險決策或操作前加入真人確認，例如刪除資料、付款、發信、部署。"],
    ["Approval", "核准", "真人或系統對高風險行動給予允許。"],
    ["Permission Boundary", "權限邊界", "限制 agent 可讀取的資料、可使用的工具與可執行的操作。"],
    ["Least Privilege", "最小權限", "只給 agent 完成任務所需的最低權限。"],
    ["Prompt Injection", "提示注入", "惡意內容試圖操控 agent 忽略原本指令或洩漏敏感資訊。"],
    ["Tool Poisoning", "工具污染", "工具描述、工具結果或外部資料被惡意設計，導致 agent 做出錯誤或危險行動。"],
    ["Data Exfiltration", "資料外洩", "Agent 被誘導把敏感資訊傳到未授權位置。"],
    ["PII Redaction", "個資遮蔽", "移除或遮蔽姓名、電話、身分證號、地址等個人資料。"],
  ]},
  { id: 13, en: "Reliability", zh: "可靠性", rows: [
    ["Retry", "重試", "工具或模型呼叫失敗時再次嘗試。"],
    ["Timeout", "逾時", "限制模型、工具或 API 的最大等待時間，避免流程卡住。"],
    ["Rate Limit", "速率限制", "限制請求頻率，避免超額、過載或成本失控。"],
    ["Fallback", "備援", "主模型、工具或資料源失敗時切換到替代方案。"],
    ["Idempotency", "冪等性", "同一操作重複執行不會造成額外副作用，對付款、刪除、寄信等特別重要。"],
    ["State", "狀態", "Agent 執行中保存的進度、變數、工具結果、對話歷史與決策資訊。"],
    ["Checkpoint", "檢查點", "保存中間狀態，方便失敗後恢復、審計或人工接手。"],
  ]},
];

// ===== 共用版面常數 (16:9 inches: 13.333 x 7.5) =====
const SLIDE_W = 13.333;
const SLIDE_H = 7.5;

// ===== 標題頁 =====
function buildTitleSlide(pptx) {
  const slide = pptx.addSlide();
  slide.background = { color: C_CREAM };

  // 左側橘色色塊
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 0.45, h: SLIDE_H,
    fill: { color: C_PRIMARY }, line: { type: "none" }
  });

  // 上方品牌標記
  slide.addText("CLAUDE  ·  AGENT  TERMINOLOGY", {
    x: 1.0, y: 0.7, w: 11.0, h: 0.4,
    fontFace: FONT_BODY, fontSize: 12, bold: true,
    color: C_PRIMARY, charSpacing: 6
  });

  // 主標題
  slide.addText("Agent 相關名詞", {
    x: 1.0, y: 1.6, w: 11.0, h: 1.2,
    fontFace: FONT_TITLE, fontSize: 60, bold: true, color: C_INK
  });

  slide.addText("中英對照表", {
    x: 1.0, y: 2.8, w: 11.0, h: 1.0,
    fontFace: FONT_TITLE, fontSize: 48, italic: true, color: C_PRIMARY
  });

  // 分隔線
  slide.addShape(pptx.ShapeType.line, {
    x: 1.0, y: 4.3, w: 3.5, h: 0,
    line: { color: C_INK, width: 2 }
  });

  // 副標
  slide.addText(
    "從 LLM、Prompt、Agent 到 MCP、Hooks、Safety —— 13 個分類、150+ 個關鍵詞彙",
    {
      x: 1.0, y: 4.5, w: 11.0, h: 0.6,
      fontFace: FONT_BODY, fontSize: 16, color: C_INK
    }
  );

  // 底部資訊列
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.45, y: SLIDE_H - 0.7, w: SLIDE_W - 0.45, h: 0.7,
    fill: { color: C_HEADER_BG }, line: { type: "none" }
  });
  slide.addText("2026 年上半年 · 東吳大學資訊科學系", {
    x: 1.0, y: SLIDE_H - 0.65, w: 7.0, h: 0.6,
    fontFace: FONT_BODY, fontSize: 12, color: C_CREAM
  });
  slide.addText("13 SECTIONS  ·  150+ TERMS", {
    x: SLIDE_W - 5.0, y: SLIDE_H - 0.65, w: 4.5, h: 0.6,
    fontFace: FONT_BODY, fontSize: 12, color: C_PRIMARY,
    bold: true, align: "right", charSpacing: 4
  });
}

// ===== 目錄頁 =====
function buildAgendaSlide(pptx) {
  const slide = pptx.addSlide();
  slide.background = { color: C_CREAM };

  // 左側橘色色塊
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 0.45, h: SLIDE_H,
    fill: { color: C_PRIMARY }, line: { type: "none" }
  });

  // 上方標籤
  slide.addText("AGENDA", {
    x: 1.0, y: 0.5, w: 11.0, h: 0.4,
    fontFace: FONT_BODY, fontSize: 12, bold: true,
    color: C_PRIMARY, charSpacing: 6
  });

  // 標題
  slide.addText("13 個主題分類", {
    x: 1.0, y: 0.95, w: 11.0, h: 0.9,
    fontFace: FONT_TITLE, fontSize: 36, bold: true, color: C_INK
  });

  // 兩欄式條目
  const half = Math.ceil(sections.length / 2);
  const left = sections.slice(0, half);
  const right = sections.slice(half);

  function renderColumn(items, x) {
    items.forEach((s, idx) => {
      const y = 2.1 + idx * 0.7;
      // 編號
      slide.addText(String(s.id).padStart(2, "0"), {
        x: x, y: y, w: 0.7, h: 0.55,
        fontFace: FONT_TITLE, fontSize: 22, bold: true,
        color: C_PRIMARY, valign: "middle"
      });
      // 英文名
      slide.addText(s.en, {
        x: x + 0.7, y: y, w: 3.2, h: 0.3,
        fontFace: FONT_BODY, fontSize: 14, bold: true,
        color: C_INK, valign: "middle"
      });
      // 中文名
      slide.addText(s.zh, {
        x: x + 0.7, y: y + 0.28, w: 3.2, h: 0.3,
        fontFace: FONT_BODY, fontSize: 11,
        color: C_WARM_GRAY, valign: "middle"
      });
    });
  }
  renderColumn(left, 1.2);
  renderColumn(right, 7.4);

  // 底部資訊列
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.45, y: SLIDE_H - 0.4, w: SLIDE_W - 0.45, h: 0.4,
    fill: { color: C_HEADER_BG }, line: { type: "none" }
  });
  slide.addText("AGENT TERMINOLOGY  ·  AGENDA", {
    x: 1.0, y: SLIDE_H - 0.38, w: 7.0, h: 0.36,
    fontFace: FONT_BODY, fontSize: 10, color: C_CREAM, charSpacing: 3
  });
}

// ===== 章節頁 =====
function buildSectionSlide(pptx, section) {
  const slide = pptx.addSlide();
  slide.background = { color: C_CREAM };

  // 左側橘色色塊
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 0.45, h: SLIDE_H,
    fill: { color: C_PRIMARY }, line: { type: "none" }
  });

  // 章節編號 (大字)
  slide.addText(String(section.id).padStart(2, "0"), {
    x: 0.85, y: 0.35, w: 1.4, h: 1.1,
    fontFace: FONT_TITLE, fontSize: 60, bold: true,
    color: C_PRIMARY, valign: "middle"
  });

  // 章節標籤
  slide.addText("SECTION", {
    x: 2.3, y: 0.45, w: 3.0, h: 0.3,
    fontFace: FONT_BODY, fontSize: 10, bold: true,
    color: C_WARM_GRAY, charSpacing: 4
  });

  // 中文標題
  slide.addText(section.zh, {
    x: 2.3, y: 0.7, w: 9.5, h: 0.55,
    fontFace: FONT_TITLE, fontSize: 28, bold: true, color: C_INK
  });

  // 英文標題
  slide.addText(section.en, {
    x: 2.3, y: 1.18, w: 9.5, h: 0.35,
    fontFace: FONT_BODY, fontSize: 14, italic: true, color: C_PRIMARY
  });

  // 分隔線
  slide.addShape(pptx.ShapeType.line, {
    x: 0.7, y: 1.7, w: SLIDE_W - 1.4, h: 0,
    line: { color: C_PRIMARY, width: 1.5 }
  });

  // 表格資料
  const headerOpts = {
    fill: { color: C_HEADER_BG },
    color: C_CREAM,
    bold: true,
    fontFace: FONT_BODY,
    align: "left",
    valign: "middle"
  };

  const tableData = [];
  // 表頭
  tableData.push([
    { text: "English",  options: { ...headerOpts } },
    { text: "中文",      options: { ...headerOpts } },
    { text: "說明",      options: { ...headerOpts } },
  ]);

  // 內容列 (隔行底色)
  section.rows.forEach((r, idx) => {
    const rowFill = idx % 2 === 0 ? { color: C_WHITE } : { color: C_ZEBRA };
    tableData.push([
      { text: r[0], options: { fill: rowFill, color: C_INK, bold: true, fontFace: FONT_BODY, valign: "middle" } },
      { text: r[1], options: { fill: rowFill, color: C_PRIMARY, bold: true, fontFace: FONT_BODY, valign: "middle" } },
      { text: r[2], options: { fill: rowFill, color: C_INK, fontFace: FONT_BODY, valign: "middle" } },
    ]);
  });

  // 動態字級 (超過 14 列時縮小)
  const totalRows = tableData.length;
  let fontSize;
  if (totalRows <= 8)        fontSize = 13;
  else if (totalRows <= 11)  fontSize = 11;
  else if (totalRows <= 14)  fontSize = 10;
  else if (totalRows <= 17)  fontSize = 9;
  else                       fontSize = 8;

  slide.addTable(tableData, {
    x: 0.7,
    y: 1.9,
    w: SLIDE_W - 1.4,
    colW: [3.0, 2.2, SLIDE_W - 1.4 - 3.0 - 2.2],
    fontSize: fontSize,
    fontFace: FONT_BODY,
    border: { type: "solid", pt: 0.5, color: C_WARM_GRAY },
    margin: 0.06,
    valign: "middle"
  });

  // 底部資訊列
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.45, y: SLIDE_H - 0.4, w: SLIDE_W - 0.45, h: 0.4,
    fill: { color: C_HEADER_BG }, line: { type: "none" }
  });
  slide.addText(`AGENT TERMINOLOGY  ·  ${section.en.toUpperCase()}`, {
    x: 1.0, y: SLIDE_H - 0.38, w: 8.0, h: 0.36,
    fontFace: FONT_BODY, fontSize: 10, color: C_CREAM, charSpacing: 3
  });
  slide.addText(`${String(section.id).padStart(2, "0")} / 13`, {
    x: SLIDE_W - 2.0, y: SLIDE_H - 0.38, w: 1.5, h: 0.36,
    fontFace: FONT_BODY, fontSize: 10, color: C_PRIMARY,
    bold: true, align: "right", charSpacing: 2
  });
}

// ===== 結尾頁 =====
function buildEndSlide(pptx) {
  const slide = pptx.addSlide();
  slide.background = { color: C_HEADER_BG };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 0.45, h: SLIDE_H,
    fill: { color: C_PRIMARY }, line: { type: "none" }
  });

  slide.addText("Thank you", {
    x: 1.0, y: 2.7, w: 11.0, h: 1.2,
    fontFace: FONT_TITLE, fontSize: 80, bold: true, color: C_CREAM
  });
  slide.addText("讓我們從詞彙開始，建立 Agent 的共同語言。", {
    x: 1.0, y: 3.95, w: 11.0, h: 0.6,
    fontFace: FONT_BODY, fontSize: 18, color: C_PRIMARY
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 1.0, y: 4.7, w: 3.0, h: 0,
    line: { color: C_PRIMARY, width: 2 }
  });
  slide.addText("2026 · 東吳大學資訊科學系", {
    x: 1.0, y: 4.85, w: 11.0, h: 0.4,
    fontFace: FONT_BODY, fontSize: 12, color: C_WARM_GRAY, charSpacing: 3
  });
}

// ===== 主流程 =====
async function build() {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.title = "Agent 相關名詞中英對照表";
  pptx.author = "Josh Hu";

  buildTitleSlide(pptx);
  buildAgendaSlide(pptx);
  for (const s of sections) buildSectionSlide(pptx, s);
  buildEndSlide(pptx);

  await pptx.writeFile({ fileName: "Agent_名詞對照表.pptx" });
  console.log("OK");
}

build().catch(e => { console.error(e); process.exit(1); });
