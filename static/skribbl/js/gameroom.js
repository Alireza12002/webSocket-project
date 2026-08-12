/**
 * Skribbl.io layout clone — UI shell only.
 * Game logic is driven by WebSocket messages from the server.
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

  // Fixed backing-store size. Stroke coordinates are expressed in this
  // space, so every client agrees on where a stroke belongs.
  const CANVAS_W = 800;
  const CANVAS_H = 600;

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
  // let secondaryColorIndex = 0;
  let brushSizeIndex = 0;
  let selectedTool = null;

  // IMPORTANT:
  // This controls whether the current player is allowed to draw.
  let canDraw = false;

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

    if (className) {
      className.split(" ").forEach((c) => el.classList.add(c));
    }

    if (text != null) {
      el.textContent = text;
    }

    return el;
  }

  // function setFillPreview(index, isPrimary) {
  //   const color = rgb(COLORS[index]);

  //   const id = isPrimary
  //     ? "#color-preview-primary"
  //     : "#color-preview-secondary";

  //   const preview = $(id);

  //   if (preview) {
  //     preview.style.fill = color;
  //   }

  //   if (isPrimary) {
  //     const mobilePreview = $(".color-preview-mobile");

  //     if (mobilePreview) {
  //       mobilePreview.style.backgroundColor = color;
  //     }
  //   }
  // }

  function updateActiveColor() {
    const active = primaryColorIndex;

    $$("#game-toolbar .colors .color").forEach((el) => {
      el.classList.toggle("selected", Number(el.dataset.index) === active);
    });

    // setFillPreview(primaryColorIndex, true);
    // setFillPreview(secondaryColorIndex, false);
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

  // function makeColorSwatch(index) {
  //   const el = createEl("div", "color");

  //   el.style.backgroundColor = rgb(COLORS[index]);
  //   el.dataset.index = String(index);

  //   el.addEventListener("click", (e) => {
  //     if (e.button === 2) return;

  //     primaryColorIndex = index;
  //     updateActiveColor();
  //   });

  //   el.addEventListener("contextmenu", (e) => {
  //     e.preventDefault();

  //     secondaryColorIndex = index;
  //     updateActiveColor();
  //   });

  //   return el;
  // }
  function makeColorSwatch(index) {
    const el = createEl("div", "color");

    el.style.backgroundColor = rgb(COLORS[index]);
    el.dataset.index = String(index);

    el.addEventListener("click", () => {
      primaryColorIndex = index;
      updateActiveColor();
    });

    return el;
  }
  function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    applyContextDefaults();
  }
  function initSizes() {
    BRUSH_SIZES.forEach((size, id) => {
      const el = createEl("div", "size clickable");
      const icon = createEl("div", "icon");

      icon.style.backgroundImage = "url(" + imgUrl("size.gif") + ")";

      icon.style.backgroundSize = sizeIconPercent(size) + "%";

      el.appendChild(icon);
      el.dataset.index = String(id);

      el.addEventListener("click", () => {
        selectSize(id);
      });

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
    const key = createEl("div", "key", opts.keydef);

    icon.style.backgroundImage = "url(" + imgUrl(opts.graphic) + ")";

    el.appendChild(icon);
    el.appendChild(key);

    el.dataset.toolId = String(id);
    el.title = opts.name;

    el.addEventListener("click", () => {
      $$("#game-toolbar .tool").forEach((t) => {
        t.classList.remove("selected");
      });

      if (!opts.isAction) {
        el.classList.add("selected");
        selectedTool = id;
      }

      if (opts.action) {
        opts.action();
      }

      el.classList.add("clicked");

      setTimeout(() => {
        el.classList.remove("clicked");
      }, 100);
    });

    return el;
  }

  // function initTools() {
  //   const brush = makeTool(0, {
  //     isAction: false,
  //     name: "Brush",
  //     keydef: "B",
  //     graphic: "pen.gif",
  //   });

  //   const fill = makeTool(1, {
  //     isAction: false,
  //     name: "Fill",
  //     keydef: "F",
  //     graphic: "fill.gif",
  //   });

  //   const undo = makeTool(2, {
  //     isAction: true,
  //     name: "Undo",
  //     keydef: "U",
  //     graphic: "undo.gif",
  //     action: function () {},
  //   });

  //   const clear = makeTool(3, {
  //     isAction: true,
  //     name: "Clear",
  //     keydef: "C",
  //     graphic: "clear.gif",

  //     action: function () {
  //       // Only drawer should be able to clear.
  //       if (!canDraw) return;

  //       ctx.clearRect(
  //         0,
  //         0,
  //         canvas.width,
  //         canvas.height
  //       );
  //     },
  //   });

  //   toolsGroup.appendChild(brush);
  //   toolsGroup.appendChild(fill);
  //   actionsGroup.appendChild(undo);
  //   actionsGroup.appendChild(clear);

  //   brush.classList.add("selected");
  //   selectedTool = 0;
  // }
  function initTools() {
    const brush = makeTool(0, {
      isAction: false,
      name: "Brush",
      keydef: "B",
      graphic: "pen.gif",
    });

    const clear = makeTool(1, {
      isAction: true,
      name: "Clear",
      keydef: "C",
      graphic: "clear.gif",

      action: function () {
        // Only the drawer can request a clear.
        if (!canDraw) {
          return;
        }

        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(
            JSON.stringify({
              type: "clear",
            }),
          );
        }
      },
    });

    toolsGroup.appendChild(brush);
    actionsGroup.appendChild(clear);

    brush.classList.add("selected");
    selectedTool = 0;
  }
  /*
   * The canvas bitmap is a FIXED 800x600 and is never reassigned after
   * init. CSS alone scales it to fit the container.
   *
   * Assigning canvas.width/height (even the same value) wipes the bitmap
   * and resets all context state, which previously erased every stroke on
   * any window resize. It also made each client's coordinate space depend
   * on its own container width, so strokes landed in the wrong place --
   * and once a resize reset lineCap/lineJoin, incoming strokes rendered
   * inconsistently. Keeping the backing store fixed solves both.
   */
  function initCanvas() {
    canvas.width = CANVAS_W;
    canvas.height = CANVAS_H;

    applyContextDefaults();
  }

  function applyContextDefaults() {
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
    ctx.lineJoin = "round";

    ctx.stroke();
  }

  /*
   * Enable / disable drawing permission.
   *
   * IMPORTANT:
   * This is only frontend behavior.
   * Backend must also verify that the sender is the drawer.
   */
  function setDrawingEnabled(enabled) {
    canDraw = Boolean(enabled);

    // If drawing becomes disabled while mouse is down,
    // immediately stop the current drawing operation.
    if (!canDraw) {
      drawing = false;
    }

    // Optional visual feedback.
    canvas.style.cursor = canDraw ? "crosshair" : "default";
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

    /*
     * START DRAWING
     *
     * Only the drawer is allowed to start.
     */
    canvas.addEventListener("mousedown", (e) => {
      if (!canDraw) {
        return;
      }

      // Only left mouse button.
      if (e.button !== 0) {
        return;
      }

      drawing = true;

      const p = pos(e);

      lastX = p.x;
      lastY = p.y;
    });

    /*
     * STOP DRAWING
     */
    canvas.addEventListener("mouseup", () => {
      drawing = false;
    });

    canvas.addEventListener("mouseleave", () => {
      drawing = false;
    });

    /*
     * DRAW
     *
     * Only drawer can enter this section.
     */
    canvas.addEventListener("mousemove", (e) => {
      if (!canDraw) {
        return;
      }

      if (!drawing) {
        return;
      }

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

      /*
       * Draw immediately on drawer's own screen.
       *
       * This makes drawing feel instant instead of
       * waiting for the server to send it back.
       */
      drawLine(data);

      /*
       * Send drawing operation to backend.
       */
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

        if (!text) {
          return;
        }

        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(
            JSON.stringify({
              type: "guess",
              text: text,
            }),
          );
        }

        input.value = "";
        counter.classList.remove("visible");
      });
    });
  }

  const GameUI = {
    /*
     * Toolbar visibility.
     *
     * This DOES NOT give drawing permission.
     */
    toolbar(data) {
      wrapper.classList.toggle("toolbar-hidden", !data.visible);

      GameUI.rate({
        visible: data.visible,
      });
    },

    /*
     * Drawing permission.
     *
     * Server should send:
     *
     * {
     *   "type": "ui",
     *   "action": "drawing",
     *   "enabled": true
     * }
     *
     * for the drawer.
     *
     * And:
     *
     * {
     *   "type": "ui",
     *   "action": "drawing",
     *   "enabled": false
     * }
     *
     * for everyone else.
     */
    drawing(data) {
      setDrawingEnabled(data.enabled);
    },

    overlay(data) {
      overlay.classList.toggle("show", !!data.show);

      overlayText.classList.remove("show");
      overlayWords.classList.remove("show");
      overlayReveal.classList.remove("show");
      overlayResult.classList.remove("show");
      overlayRoom.classList.remove("show");
      overlayScoreboard.classList.remove("show");

      if (!data.show) {
        return;
      }

      const mode = data.mode || "text";

      if (mode === "text") {
        overlayText.classList.add("show");
        overlayText.textContent = data.text || "";
      } else if (mode === "words") {
        overlayWords.classList.add("show");
        overlayWords.innerHTML = "";

        (data.words || []).forEach((word) => {
          const btn = createEl("div", "word", word);

          btn.addEventListener("click", () => {
            if (socket && socket.readyState === WebSocket.OPEN) {
              socket.send(
                JSON.stringify({
                  type: "word_choice",
                  word: word,
                }),
              );
            }

            setDrawingEnabled(true);

            overlayWords.querySelectorAll(".word").forEach((w) => {
              w.style.pointerEvents = "none";
            });

            GameUI.overlay({
              show: false,
            });
          });

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
      if (data.description != null) {
        wordDescEl.textContent = data.description;
      }

      if (data.word != null) {
        wordEl.textContent = data.word;
      }

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

      /*
       * Automatically determine whether the
       * current player is the drawer.
       *
       * Example:
       *
       * {
       *   name: "Ali",
       *   drawing: true,
       *   me: true
       * }
       *
       * => canDraw = true
       */

      const me = list.find((player) => player.me);

      if (me) {
        setDrawingEnabled(Boolean(me.drawing));
      } else {
        setDrawingEnabled(false);
      }

      list.forEach((player, i) => {
        const el = createEl("div", "player");

        if (i % 2 === 0) {
          el.classList.add("odd");
        }

        if (i === 0) {
          el.classList.add("first");
        }

        if (i === list.length - 1) {
          el.classList.add("last");
        }

        if (player.guessed) {
          el.classList.add("guessed");
        }

        if (player.drawing) {
          el.classList.add("drawing");
        }

        if (player.admin) {
          el.classList.add("admin");
        }

        const bg = createEl("div", "player-background");

        const info = createEl("div", "player-info");

        const name = createEl("div", "player-name", player.name || "Player");

        if (player.me) {
          name.classList.add("me");
        }

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

      if (chatType === "guessed") {
        p.classList.add("guessed");
      }

      p.style.color = CHAT_TYPES[chatType] || CHAT_TYPES.base;

      chatContent.appendChild(p);

      chatContent.scrollTop = chatContent.scrollHeight;

      if (data.bubble !== false) {
        const bubbleHost = $("#game-canvas .bubbles");

        const bubble = p.cloneNode(true);

        bubbleHost.appendChild(bubble);

        setTimeout(() => {
          bubble.remove();
        }, 2500);
      }
    },

    chat_clear() {
      chatContent.innerHTML = "";
    },

    guess_input(data) {
      chatForms.forEach((form) => {
        const input = form.querySelector("input");

        if (data.enabled != null) {
          input.disabled = !data.enabled;
        }

        if (data.placeholder != null) {
          input.placeholder = data.placeholder;
        }

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

    const username = sessionStorage.getItem("username")
    console.log(username)
    socket = new WebSocket(
      `${protocol}//${window.location.host}/ws/board/${roomName}/?username=${encodeURIComponent(username)}`
    );

    socket.onopen = function () {
      console.log("WebSocket connected");
    };

    socket.onmessage = function (e) {
      const data = JSON.parse(e.data);

      if (data.type === "draw") {
        drawLine(data.payload);
        return;
      }
      if (data.type === "clear") {
        clearCanvas();
        return;
      }

      if (data.type === "ui") {
        GameUI.handle(data);
        return;
      }

      if (typeof GameUI[data.type] === "function") {
        GameUI[data.type](data);
      }
    };

    socket.onclose = function (event) {
      console.error("WebSocket closed:", event.code, event.reason);

      setDrawingEnabled(false);
    };

    socket.onerror = function (error) {
      console.error("WebSocket error:", error);

      setDrawingEnabled(false);
    };
  }

  function init() {
    initColors();
    initSizes();
    initTools();

    initCanvas();
    bindDrawing();
    bindChatInput();

    // No resize handler: the bitmap is a fixed 800x600 and CSS scales it,
    // so a resize needs no JS. Re-assigning canvas.width/height here is
    // what used to erase the drawing.

    const roomScript = document.getElementById("room_name");

    if (roomScript) {
      const roomName = JSON.parse(roomScript.textContent);

      connectSocket(roomName);
    }

    /*
     * Initial state:
     *
     * Nobody can draw until the server
     * tells us that this player is the drawer.
     */
    setDrawingEnabled(false);

    GameUI.toolbar({
      visible: false,
    });

    GameUI.rate({
      visible: false,
    });

    GameUI.guess_input({
      enabled: true,
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
