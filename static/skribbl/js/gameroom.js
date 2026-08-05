/**
 * Skribbl.io layout clone — UI shell only.
 * Game logic is driven by WebSocket messages from the server.
 *
 * UI message examples (send via socket):
 *   { "type": "ui", "action": "toolbar", "visible": true }
 *   { "type": "ui", "action": "overlay", "show": true, "mode": "text", "text": "Waiting..." }
 *   { "type": "ui", "action": "word", "description": "DRAW THIS", "word": "_ _ _ _", "hints": ["_", "_", "a", "_"] }
 *   { "type": "ui", "action": "clock", "time": 80 }
 *   { "type": "ui", "action": "round", "text": "Round 1 of 3" }
 *   { "type": "ui", "action": "players", "players": [{ "name": "Alice", "score": 100, "guessed": false, "drawing": true, "me": true }] }
 *   { "type": "ui", "action": "chat_add", "name": "Bob", "text": "apple", "chatType": "close" }
 *   { "type": "ui", "action": "chat_clear" }
 *   { "type": "ui", "action": "guess_input", "enabled": true, "placeholder": "Type your guess here..." }
 *   { "type": "ui", "action": "rate", "visible": true }
 *   { "type": "ui", "action": "loading", "show": false }
 */

(function () {
  "use strict";

  const STATIC_IMG = window.SKRIBBL_STATIC || "/static/skribbl/img/";

  const COLORS = [
    [255, 255, 255],
    [0, 0, 0],
    [193, 193, 193],
    [80, 80, 80],
    [239, 19, 11],
    [116, 11, 7],
    [255, 113, 0],
    [194, 56, 0],
    [255, 228, 0],
    [232, 162, 0],
    [0, 204, 0],
    [0, 70, 25],
    [0, 255, 145],
    [0, 120, 93],
    [0, 178, 255],
    [0, 86, 158],
    [35, 31, 211],
    [14, 8, 101],
    [163, 0, 186],
    [85, 0, 105],
    [223, 105, 167],
    [135, 53, 84],
    [255, 172, 142],
    [204, 119, 77],
    [160, 82, 45],
    [99, 48, 13],
  ];

  const BRUSH_SIZES = [4, 10, 20, 32, 40];
  const MIN_SIZE = 4;
  const MAX_SIZE = 40;

  const CHAT_TYPES = {
    base: "var(--COLOR_CHAT_TEXT_BASE)",
    guessed: "var(--COLOR_CHAT_TEXT_GUESSED)",
    close: "var(--COLOR_CHAT_TEXT_CLOSE)",
    drawing: "var(--COLOR_CHAT_TEXT_DRAWING)",
    join: "var(--COLOR_CHAT_TEXT_JOIN)",
    leave: "var(--COLOR_CHAT_TEXT_LEAVE)",
    owner: "var(--COLOR_CHAT_TEXT_OWNER)",
    guesschat: "var(--COLOR_CHAT_TEXT_GUESSCHAT)",
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const game = $("#game");
  const wrapper = $("#game-wrapper");
  const canvas = $("#game-canvas canvas");
  const ctx = canvas.getContext("2d");
  const overlay = $("#game-canvas .overlay");
  const overlayText = $("#game-canvas .overlay-content .text");
  const overlayWords = $("#game-canvas .overlay-content .words");
  const overlayReveal = $("#game-canvas .overlay-content .reveal");
  const overlayResult = $("#game-canvas .overlay-content .result");
  const overlayRoom = $("#game-canvas .room");
  const overlayScoreboard = $("#game-canvas .overlay-content .scoreboard");
  const playersList = $("#game-players .players-list");
  const chatContent = $("#game-chat .chat-content");
  const chatForms = $$("form.chat-form");
  const clockEl = $("#game-clock .text");
  const roundEl = $("#game-round .text");
  const wordDescEl = $("#game-word .description");
  const wordEl = $("#game-word .word");
  const hintsContainer = $("#game-word .hints .container");
  const colorsEl = $("#game-toolbar .colors");
  const sizesContainer = $("#game-toolbar .sizes .container");
  const sizePreview = $("#game-toolbar .sizes .size-preview");
  const toolsGroup = $("#game-toolbar .toolbar-group-tools");
  const actionsGroup = $("#game-toolbar .toolbar-group-actions");
  const rateEl = $("#game-rate");
  const loadEl = $("#load");

  let primaryColorIndex = 1;
  let secondaryColorIndex = 0;
  let brushSizeIndex = 0;
  let selectedTool = null;
  let drawing = false;
  let lastX = 0;
  let lastY = 0;
  let socket = null;

  function rgb(color) {
    return "rgb(" + color[0] + "," + color[1] + "," + color[2] + ")";
  }

  function imgUrl(name) {
    return STATIC_IMG + name;
  }

  function clampSize(size) {
    return Math.max(MIN_SIZE, Math.min(MAX_SIZE, size));
  }

  function sizeIconPercent(size) {
    return 20 + ((size - MIN_SIZE) / (MAX_SIZE - MIN_SIZE)) * 80;
  }

  function createEl(tag, className, text) {
    const el = document.createElement(tag);
    if (className) className.split(" ").forEach((c) => el.classList.add(c));
    if (text != null) el.textContent = text;
    return el;
  }

  function setFillPreview(index, isPrimary) {
    const color = rgb(COLORS[index]);
    const id = isPrimary
      ? "#color-preview-primary"
      : "#color-preview-secondary";
    $(id).style.fill = color;
    if (isPrimary) {
      $(".color-preview-mobile").style.backgroundColor = color;
    }
  }

  function updateActiveColor() {
    const active = primaryColorIndex;
    $$("#game-toolbar .colors .color").forEach((el) => {
      el.classList.toggle("selected", Number(el.dataset.index) === active);
    });
    setFillPreview(primaryColorIndex, true);
    setFillPreview(secondaryColorIndex, false);
  }

  function initColors() {
    const top = createEl("div", "top");
    const bottom = createEl("div", "bottom");
    for (let i = 0; i < COLORS.length / 2; i++) {
      top.appendChild(makeColorSwatch(i * 2));
      bottom.appendChild(makeColorSwatch(i * 2 + 1));
    }
    colorsEl.appendChild(top);
    colorsEl.appendChild(bottom);
    updateActiveColor();
  }

  function makeColorSwatch(index) {
    const el = createEl("div", "color");
    el.style.backgroundColor = rgb(COLORS[index]);
    el.dataset.index = String(index);
    el.addEventListener("click", (e) => {
      if (e.button === 2) return;
      primaryColorIndex = index;
      updateActiveColor();
    });
    el.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      secondaryColorIndex = index;
      updateActiveColor();
    });
    return el;
  }

  function initSizes() {
    BRUSH_SIZES.forEach((size, id) => {
      const el = createEl("div", "size clickable");
      const icon = createEl("div", "icon");
      icon.style.backgroundImage = "url(" + imgUrl("size.gif") + ")";
      icon.style.backgroundSize = sizeIconPercent(size) + "%";
      el.appendChild(icon);
      el.dataset.index = String(id);
      el.addEventListener("click", () => selectSize(id));
      sizesContainer.appendChild(el);
    });
    selectSize(0);
    sizePreview.addEventListener("click", () => {
      sizesContainer.classList.toggle("open");
    });
    document.addEventListener("click", (e) => {
      if (!e.target.closest("#game-toolbar .sizes")) {
        sizesContainer.classList.remove("open");
      }
    });
  }

  function selectSize(id) {
    brushSizeIndex = id;
    const size = BRUSH_SIZES[id];
    const icon = sizePreview.querySelector(".icon");
    icon.style.backgroundImage = "url(" + imgUrl("size.gif") + ")";
    icon.style.backgroundSize = sizeIconPercent(size) + "%";
    $$("#game-toolbar .sizes .size").forEach((el) => {
      el.classList.toggle("selected", Number(el.dataset.index) === id);
    });
    sizesContainer.classList.remove("open");
  }

  function makeTool(id, opts) {
    const el = createEl("div", "tool clickable");
    const icon = createEl("div", "icon");
    icon.style.backgroundImage = "url(" + imgUrl(opts.graphic) + ")";
    const key = createEl("div", "key", opts.keydef);
    el.appendChild(icon);
    el.appendChild(key);
    el.dataset.toolId = String(id);
    el.title = opts.name;
    el.addEventListener("click", () => {
      $$("#game-toolbar .tool").forEach((t) => t.classList.remove("selected"));
      if (!opts.isAction) {
        el.classList.add("selected");
        selectedTool = id;
      }
      if (opts.action) opts.action();
      el.classList.add("clicked");
      setTimeout(() => el.classList.remove("clicked"), 100);
    });
    return el;
  }

  function initTools() {
    const brush = makeTool(0, {
      isAction: false,
      name: "Brush",
      keydef: "B",
      graphic: "pen.gif",
    });
    const fill = makeTool(1, {
      isAction: false,
      name: "Fill",
      keydef: "F",
      graphic: "fill.gif",
    });
    const undo = makeTool(2, {
      isAction: true,
      name: "Undo",
      keydef: "U",
      graphic: "undo.gif",
      action: function () {},
    });
    const clear = makeTool(3, {
      isAction: true,
      name: "Clear",
      keydef: "C",
      graphic: "clear.gif",
      action: function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      },
    });
    toolsGroup.appendChild(brush);
    toolsGroup.appendChild(fill);
    actionsGroup.appendChild(undo);
    actionsGroup.appendChild(clear);
    brush.classList.add("selected");
    selectedTool = 0;
  }

  function resizeCanvas() {
    const container = $("#game-canvas");
    const w = container.clientWidth;
    const h = Math.round((w * 600) / 800);
    canvas.width = w;
    canvas.height = h;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
  }

  function currentDrawColor() {
    return rgb(COLORS[primaryColorIndex]);
  }

  function currentBrushSize() {
    return BRUSH_SIZES[brushSizeIndex];
  }

  function drawLine(data) {
    ctx.beginPath();
    ctx.moveTo(data.x0, data.y0);
    ctx.lineTo(data.x1, data.y1);
    ctx.strokeStyle = data.color || "#000";
    ctx.lineWidth = data.size || 4;
    ctx.lineCap = "round";
    ctx.stroke();
  }

  function bindDrawing() {
    function pos(e) {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY,
      };
    }

    canvas.addEventListener("mousedown", (e) => {
      drawing = true;
      const p = pos(e);
      lastX = p.x;
      lastY = p.y;
    });

    canvas.addEventListener("mouseup", () => (drawing = false));
    canvas.addEventListener("mouseleave", () => (drawing = false));

    canvas.addEventListener("mousemove", (e) => {
      if (!drawing) return;
      const p = pos(e);
      const data = {
        type: "draw",
        x0: lastX,
        y0: lastY,
        x1: p.x,
        y1: p.y,
        color: currentDrawColor(),
        size: currentBrushSize(),
      };
      drawLine(data);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data));
      }
      lastX = p.x;
      lastY = p.y;
    });
  }

  function bindChatInput() {
    chatForms.forEach((form) => {
      const input = form.querySelector("input");
      const counter = form.querySelector(".characters");
      input.addEventListener("input", () => {
        const left = input.maxLength - input.value.length;
        counter.textContent = left;
        counter.classList.toggle("visible", input.value.length > 0);
      });
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "guess", text: text }));
        }
        input.value = "";
        counter.classList.remove("visible");
      });
    });
  }

  const GameUI = {
    toolbar(data) {
      wrapper.classList.toggle("toolbar-hidden", !data.visible);
      GameUI.rate({ visible: data.visible });
    },

    overlay(data) {
      overlay.classList.toggle("show", !!data.show);
      overlayText.classList.remove("show");
      overlayWords.classList.remove("show");
      overlayReveal.classList.remove("show");
      overlayResult.classList.remove("show");
      overlayRoom.classList.remove("show");
      overlayScoreboard.classList.remove("show");

      if (!data.show) return;

      const mode = data.mode || "text";
      if (mode === "text") {
        overlayText.classList.add("show");
        overlayText.textContent = data.text || "";
      } else if (mode === "words") {
        overlayWords.classList.add("show");
        overlayWords.innerHTML = "";
        (data.words || []).forEach((word) => {
          const btn = createEl("div", "word", word);
          overlayWords.appendChild(btn);
        });
      } else if (mode === "reveal") {
        overlayReveal.classList.add("show");
        overlayReveal.querySelector(".word").textContent = data.word || "";
        const reason = overlayReveal.querySelector(".reason");
        reason.textContent = data.reason || "";
        reason.style.display = data.reason ? "block" : "none";
      } else if (mode === "result") {
        overlayResult.classList.add("show");
        if (data.winnerName != null) {
          overlayResult.querySelector(".winner-name").textContent =
            data.winnerName;
        }
        if (data.winnerText != null) {
          overlayResult.querySelector(".winner-text").textContent =
            data.winnerText;
        }
      } else if (mode === "scoreboard") {
        overlayScoreboard.classList.add("show");

        const list = overlayScoreboard.querySelector(".players");

        list.innerHTML = "";

        (data.players || []).forEach((player, index) => {
          const row = document.createElement("div");
          row.className = "score-row";

          row.innerHTML = `
            <div class="rank">${index + 1}</div>
            <div class="name">${player.name}</div>
            <div class="score">${player.score}</div>
        `;

          list.appendChild(row);
        });

        const btn = overlayScoreboard.querySelector(".continue");

        btn.style.display = data.showButton ? "" : "none";
      } else if (mode === "room") {
        overlayRoom.classList.add("show");
      }
    },

    word(data) {
      if (data.description != null) wordDescEl.textContent = data.description;
      if (data.word != null) wordEl.textContent = data.word;
      hintsContainer.innerHTML = "";
      if (data.hints && data.hints.length) {
        data.hints.forEach((hint) => {
          const span = createEl(
            "span",
            hint === "_" ? "hint" : "hint uncover",
            hint,
          );
          hintsContainer.appendChild(span);
        });
      }
      if (data.wordLength != null) {
        const len = createEl("span", "word-length", data.wordLength);
        hintsContainer.appendChild(len);
      }
    },

    clock(data) {
      clockEl.textContent = data.time != null ? String(data.time) : "";
      if (data.animate) {
        $("#game-clock").style.animationName = "none";
        void $("#game-clock").offsetWidth;
        $("#game-clock").style.animationName = "";
      }
    },

    round(data) {
      roundEl.textContent = data.text || "";
    },

    players(data) {
      playersList.innerHTML = "";
      const list = data.players || [];
      list.forEach((player, i) => {
        const el = createEl("div", "player");
        if (i % 2 === 0) el.classList.add("odd");
        if (i === 0) el.classList.add("first");
        if (i === list.length - 1) el.classList.add("last");
        if (player.guessed) el.classList.add("guessed");
        if (player.drawing) el.classList.add("drawing");
        if (player.admin) el.classList.add("admin");

        const bg = createEl("div", "player-background");
        const info = createEl("div", "player-info");
        const name = createEl("div", "player-name", player.name || "Player");
        if (player.me) name.classList.add("me");
        const score = createEl(
          "div",
          "player-score",
          String(player.score != null ? player.score : 0),
        );
        info.appendChild(name);
        info.appendChild(score);

        const avatarWrap = createEl("div", "player-avatar-container");
        const avatar = createEl("div", "avatar");
        const color = createEl("div", "color");
        color.style.backgroundColor = player.color || "#4571ff";
        color.style.borderRadius = "4px";
        avatar.appendChild(color);
        if (player.drawing) {
          const pen = createEl("div", "drawing");
          pen.style.backgroundImage = "url(" + imgUrl("pen.gif") + ")";
          avatar.appendChild(pen);
        }
        avatarWrap.appendChild(avatar);

        el.appendChild(bg);
        el.appendChild(info);
        el.appendChild(avatarWrap);
        playersList.appendChild(el);
      });
    },

    chat_add(data) {
      const p = document.createElement("p");
      const name = document.createElement("b");
      name.textContent = (data.name || "Player") + ": ";
      p.appendChild(name);
      const span = document.createElement("span");
      span.textContent = data.text || "";
      p.appendChild(span);

      const chatType = (data.chatType || "base").toLowerCase();
      if (chatType === "guessed") p.classList.add("guessed");
      p.style.color = CHAT_TYPES[chatType] || CHAT_TYPES.base;

      chatContent.appendChild(p);
      chatContent.scrollTop = chatContent.scrollHeight;

      if (data.bubble !== false) {
        const bubbleHost = $("#game-canvas .bubbles");
        const bubble = p.cloneNode(true);
        bubbleHost.appendChild(bubble);
        setTimeout(() => bubble.remove(), 2500);
      }
    },

    chat_clear() {
      chatContent.innerHTML = "";
    },

    guess_input(data) {
      chatForms.forEach((form) => {
        const input = form.querySelector("input");
        if (data.enabled != null) input.disabled = !data.enabled;
        if (data.placeholder != null) input.placeholder = data.placeholder;
        form.style.display = data.visible === false ? "none" : "";
      });
    },

    rate(data) {
      rateEl.style.display = data.visible ? "block" : "none";
    },

    loading(data) {
      loadEl.style.display = data.show ? "block" : "none";
    },

    handle(data) {
      const action = data.action;
      if (action && typeof GameUI[action] === "function") {
        GameUI[action](data);
      }
    },
  };

  window.GameUI = GameUI;

  function connectSocket(roomName) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(
      protocol + "//" + window.location.host + "/ws/board/" + roomName + "/",
    );

    socket.onmessage = function (e) {
      const data = JSON.parse(e.data);
      if (data.type === "draw") {
        drawLine(data.payload);
      } else if (data.type === "ui") {
        GameUI.handle(data);
      } else if (typeof GameUI[data.type] === "function") {
        GameUI[data.type](data);
      }
    };

    socket.onclose = function () {
      console.error("websocket closed unexpectedly");
    };
  }

  function init() {
    initColors();
    initSizes();
    initTools();
    resizeCanvas();
    bindDrawing();
    bindChatInput();
    window.addEventListener("resize", resizeCanvas);

    const roomScript = document.getElementById("room_name");
    if (roomScript) {
      const roomName = JSON.parse(roomScript.textContent);
      connectSocket(roomName);
    }

    GameUI.toolbar({ visible: true });
    GameUI.rate({ visible: false });
    GameUI.guess_input({ enabled: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
