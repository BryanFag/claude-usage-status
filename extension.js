const vscode = require("vscode");
const fs = require("fs");
const os = require("os");
const path = require("path");

const USAGE_URL = "https://api.anthropic.com/api/oauth/usage";
const OAUTH_BETA_HEADER = "oauth-2025-04-20";
const CREDENTIALS_PATH = path.join(os.homedir(), ".claude", ".credentials.json");
const POLL_INTERVAL_MS = 3 * 60 * 1000;
const REQUEST_TIMEOUT_MS = 10 * 1000;
const MINUTE_MS = 60 * 1000;
const HOUR_MS = 60 * MINUTE_MS;
const DAY_MS = 24 * HOUR_MS;
const CLAUDE_ORANGE = "#D97757";
const TRACK_COLOR = "#80808055";
const CLAUDE_MARK = "✻";
const BAR_ICON_PREFIX = "claude-usage-bar-";
const BAR_ICON_STEP = 5;
const WINDOW_SEPARATOR = " ";
const TOOLTIP_SEGMENTS = 24;
const TOOLTIP_BLOCK = "█";
const STATUS_BAR_ITEM_ID = "claudeUsageStatusbar.usage";
const REFRESH_COMMAND = "claudeUsageStatusbar.refresh";
const USAGE_WINDOWS = [
  { key: "five_hour", shortLabel: "5h", label: "Sessão (5 h)" },
  { key: "seven_day", shortLabel: "7d", label: "Semana (7 dias)" },
];

let statusBarItem;
let lastUsage;
let lastUpdatedAt;

function readAccessToken() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, "utf8"));
  const oauth = credentials.claudeAiOauth;
  if (!oauth || !oauth.accessToken) {
    throw new Error("login do Claude não encontrado");
  }
  if (oauth.expiresAt && oauth.expiresAt < Date.now()) {
    throw new Error("login expirado; abra o Claude para renovar");
  }
  return oauth.accessToken;
}

async function fetchUsage() {
  const response = await fetch(USAGE_URL, {
    headers: {
      Authorization: `Bearer ${readAccessToken()}`,
      "anthropic-beta": OAUTH_BETA_HEADER,
      "Content-Type": "application/json",
    },
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function countFilledSegments(window, segments) {
  const utilization = window ? window.utilization : 0;
  return Math.min(segments, Math.max(0, Math.round((utilization / 100) * segments)));
}

function formatPercent(window) {
  return window ? `${Math.round(window.utilization)}%` : "-";
}

function formatBarIcon(window) {
  const utilization = window ? window.utilization : 0;
  const step = Math.min(100, Math.max(0, Math.round(utilization / BAR_ICON_STEP) * BAR_ICON_STEP));
  return `$(${BAR_ICON_PREFIX}${step})`;
}

function formatStatusBarWindow(usageWindow, usage) {
  const window = usage[usageWindow.key];
  return `${usageWindow.shortLabel} ${formatBarIcon(window)} ${formatPercent(window)}`;
}

function formatTooltipBar(window) {
  const filled = countFilledSegments(window, TOOLTIP_SEGMENTS);
  const filledPart = `<span style="color:${CLAUDE_ORANGE};">${TOOLTIP_BLOCK.repeat(filled)}</span>`;
  const emptyPart = `<span style="color:${TRACK_COLOR};">${TOOLTIP_BLOCK.repeat(TOOLTIP_SEGMENTS - filled)}</span>`;
  return filledPart + emptyPart;
}

function formatTimeLeft(resetsAt) {
  const remainingMs = Math.max(0, new Date(resetsAt).getTime() - Date.now());
  const days = Math.floor(remainingMs / DAY_MS);
  const hours = Math.floor((remainingMs % DAY_MS) / HOUR_MS);
  const minutes = Math.floor((remainingMs % HOUR_MS) / MINUTE_MS);
  if (days > 0) {
    return `${days}d ${hours}h`;
  }
  if (hours > 0) {
    return `${hours}h ${minutes}min`;
  }
  return `${minutes}min`;
}

function formatResetClock(resetsAt) {
  return new Date(resetsAt).toLocaleString("pt-BR", {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatReset(window) {
  if (!window || !window.resets_at) {
    return "sem horário de reset";
  }
  return `zera em ${formatTimeLeft(window.resets_at)} · ${formatResetClock(window.resets_at)}`;
}

function formatClock(date) {
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function buildTooltip(usage, staleReason) {
  const tooltip = new vscode.MarkdownString();
  tooltip.supportHtml = true;
  tooltip.supportThemeIcons = true;
  tooltip.appendMarkdown(`<span style="color:${CLAUDE_ORANGE};">**${CLAUDE_MARK} Uso do Claude**</span>\n\n`);
  for (const usageWindow of USAGE_WINDOWS) {
    const window = usage[usageWindow.key];
    tooltip.appendMarkdown(`**${usageWindow.label}** · ${formatPercent(window)}\n\n`);
    tooltip.appendMarkdown(`${formatTooltipBar(window)}\n\n`);
    tooltip.appendMarkdown(`${formatReset(window)}\n\n`);
  }
  tooltip.appendMarkdown(`---\n\n`);
  if (staleReason) {
    tooltip.appendMarkdown(`$(warning) Desatualizado: ${staleReason}\n\n`);
  }
  tooltip.appendMarkdown(`Atualizado às ${formatClock(lastUpdatedAt)} · clique para atualizar`);
  return tooltip;
}

function renderUsage(usage, staleReason) {
  const windows = USAGE_WINDOWS.map((usageWindow) => formatStatusBarWindow(usageWindow, usage)).join(WINDOW_SEPARATOR);
  const staleMark = staleReason ? " $(warning)" : "";
  statusBarItem.text = `${CLAUDE_MARK} ${windows}${staleMark}`;
  statusBarItem.tooltip = buildTooltip(usage, staleReason);
}

function renderError(message) {
  if (lastUsage) {
    renderUsage(lastUsage, message);
    return;
  }
  statusBarItem.text = `${CLAUDE_MARK} Claude $(warning)`;
  statusBarItem.tooltip = `Uso do Claude indisponível: ${message}`;
}

async function refresh() {
  try {
    lastUsage = await fetchUsage();
    lastUpdatedAt = new Date();
    renderUsage(lastUsage);
  } catch (error) {
    renderError(error.message);
  }
}

function activate(context) {
  statusBarItem = vscode.window.createStatusBarItem(STATUS_BAR_ITEM_ID, vscode.StatusBarAlignment.Right, 100);
  statusBarItem.name = "Uso do Claude";
  statusBarItem.command = REFRESH_COMMAND;
  statusBarItem.color = CLAUDE_ORANGE;
  statusBarItem.text = `${CLAUDE_MARK} Claude…`;
  statusBarItem.show();
  const timer = setInterval(refresh, POLL_INTERVAL_MS);
  context.subscriptions.push(
    statusBarItem,
    vscode.commands.registerCommand(REFRESH_COMMAND, refresh),
    { dispose: () => clearInterval(timer) },
  );
  refresh();
}

function deactivate() {}

module.exports = { activate, deactivate };
